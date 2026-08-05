import hashlib

import pytest

from healthcare_pipeline.services.payload_integrity import (
    PayloadIntegrity,
    build_idempotency_key,
    calculate_payload_integrity,
)


def test_calculate_payload_integrity_returns_value_object() -> None:
    payload = b"healthcare-message"

    result = calculate_payload_integrity(payload)

    assert isinstance(result, PayloadIntegrity)


def test_calculate_payload_integrity_returns_sha256_and_size() -> None:
    payload = b"healthcare-message"

    result = calculate_payload_integrity(payload)

    assert result.sha256 == hashlib.sha256(payload).hexdigest()
    assert result.size_bytes == len(payload)


def test_calculate_payload_integrity_is_deterministic() -> None:
    payload = b"same-healthcare-message"

    first_result = calculate_payload_integrity(payload)
    second_result = calculate_payload_integrity(payload)

    assert first_result == second_result


def test_different_payloads_produce_different_hashes() -> None:
    first_result = calculate_payload_integrity(
        b"healthcare-message-one"
    )
    second_result = calculate_payload_integrity(
        b"healthcare-message-two"
    )

    assert first_result.sha256 != second_result.sha256


def test_payload_integrity_value_is_immutable() -> None:
    result = calculate_payload_integrity(
        b"healthcare-message"
    )

    with pytest.raises(AttributeError):
        result.sha256 = "changed"  # type: ignore[misc]


def test_calculate_payload_integrity_rejects_empty_payload() -> None:
    with pytest.raises(
        ValueError,
        match="payload must not be empty",
    ):
        calculate_payload_integrity(b"")


@pytest.mark.parametrize(
    "invalid_payload",
    [
        "not-bytes",
        bytearray(b"mutable-bytes"),
        memoryview(b"memory-view"),
        123,
        None,
    ],
)
def test_calculate_payload_integrity_rejects_non_bytes(
    invalid_payload: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="payload must be provided as bytes",
    ):
        calculate_payload_integrity(  # type: ignore[arg-type]
            invalid_payload
        )


def test_build_idempotency_key_prefers_source_message_id() -> None:
    result = build_idempotency_key(
        source_system_code="EPIC-PROD",
        source_message_id="MSG-1001",
        payload_hash="a" * 64,
    )

    assert result == "epic-prod:message:MSG-1001"


def test_build_idempotency_key_normalizes_source_code() -> None:
    result = build_idempotency_key(
        source_system_code="  EPIC-PROD  ",
        source_message_id="MSG-1001",
        payload_hash="a" * 64,
    )

    assert result == "epic-prod:message:MSG-1001"


def test_build_idempotency_key_trims_message_id() -> None:
    result = build_idempotency_key(
        source_system_code="epic-prod",
        source_message_id="  MSG-1001  ",
        payload_hash="a" * 64,
    )

    assert result == "epic-prod:message:MSG-1001"


def test_build_idempotency_key_preserves_message_id_case() -> None:
    result = build_idempotency_key(
        source_system_code="epic-prod",
        source_message_id="Msg-AbC-1001",
        payload_hash="a" * 64,
    )

    assert result == "epic-prod:message:Msg-AbC-1001"


def test_build_idempotency_key_uses_hash_when_message_id_none() -> None:
    payload_hash = "b" * 64

    result = build_idempotency_key(
        source_system_code="LAB-PROD",
        source_message_id=None,
        payload_hash=payload_hash,
    )

    assert result == f"lab-prod:payload:{payload_hash}"


def test_build_idempotency_key_uses_hash_when_message_id_blank() -> None:
    payload_hash = "c" * 64

    result = build_idempotency_key(
        source_system_code="LAB-PROD",
        source_message_id="   ",
        payload_hash=payload_hash,
    )

    assert result == f"lab-prod:payload:{payload_hash}"


def test_build_idempotency_key_normalizes_uppercase_hash() -> None:
    uppercase_hash = "ABCDEF" * 10 + "ABCD"

    result = build_idempotency_key(
        source_system_code="LAB-PROD",
        source_message_id=None,
        payload_hash=uppercase_hash,
    )

    assert result == (
        "lab-prod:payload:"
        f"{uppercase_hash.lower()}"
    )


def test_build_idempotency_key_rejects_blank_source_code() -> None:
    with pytest.raises(
        ValueError,
        match="source_system_code must not be blank",
    ):
        build_idempotency_key(
            source_system_code=" ",
            source_message_id="MSG-1",
            payload_hash="a" * 64,
        )


@pytest.mark.parametrize(
    "invalid_source_code",
    [
        None,
        123,
        b"epic-prod",
    ],
)
def test_build_idempotency_key_rejects_non_string_source_code(
    invalid_source_code: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="source_system_code must be a string",
    ):
        build_idempotency_key(
            source_system_code=invalid_source_code,  # type: ignore[arg-type]
            source_message_id="MSG-1",
            payload_hash="a" * 64,
        )


@pytest.mark.parametrize(
    "invalid_message_id",
    [
        123,
        b"MSG-1",
        ["MSG-1"],
    ],
)
def test_build_idempotency_key_rejects_non_string_message_id(
    invalid_message_id: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="source_message_id must be a string or None",
    ):
        build_idempotency_key(
            source_system_code="epic-prod",
            source_message_id=invalid_message_id,  # type: ignore[arg-type]
            payload_hash="a" * 64,
        )


@pytest.mark.parametrize(
    "invalid_hash",
    [
        "",
        "invalid",
        "a" * 63,
        "a" * 65,
        "g" * 64,
        "12345",
    ],
)
def test_build_idempotency_key_rejects_invalid_hash_fallback(
    invalid_hash: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="64-character SHA-256 hexadecimal digest",
    ):
        build_idempotency_key(
            source_system_code="epic-prod",
            source_message_id=None,
            payload_hash=invalid_hash,
        )


def test_invalid_hash_does_not_matter_when_message_id_exists() -> None:
    result = build_idempotency_key(
        source_system_code="epic-prod",
        source_message_id="MSG-1001",
        payload_hash="not-needed-for-key",
    )

    assert result == "epic-prod:message:MSG-1001"


def test_build_idempotency_key_rejects_non_string_hash_fallback() -> None:
    with pytest.raises(
        TypeError,
        match="payload_hash must be a string",
    ):
        build_idempotency_key(
            source_system_code="epic-prod",
            source_message_id=None,
            payload_hash=None,  # type: ignore[arg-type]
        )