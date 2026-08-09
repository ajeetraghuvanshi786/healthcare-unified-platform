from __future__ import annotations

from datetime import datetime
from decimal import Decimal


def normalize_required(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    if any(ord(character) < 32 for character in normalized):
        raise ValueError(f"{field_name} must not contain control characters")
    return normalized


def normalize_optional(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")
    normalized = value.strip()
    if not normalized:
        return None
    if any(ord(character) < 32 for character in normalized):
        raise ValueError(f"{field_name} must not contain control characters")
    return normalized


def ensure_aware(value: datetime | None, field_name: str) -> None:
    if value is not None and value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def ensure_non_negative(value: Decimal | None, field_name: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must not be negative")
