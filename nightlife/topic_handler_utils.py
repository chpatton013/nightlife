import os

import psutil

from .state import STATE_DIR, STATE_HOME

__all__ = ["STATE_HOME", "topic_state_file", "pkill"]


def topic_state_file(topic: str, *parts: str) -> str:
    return os.path.join(STATE_DIR, topic, *parts)


def pkill(name: str, signum: int) -> None:
    for p in psutil.process_iter(["name", "exe", "cmdline"]):
        if (
            p.info["name"] == name or
            (p.info["exe"] and os.path.basename(p.info["exe"]) == name) or
            (p.info["cmdline"] and os.path.basename(p.info["cmdline"][0]) == name)
        ):
            p.send_signal(signum)
