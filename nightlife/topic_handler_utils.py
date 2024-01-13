import os

import psutil

from .config import STATE_HOME, state_file

__all__ = ["STATE_HOME", "topic_state_file", "pkill"]


def topic_state_file(topic: str, *parts: str) -> str:
    return state_file(topic, *parts)


def pkill(name: str, signum: int) -> None:
    for p in psutil.process_iter(["name", "exe", "cmdline"]):
        if (
            p.info["name"] == name or
            (p.info["exe"] and os.path.basename(p.info["exe"]) == name) or
            (p.info["cmdline"] and os.path.basename(p.info["cmdline"][0]) == name)
        ):
            p.send_signal(signum)
