import os

from .config import STATE_HOME, state_file
from .system import pkill, symlink, unlink

__all__ = [
    "pkill",
    "symlink",
    "system_state_file",
    "topic_state_file",
    "unlink",
]


def system_state_file(*parts: str) -> str:
    return os.path.join(STATE_HOME, *parts)


def topic_state_file(topic: str, *parts: str) -> str:
    return state_file(topic, *parts)
