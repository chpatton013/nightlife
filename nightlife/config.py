import os
import urllib.parse


BIN_HOME = os.getenv(
    "XDG_BIN_HOME",
    os.path.join(os.path.expanduser("~"), ".local/bin")
)

CONFIG_HOME = os.getenv(
    "XDG_CONFIG_HOME",
    os.path.join(os.path.expanduser("~"), ".config")
)
CONFIG_DIR = os.path.join(CONFIG_HOME, "nightlife")

STATE_HOME = os.getenv(
    "XDG_STATE_HOME",
    os.path.join(os.path.expanduser("~"), ".local/state")
)
STATE_DIR = os.path.join(STATE_HOME, "nightlife")


def app_file(*parts: str) -> str:
    """
    TODO: replace this with something portable post-installation
    """
    import nightlife
    module = os.path.dirname(nightlife.__file__)
    app = os.path.dirname(module)
    return os.path.join(app, *parts)


def config_file(*parts: str) -> str:
    return os.path.join(CONFIG_DIR, *parts)


def state_file(*parts: str) -> str:
    return os.path.join(STATE_DIR, *parts)


PRINCIPAL_LOCKFILE = state_file("principal.lock")
AGENT_LOCKFILE = state_file("agent.lock")


def write_lockfile(lockfile: str, host: str, port: int) -> None:
    url = f"{host}:{port}"
    if not urllib.parse.urlparse(url).scheme:
        url = f"http://{url}"

    os.makedirs(os.path.dirname(lockfile), exist_ok=True)
    with open(lockfile, "w") as f:
        f.write(url)
