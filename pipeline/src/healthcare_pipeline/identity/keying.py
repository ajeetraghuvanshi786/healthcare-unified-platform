from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Protocol


class IdentityKeyEncoder(Protocol):
    def encode(self, namespace: str, value: str) -> str: ...


@dataclass(frozen=True, slots=True)
class HmacIdentityKeyEncoder:
    """Produces non-reversible deterministic index keys for PHI-derived candidate features."""

    secret_key: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.secret_key, bytes):
            raise TypeError("secret_key must be bytes")
        if len(self.secret_key) < 32:
            raise ValueError("secret_key must contain at least 32 bytes")

    def encode(self, namespace: str, value: str) -> str:
        if not isinstance(namespace, str) or not namespace.strip():
            raise ValueError("namespace must be a non-blank string")
        if not isinstance(value, str) or not value:
            raise ValueError("value must be a non-blank string")
        payload = f"{namespace.strip()}\x1e{value}".encode()
        return hmac.new(self.secret_key, payload, hashlib.sha256).hexdigest()
