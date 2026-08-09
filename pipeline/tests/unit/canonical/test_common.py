from datetime import UTC, datetime
from decimal import Decimal

import pytest

from healthcare_pipeline.canonical import (
    Coding,
    HumanName,
    Identifier,
    Period,
    Quantity,
)


def test_identifier_normalizes_and_exposes_identity_key() -> None:
    identifier = Identifier(value=" 12345 ", system=" Hospital ", type_code="mr")

    assert identifier.value == "12345"
    assert identifier.identity_key == ("hospital", "12345", "MR")


def test_coding_requires_code_or_display() -> None:
    with pytest.raises(ValueError, match="code or display"):
        Coding()


def test_human_name_requires_family_or_given() -> None:
    with pytest.raises(ValueError, match="family or given"):
        HumanName()


def test_period_requires_timezone_aware_values_and_order() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        Period(start=datetime(2026, 8, 7, 10, 0))

    with pytest.raises(ValueError, match="must not precede"):
        Period(
            start=datetime(2026, 8, 7, 11, 0, tzinfo=UTC),
            end=datetime(2026, 8, 7, 10, 0, tzinfo=UTC),
        )


def test_quantity_uses_decimal_and_rejects_negative_values() -> None:
    quantity = Quantity(Decimal("1.25"))
    assert quantity.value == Decimal("1.25")

    with pytest.raises(ValueError, match="must not be negative"):
        Quantity(Decimal("-0.01"))
