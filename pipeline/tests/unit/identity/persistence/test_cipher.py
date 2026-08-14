from datetime import date

import pytest
from cryptography.exceptions import InvalidTag

from healthcare_pipeline.canonical import HumanName, Identifier, Patient
from healthcare_pipeline.identity import IdentityRecord, IdentityScope
from healthcare_pipeline.identity.persistence import AesGcmIdentityRecordCipher


def _record() -> IdentityRecord:
    return IdentityRecord(
        record_id="record-token",
        source_system="epic",
        scope=IdentityScope("tenant-a", "enterprise"),
        patient=Patient(
            identifiers=(Identifier("MRN-1", system="hospital-a"),),
            names=(HumanName(family="Doe", given=("Jane",)),),
            birth_date=date(1990, 1, 2),
        ),
    )


def test_cipher_round_trip_and_random_nonce() -> None:
    cipher = AesGcmIdentityRecordCipher(b"a" * 32)
    record = _record()
    first = cipher.encrypt(record)
    second = cipher.encrypt(record)
    assert first.nonce != second.nonce
    restored = cipher.decrypt(
        record_id=record.record_id,
        source_system=record.source_system,
        scope=record.scope,
        nonce=first.nonce,
        ciphertext=first.ciphertext,
    )
    assert restored == record


def test_cipher_binds_ciphertext_to_record_metadata() -> None:
    cipher = AesGcmIdentityRecordCipher(b"a" * 32)
    record = _record()
    encrypted = cipher.encrypt(record)
    with pytest.raises(InvalidTag):
        cipher.decrypt(
            record_id="different-record",
            source_system=record.source_system,
            scope=record.scope,
            nonce=encrypted.nonce,
            ciphertext=encrypted.ciphertext,
        )
