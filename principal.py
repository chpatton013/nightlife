"""
Usage:

     export NIGHTLIFE_PRINCIPAL_AGENT_HOST=http://localhost:8000
     export NIGHTLIFE_PRINCIPAL_PRIVATE_KEY_FILE=./keys/priv
     NIGHTLIFE_PRINCIPAL_EVENT=event python3 principal.py 0<&-
"""

import argparse
import datetime
import logging
import os
import subprocess
import sys
import urllib.request
import uuid

import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


logging.basicConfig(
    level=(logging.DEBUG if os.getenv("NIGHTLIFE_PRINCIPAL_DEBUG") else logging.INFO),
    format="%(asctime)s|%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class PrincipalSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NIGHTLIFE_PRINCIPAL_",
        env_file=os.getenv("NIGHTLIFE_PRINCIPAL_ENV_FILE", ".env"),
    )

    agent_host: str
    event: str
    events_dir: str = "events"
    event_timeout: int = 30
    timesync_tolerance: int = 30
    private_key_file: str = "privkey"
    jwt_issuer: str = "urn:nightlife:principal"
    jwt_audience: str = "urn:nightlife:agent"


settings = PrincipalSettings()


def read_private_key(password: bytes | None) -> Ed25519PrivateKey:
    with open(settings.private_key_file, "rb") as f:
        privkey_bytes = f.read()
    privkey = load_pem_private_key(privkey_bytes, password or None)
    assert isinstance(privkey, Ed25519PrivateKey)
    return privkey


def encode_jwt(privkey: Ed25519PrivateKey) -> str:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    tolerance = datetime.timedelta(seconds=settings.timesync_tolerance)
    payload = {
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "jti": uuid.uuid4().urn,
        "iat": now,
        "nbf": now - tolerance,
        "exp": now + tolerance,
    }
    return jwt.encode(payload, privkey, algorithm="EdDSA")


def trigger_event() -> bytes:
    event_path = os.path.join(settings.events_dir, settings.event)
    p = subprocess.run(
        [event_path],
        check=True,
        timeout=settings.event_timeout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return p.stdout


def post_topic(token: str, body: bytes) -> bytes:
    request = urllib.request.Request(
        f"{settings.agent_host}/topic/{settings.event}",
        method="POST",
        data=body,
    )
    request.add_header("Authorization", "bearer " + token)
    with urllib.request.urlopen(request) as f:
        return f.read()


if __name__ == "__main__":
    password = sys.stdin.buffer.read() if sys.stdin else None
    privkey = read_private_key(password)
    token = encode_jwt(privkey)
    body = trigger_event()
    response = post_topic(token, body)
    sys.stdout.buffer.write(response)
