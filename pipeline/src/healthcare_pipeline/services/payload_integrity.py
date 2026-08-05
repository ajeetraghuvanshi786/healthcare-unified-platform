from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True, slots=True)
class PayloadIntegrity:
    """
    Immutable integrity metadata calculated from an incoming payload.

    Attributes:
        sha256:
            Lowercase hexadecimal SHA-256 digest of the exact payload bytes.

        size_bytes:
            Exact size of the payload in bytes.
    """

    sha256: str
    size_bytes: int


def calculate_payload_integrity(payload: bytes) -> PayloadIntegrity:
    """
    Calculate integrity metadata for an immutable healthcare payload.

    The calculation must be performed against the exact bytes received from
    the external source. The payload must not be decoded, reformatted,
    normalized, or modified before this function is called.

    Args:
        payload:
            Exact payload bytes received from the external source.

    Returns:
        PayloadIntegrity:
            Immutable SHA-256 digest and byte-size metadata.

    Raises:
        TypeError:
            If payload is not provided as bytes.

        ValueError:
            If payload is empty.

    Example:
        >>> payload = b"MSH|^~\\\\&|LAB|HOSPITAL"
        >>> result = calculate_payload_integrity(payload)
        >>> len(result.sha256)
        64
        >>> result.size_bytes
        22
    """

    if not isinstance(payload, bytes):
        raise TypeError("payload must be provided as bytes")

    if not payload:
        raise ValueError("payload must not be empty")

    return PayloadIntegrity(
        sha256=hashlib.sha256(payload).hexdigest(),
        size_bytes=len(payload),
    )


def build_idempotency_key(
    *,
    source_system_code: str,
    source_message_id: str | None,
    payload_hash: str,
) -> str:
    """
    Build a deterministic idempotency key for an ingestion record.

    The source message identifier is preferred because it normally represents
    the logical identity assigned by the sending system.

    If no usable source message identifier exists, the payload's SHA-256
    digest is used as the fallback identity.

    The resulting key is scoped again by tenant and source-system identifiers
    through the database unique constraint:

        tenant_id + source_system_id + idempotency_key

    Args:
        source_system_code:
            Stable internal code representing the sending source system.

            Examples:
                epic-prod
                northstar-lis-prod
                pharmacy-sftp
                payer-x12-gateway

        source_message_id:
            Message identifier assigned by the source system.

            Examples:
                HL7 MSH-10 message control ID
                FHIR Bundle.identifier value
                X12 interchange or transaction identifier
                File-import record identifier

        payload_hash:
            Sixty-four-character hexadecimal SHA-256 digest calculated from
            the exact payload bytes.

    Returns:
        str:
            Deterministic normalized idempotency key.

    Raises:
        TypeError:
            If source_system_code is not a string.
            If source_message_id is provided but is not a string.
            If payload_hash is not a string.

        ValueError:
            If source_system_code is blank.
            If no usable source message ID exists and payload_hash is not a
            valid SHA-256 hexadecimal digest.

    Examples:
        Source message ID available:

        >>> build_idempotency_key(
        ...     source_system_code="EPIC-PROD",
        ...     source_message_id="MSG-1001",
        ...     payload_hash="a" * 64,
        ... )
        'epic-prod:message:MSG-1001'

        Source message ID unavailable:

        >>> build_idempotency_key(
        ...     source_system_code="LAB-PROD",
        ...     source_message_id=None,
        ...     payload_hash="b" * 64,
        ... )
        'lab-prod:payload:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
    """

    normalized_source_code = _normalize_source_system_code(
        source_system_code
    )

    normalized_message_id = _normalize_optional_message_id(
        source_message_id
    )

    if normalized_message_id is not None:
        return (
            f"{normalized_source_code}:"
            f"message:{normalized_message_id}"
        )

    normalized_payload_hash = _normalize_sha256(payload_hash)

    return (
        f"{normalized_source_code}:"
        f"payload:{normalized_payload_hash}"
    )


def _normalize_source_system_code(source_system_code: str) -> str:
    """
    Normalize a source-system code for deterministic key generation.

    Source-system codes are converted to lowercase because internal technical
    codes should be case-insensitive.

    Leading and trailing whitespace is removed.

    Internal whitespace is not silently removed because that may hide invalid
    source-system configuration.
    """

    if not isinstance(source_system_code, str):
        raise TypeError("source_system_code must be a string")

    normalized_source_code = source_system_code.strip().lower()

    if not normalized_source_code:
        raise ValueError("source_system_code must not be blank")

    return normalized_source_code


def _normalize_optional_message_id(
    source_message_id: str | None,
) -> str | None:
    """
    Normalize an optional source-assigned message identifier.

    Message identifier case is preserved because some source systems treat
    identifiers as case-sensitive.
    """

    if source_message_id is None:
        return None

    if not isinstance(source_message_id, str):
        raise TypeError(
            "source_message_id must be a string or None"
        )

    normalized_message_id = source_message_id.strip()

    if not normalized_message_id:
        return None

    return normalized_message_id


def _normalize_sha256(payload_hash: str) -> str:
    """
    Validate and normalize a SHA-256 hexadecimal digest.

    A valid SHA-256 digest contains exactly 64 hexadecimal characters.
    The returned value is always lowercase.
    """

    if not isinstance(payload_hash, str):
        raise TypeError("payload_hash must be a string")

    normalized_payload_hash = payload_hash.strip().lower()

    if not _SHA256_PATTERN.fullmatch(normalized_payload_hash):
        raise ValueError(
            "payload_hash must be a 64-character SHA-256 "
            "hexadecimal digest"
        )

    return normalized_payload_hash