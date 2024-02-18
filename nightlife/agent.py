import logging
import os
import threading
from contextlib import asynccontextmanager

import jwt
from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.security import HTTPBearer
from fastapi.responses import PlainTextResponse
from pydantic_settings import BaseSettings, SettingsConfigDict
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEvent,
    FileSystemMovedEvent,
    FileSystemEventHandler,
)

from .respond import (
    RespondTool,
    TopicHandlerResults,
    TopicHandlers,
    TopicRegistry,
)


logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG") else logging.INFO,
    format="%(asctime)s|%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NIGHTLIFE_AGENT_")

    app_name: str = "Nightlife Agent"
    public_key_file: str = "config/auth/keys/pub"
    jwt_issuer: str = "urn:nightlife:principal"
    jwt_audience: str = "urn:nightlife:agent"


SETTINGS = AgentSettings()
PUBLIC_KEY = b""


def _read_public_key(public_key_file: str) -> None:
    global PUBLIC_KEY
    try:
        logging.info("Reading public key file '%s'", public_key_file)
        with open(public_key_file, "rb") as f:
            PUBLIC_KEY = f.read()
    except Exception as e:
        logging.error("Failed to read public key file '%s': %s", public_key_file, str(e))
        PUBLIC_KEY = b""


class PublicKeyFileEventHandler(FileSystemEventHandler):
    def __init__(self, public_key_file: str):
        self.public_key_file = public_key_file
        self._thread_active = False
        self._cv = threading.Condition()
        self._thread = threading.Thread(target=lambda: self._thread_target())

    def _thread_target(self) -> None:
        while self._thread_active:
            _read_public_key(self.public_key_file)
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

    def _on_src_path_event(self, event: FileSystemEvent) -> None:
        path = os.path.abspath(self.public_key_file)
        if event.src_path == path:
            with self._cv:
                self._cv.notify()

    def _on_dest_path_event(self, event: FileSystemMovedEvent) -> None:
        path = os.path.abspath(self.public_key_file)
        if event.dest_path == path:
            with self._cv:
                self._cv.notify()

    def on_created(self, event: FileSystemEvent) -> None:
        self._on_src_path_event(event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._on_src_path_event(event)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._on_src_path_event(event)

    def on_moved(self, event: FileSystemMovedEvent) -> None:
        self._on_dest_path_event(event)


@asynccontextmanager
async def lifespan(_: FastAPI):
    event_handler = PublicKeyFileEventHandler(SETTINGS.public_key_file)

    observer = Observer()
    observer.schedule(event_handler, os.path.dirname(SETTINGS.public_key_file), recursive=True)

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
            raise HTTPException(401, "Unauthorized: missing bearer token")
        token = authorization.credentials
        payload = jwt.decode(token, PUBLIC_KEY, audience=SETTINGS.jwt_audience, algorithms=["EdDSA"])

        if payload.get("iss") != SETTINGS.jwt_issuer:
            raise HTTPException(401, "Unauthorized: invalid iss")

        if not payload.get("jti"):
            raise HTTPException(401, "Unauthorized: missing jti")
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


async def _await_body(request: Request) -> bytes:
    return await request.body()


@app.get("/topics")
async def get_topics() -> TopicRegistry:
    try:
        return RespondTool().topic_registry()
    except FileNotFoundError:
        raise HTTPException(500, "server misconfiguration")


@app.get("/topic/{topic_name}")
async def get_topic(topic_name: str) -> TopicHandlers:
    try:
        return RespondTool().topic_handlers(topic_name)
    except FileNotFoundError:
        raise HTTPException(404)


@app.post("/topic/{topic_name}")
async def post_topic(topic_name: str, body: bytes = Depends(_await_body)) -> TopicHandlerResults:
    try:
        return RespondTool().handle_topic(topic_name, body)
    except FileNotFoundError:
        raise HTTPException(404)
