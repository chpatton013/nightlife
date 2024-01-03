import os


STATE_DIR = os.path.join(
    os.getenv(
        "XDG_STATE_HOME",
        os.path.join(os.path.expanduser("~"), ".local/state")
    ),
    "nightlife"
)

PRINCIPAL_LOCKFILE = os.path.join(STATE_DIR, "principal.lock")

AGENT_LOCKFILE = os.path.join(STATE_DIR, "agent.lock")
