"""
Usage:

    python3 run_server.py /path/to/principal.lock principal:app --host=0.0.0.0 --port=8000
    python3 run_server.py /path/to/agent.lock agent:app --port=8001
"""

import argparse
import os
import urllib.parse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("lockfile")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args, unknown_args = parser.parse_known_args()

    url = f"{args.host}:{args.port}"
    if not urllib.parse.urlparse(url):
        url = f"http://{url}"

    os.makedirs(os.path.dirname(args.lockfile), exist_ok=True)
    with open(args.lockfile, "w") as f:
        f.write(url)

    cmd = ["uvicorn", "--host", args.host, "--port", args.port] + unknown_args
    os.execvp(cmd[0], cmd)
