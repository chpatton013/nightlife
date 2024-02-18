import logging
import os
import shutil
import subprocess

import psutil


def pkill(name: str, signum: int) -> None:
    for p in psutil.process_iter(attrs=["name", "exe", "cmdline"]):
        # Process.info property is conditionally set based on attrs argument to
        # psutil.process_iter. Since this property normally doesn't exist, we
        # need to assert its presence to satisfy mypy that it actually does.
        assert hasattr(p, "info")
        if (
            p.info["name"] == name
            or (p.info["exe"] and os.path.basename(p.info["exe"]) == name)
            or (p.info["cmdline"] and os.path.basename(p.info["cmdline"][0]) == name)
        ):
            logging.debug("Sending signal %d to %s process %d", signum, p.name(), p.pid)
            p.send_signal(signum)


def unlink(path: str) -> None:
    try:
        os.unlink(path)
    except IsADirectoryError:
        try:
            os.rmdir(path)
        except OSError:
            logging.error(
                "Refusing to delete %s because it is a non-empty directory", path
            )
            raise
    except FileNotFoundError:
        pass


def symlink(src: str, dst: str) -> None:
    try:
        if os.path.abspath(os.readlink(dst)) == os.path.abspath(src):
            # dst is already pointing to src; short-circuit
            return
    except FileNotFoundError:
        # dst does not exist; the parent directory may also be missing
        os.makedirs(os.path.dirname(dst), exist_ok=True)
    else:
        # Remove dst before replacing it with a symlink to src
        unlink(dst)

    os.symlink(src, dst)


def copy(src: str, dst: str) -> None:
    if os.path.abspath(src) == os.path.abspath(dst):
        return
    unlink(dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy(src, dst)


def which(executable: str) -> str | None:
    try:
        p = subprocess.run(
            ["which", executable],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        return p.stdout.decode()
    except subprocess.CalledProcessError:
        return None
