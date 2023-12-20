"""
Usage:

    # no permissions for group/other
    umask 077

    # pubkey path as input arg
    # privkey data on stdout
    # skip privkey encryption password prompt with 0<&-
    python3 auth.py keys/pub >keys/priv 0<&-
"""

import argparse
import sys

from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


def generate_keys(password: bytes | None) -> (bytes, bytes):
    privkey = Ed25519PrivateKey.generate()
    privkey_bytes = privkey.private_bytes(
        Encoding.PEM,
        PrivateFormat.PKCS8,
        BestAvailableEncryption(password) if password else NoEncryption(),
    )

    pubkey = privkey.public_key()
    pubkey_bytes = pubkey.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

    return privkey_bytes, pubkey_bytes


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pub_file")
    args = parser.parse_args()

    password = sys.stdin.buffer.read() if sys.stdin else None
    privkey_bytes, pubkey_bytes = generate_keys(password)

    with open(args.pub_file, "wb") as f:
        f.write(pubkey_bytes)

    sys.stdout.buffer.write(privkey_bytes)
