"""Encrypted-at-rest storage for Kaka.ai.

Data is sealed with Fernet (AES-128-CBC + HMAC-SHA256, authenticated) using a
key derived from a user passphrase via PBKDF2-HMAC-SHA256 (600k iterations).
No passphrase or key material is ever written to disk.
"""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path

_FERNET_PREFIX = b"gAAAA"  # all Fernet tokens start with this


def is_encrypted(raw: bytes | str) -> bool:
    """Detect whether a blob/file content is already Fernet-sealed."""
    if isinstance(raw, str):
        raw = raw.lstrip().encode(errors="ignore")[:16]
    return bytes(raw[:16]).lstrip().startswith(_FERNET_PREFIX)


def derive_key(passphrase: str) -> bytes:
    """Derive a Fernet key from a passphrase (PBKDF2-HMAC-SHA256, 600k iters)."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"kaka.ai/v1/at-rest",  # fixed app salt; secrecy comes from the passphrase
        iterations=600_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def seal(text: str, passphrase: str) -> str:
    """Encrypt UTF-8 text into a Fernet token string."""
    from cryptography.fernet import Fernet

    if not passphrase or len(passphrase) < 6:
        raise ValueError("Passphrase too short (minimum 6 characters) for at-rest encryption.")
    return Fernet(derive_key(passphrase)).encrypt(text.encode()).decode()


def unseal(token: str, passphrase: str) -> str:
    """Decrypt a Fernet token back to text. Raises ValueError on bad passphrase."""
    import binascii

    from cryptography.fernet import Fernet, InvalidToken

    try:
        return Fernet(derive_key(passphrase)).decrypt(token.encode()).decode()
    except (InvalidToken, binascii.Error, ValueError) as e:
        raise ValueError(
            "Decryption failed: wrong DATA_PASSPHRASE (or corrupted data). "
            "Fail-closed: refusing to load encrypted agent data."
        ) from e


def read_maybe_encrypted(path: Path, passphrase: str | None) -> str:
    """Read a file that may be plaintext (legacy) or sealed; returns plain text."""
    raw = path.read_text(encoding="utf-8")
    if is_encrypted(raw):
        if not passphrase:
            raise ValueError(
                f"{path.name} is encrypted — set DATA_PASSPHRASE to unlock it."
            )
        return unseal(raw, passphrase)
    return raw


def write_sealed(path: Path, text: str, passphrase: str | None) -> None:
    """Write text to file (atomically), sealing it first when a passphrase is configured."""
    if passphrase:
        payload = seal(text, passphrase)
    else:
        payload = text
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(path)
