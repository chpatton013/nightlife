import datetime
import logging
import os
import subprocess
import threading
import time
from contextlib import asynccontextmanager

import jwt
from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.security import HTTPBearer
from fastapi.responses import PlainTextResponse
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler


logging.basicConfig(
    level=(logging.DEBUG if os.getenv("NIGHTLIFE_AGENT_DEBUG") else logging.INFO),
    format="%(asctime)s|%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NIGHTLIFE_AGENT_",
        env_file=os.getenv("NIGHTLIFE_AGENT_ENV_FILE", ".env"),
    )

    app_name: str = "Nightlife Agent"
    topics_dir: str = "topics"
    topic_handler_timeout: int = 15
    topic_handler_output_limit: int = 1024
    request_age_limit: int = 30
    public_key_file: str = "pubkey"
    jwt_issuer: str = "urn:nightlife:principal"
    jwt_audience: str = "urn:nightlife:agent"


settings = AgentSettings()


PUBLIC_KEY = b""


def _read_public_key() -> None:
    global PUBLIC_KEY
    try:
        logging.info("Reading public key file '%s'", settings.public_key_file)
        with open(settings.public_key_file, "rb") as f:
            PUBLIC_KEY = f.read()
    except Exception as e:
        logging.error("Failed to read public key file '%s': %s", settings.public_key_file, str(e))
        PUBLIC_KEY = b""


class PublicKeyFileEventHandler(FileSystemEventHandler):
    def __init__(self):
        self._thread_active = False
        self._cv = threading.Condition()
        self._thread = threading.Thread(target=lambda: self._thread_target())

    def _thread_target(self) -> None:
        while self._thread_active:
            _read_public_key()
            with self._cv:
                self._cv.wait()

    def start(self) -> None:
        self._thread_active = True
        self._thread.start()

    def stop(self) -> None:
        self._thread_active = False
        with self._cv:
            self._cv.notify_all()

    def join(self) -> None:
        self._thread.join()

    def on_any_event(self, event: FileSystemEvent) -> None:
        path = os.path.abspath(settings.public_key_file)
        src_event_type = (event.event_type in ("created", "deleted", "modified"))
        dest_event_type = (event.event_type == "moved")
        if (
            (src_event_type and event.src_path == path) or
            (dest_event_type and event.dest_path == path)
        ):
            with self._cv:
                self._cv.notify()


@asynccontextmanager
async def lifespan(app: FastAPI):
    event_handler = PublicKeyFileEventHandler()

    observer = Observer()
    observer.schedule(event_handler, os.path.dirname(settings.public_key_file), recursive=True)

    event_handler.start()
    observer.start()

    yield

    observer.stop()
    event_handler.stop()

    observer.join()
    event_handler.join()


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def authenticate(request: Request, call_next):
    try:
        authorization = await HTTPBearer(auto_error=False)(request)
        if authorization is None or authorization.scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Unauthorized: missing bearer token")
        token = authorization.credentials
        payload = jwt.decode(token, PUBLIC_KEY, audience=settings.jwt_audience, algorithms=["EdDSA"])

        if payload.get("iss") != settings.jwt_issuer:
            raise HTTPException(status_code=401, detail="Unauthorized: invalid iss")

        if not payload.get("jti"):
            raise HTTPException(status_code=401, detail="Unauthorized: missing jti")
    except HTTPException as e:
        return PlainTextResponse(e.detail, status_code=e.status_code, headers=e.headers)

    logging.info("Authenticated JTI %s", payload["jti"])
    return await call_next(request)


@app.middleware("http")
async def log_request(request: Request, call_next):
    logging.info(
        "client=%s:%d method=%s path=%s query=%s",
        request.client.host if request.client else "<unknown>",
        request.client.port if request.client else 0,
        request.method,
        request.url.path,
        str(request.query_params),
    )
    return await call_next(request)


# Gzip payloads that would span across 4 TCP packets.
# 1 MTU == 1500 bytes, so a little less than 4x that value.
app.add_middleware(GZipMiddleware, minimum_size=5500)


class GetTopic(BaseModel):
    name: str
    handlers: list[str] = []


class GetTopics(BaseModel):
    topics: list[GetTopic]


class TopicHandlerResult(BaseModel):
    success: bool
    timed_out: bool
    exit_status: int
    runtime_ms: int


class TopicHandlerOutput(BaseModel):
    truncated: bool
    length: int
    output: bytes


class TopicHandler(BaseModel):
    name: str
    result: TopicHandlerResult
    stdout: TopicHandlerOutput
    stderr: TopicHandlerOutput


class PostTopicResponse(BaseModel):
    name: str
    handlers: list[TopicHandler] = []


def _make_topic_handler_result(exit_status: int, runtime: float, timed_out: bool) -> TopicHandlerResult:
    return TopicHandlerResult(
        success=(exit_status==0),
        timed_out=timed_out,
        exit_status=exit_status,
        runtime_ms=int(runtime * 1000),
    )


def _make_topic_handler_output(output: bytes, max_len: int) -> TopicHandlerOutput:
    return TopicHandlerOutput(
        truncated=len(output) > max_len,
        length=len(output),
        output=output[:max_len],
    )


def _handle_topic(topic_dir: str, handler: str, body: bytes) -> TopicHandler:
    handler_path = os.path.join(topic_dir, handler)
    try:
        start_time = time.time()
        p = subprocess.run(
            [handler_path],
            timeout=settings.topic_handler_timeout,
            input=body,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        duration = time.time() - start_time
        result = _make_topic_handler_result(p.returncode, duration, False)
    except subprocess.TimeoutExpired:
        result = _make_topic_handler_result(p.returncode, duration, True)
    return TopicHandler(
        name=handler,
        result=result,
        stdout=_make_topic_handler_output(p.stdout, settings.topic_handler_output_limit),
        stderr=_make_topic_handler_output(p.stderr, settings.topic_handler_output_limit),
    )


async def _await_body(request: Request) -> bytes:
    return await request.body()


def listfiles(directory: str) -> list[str]:
    return [
        f for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f))
    ]


def _get_topic(topic_name: str) -> (str, GetTopic):
    topic_dir = os.path.join(settings.topics_dir, topic_name)
    try:
        handlers = sorted(listfiles(topic_dir))
    except FileNotFoundError:
        raise HTTPException(status_code=404)
    return topic_dir, GetTopic(name=topic_name, handlers=handlers)


@app.get("/topics")
async def get_topics() -> GetTopics:
    try:
        topic_names = sorted(listfiles(settings.topics_dir))
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="server misconfiguration")

    try:
        topics = [_get_topic(topic_name)[1] for topic_name in topic_names]
    except HTTPException:
        raise HTTPException(status_code=500, detail="server race condition")

    return GetTopics(topics=topics)


@app.get("/topic/{topic_name}")
async def get_topic(topic_name: str) -> GetTopic:
    return _get_topic(topic_name)[1]


@app.post("/topic/{topic_name}")
async def post_topic(topic_name: str, body: bytes = Depends(_await_body)):
    response = PostTopicResponse(name=topic_name)
    topic_dir, topic = _get_topic(topic_name)
    for handler in topic.handlers:
        response.handlers.append(_handle_topic(topic_dir, handler, body))
    return response
