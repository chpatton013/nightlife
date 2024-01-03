import os
import urllib.parse


STATE_HOME = os.getenv(
    "XDG_STATE_HOME",
    os.path.join(os.path.expanduser("~"), ".local/state")
)
STATE_DIR = os.path.join(STATE_HOME, "nightlife")
PRINCIPAL_LOCKFILE = os.path.join(STATE_DIR, "principal.lock")
AGENT_LOCKFILE = os.path.join(STATE_DIR, "agent.lock")


def write_lockfile(lockfile: str, host: str, port: int) -> None:
    url = f"{host}:{port}"
    if not urllib.parse.urlparse(url).scheme:
        url = f"http://{url}"

    os.makedirs(os.path.dirname(lockfile), exist_ok=True)
    with open(lockfile, "w") as f:
        f.write(url)
