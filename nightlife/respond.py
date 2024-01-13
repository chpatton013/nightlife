import logging
import os
import subprocess
import time
from dataclasses import dataclass, field

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from .config import config_file


class RespondSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NIGHTLIFE_RESPOND_")

    topics_dir: str = config_file("handlers")
    handler_timeout: int = 15
    handler_output_limit: int = 1024


class TopicHandlers(BaseModel):
    name: str
    handlers: list[str] = []


class TopicRegistry(BaseModel):
    topics: list[TopicHandlers] = []


class TopicHandlerStatus(BaseModel):
    success: bool
    timed_out: bool
    exit_status: int | None
    runtime_ms: int


class TopicHandlerOutput(BaseModel):
    truncated: bool
    length: int
    output: bytes


class TopicHandlerResult(BaseModel):
    name: str
    status: TopicHandlerStatus
    stdout: TopicHandlerOutput
    stderr: TopicHandlerOutput


class TopicHandlerResults(BaseModel):
    name: str
    handlers: list[TopicHandlerResult] = []


def _make_topic_handler_status(exit_status: int | None, runtime: float) -> TopicHandlerStatus:
    return TopicHandlerStatus(
        success=(exit_status == 0),
        timed_out=(exit_status is None),
        exit_status=exit_status,
        runtime_ms=int(runtime * 1000),
    )

def _make_topic_handler_output(output: bytes, max_len: int) -> TopicHandlerOutput:
    return TopicHandlerOutput(
        truncated=len(output) > max_len,
        length=len(output),
        output=output[:max_len],
    )


@dataclass
class RespondTool:
    settings: RespondSettings = field(default_factory=RespondSettings)

    def topic_handlers(self, name: str) -> TopicHandlers:
        return TopicHandlers(name=name, handlers=self._list_handlers(name))

    def topic_registry(self) -> TopicRegistry:
        return TopicRegistry(
            topics=[self.topic_handlers(name) for name in self._list_topics()]
        )

    def handle_topic(self, topic_name: str, input: bytes | None) -> TopicHandlerResults:
        logging.info("Invoking handlers for topic %s", topic_name)
        results = TopicHandlerResults(
            name=topic_name,
            handlers=[
                self._invoke_topic_handler(topic_name, handler, input)
                for handler in self._list_handlers(topic_name)
            ],
        )
        return results

    def _list_handlers(self, topic_name: str) -> list[str]:
        topic_dir = os.path.join(self.settings.topics_dir, topic_name)
        logging.info("Scanning for topic handlers in %s", topic_dir)
        return sorted(
            f for f in os.listdir(topic_dir)
            if os.path.isfile(os.path.join(topic_dir, f))
        )

    def _list_topics(self) -> list[str]:
        logging.info("Scanning for topics in %s", self.settings.topics_dir)
        return sorted(
            f for f in os.listdir(self.settings.topics_dir)
            if os.path.isdir(os.path.join(self.settings.topics_dir, f))
        )

    def _invoke_topic_handler(self, topic_name: str, handler: str, input: bytes | None) -> TopicHandlerResult:
        topic_dir = os.path.join(self.settings.topics_dir, topic_name)
        handler_path = os.path.join(topic_dir, handler)
        start_time = time.time()
        try:
            logging.info("Invoking topic handler %s/%s", topic_name, handler)
            p = subprocess.run(
                [handler_path],
                timeout=self.settings.handler_timeout,
                input=input,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            duration = time.time() - start_time
            status = _make_topic_handler_status(p.returncode, duration)
            stdout = p.stdout
            stderr = p.stderr
        except subprocess.TimeoutExpired as e:
            status = _make_topic_handler_status(None, self.settings.handler_timeout)
            stdout = e.stdout or b""
            stderr = e.stderr or b""
        return TopicHandlerResult(
            name=handler,
            status=status,
            stdout=_make_topic_handler_output(stdout, self.settings.handler_output_limit),
            stderr=_make_topic_handler_output(stderr, self.settings.handler_output_limit),
        )
