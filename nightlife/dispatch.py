import datetime
import logging
import os
import subprocess
import urllib.request
import uuid
from dataclasses import dataclass, field

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
)
import jwt
from pydantic_settings import BaseSettings, SettingsConfigDict


class DispatchSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NIGHTLIFE_DISPATCH_")

    events_dir: str = "config/events"
    event_timeout: int = 30
    timesync_tolerance: int = 30
    jwt_issuer: str = "urn:nightlife:principal"
    jwt_audience: str = "urn:nightlife:agent"


@dataclass
class TriggerTool:
    settings: DispatchSettings = field(default_factory=DispatchSettings)

    def trigger(self, event: str) -> bytes:
        logging.info("Triggering event %s", event)
        event_path = os.path.join(self.settings.events_dir, event)
        p = subprocess.run(
            [event_path],
            check=True,
            timeout=self.settings.event_timeout,
            stdout=subprocess.PIPE,
        )
        return p.stdout


@dataclass
class BroadcastTool:
    agent_host: str
    private_key_file: str
    private_key_password: bytes | None
    settings: DispatchSettings = field(default_factory=DispatchSettings)

    def broadcast(self, event: str, body: bytes) -> bytes:
        privkey = self._read_private_key()
        token = self._encode_jwt(privkey)
        return self._post_topic(event, token, body)

    def _read_private_key(self) -> Ed25519PrivateKey:
        logging.info("Reading private key file")
        with open(self.private_key_file, "rb") as f:
            privkey_bytes = f.read()
        privkey = load_pem_private_key(privkey_bytes, self.private_key_password or None)
        assert isinstance(privkey, Ed25519PrivateKey)
        return privkey

    def _encode_jwt(self, privkey: Ed25519PrivateKey) -> str:
        logging.info("Encoding JWT")
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        tolerance = datetime.timedelta(seconds=self.settings.timesync_tolerance)
        payload = {
            "iss": self.settings.jwt_issuer,
            "aud": self.settings.jwt_audience,
            "jti": uuid.uuid4().urn,
            "iat": now,
            "nbf": now - tolerance,
            "exp": now + tolerance,
        }
        return jwt.encode(payload, privkey, algorithm="EdDSA")

    def _post_topic(self, event: str, token: str, body: bytes) -> bytes:
        logging.info("Posting topic %s", event)
        request = urllib.request.Request(
            f"{self.agent_host}/topic/{event}",
            method="POST",
            data=body,
        )
        request.add_header("Authorization", "bearer " + token)
        with urllib.request.urlopen(request) as f:
            return f.read()


class DispatchTool:
    def __init__(self, settings: DispatchSettings | None = None, **kwargs):
        settings = settings or DispatchSettings()
        self.trigger = TriggerTool(settings)
        self.broadcast = BroadcastTool(settings=settings, **kwargs)

    def dispatch(self, event: str) -> bytes:
        body = self.trigger.trigger(event)
        return self.broadcast.broadcast(event, body)
