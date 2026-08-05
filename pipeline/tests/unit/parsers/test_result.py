from types import MappingProxyType

import pytest

from healthcare_pipeline.parsers import MessageFormat, ParseIssue, ParseResult


def build_success_result() -> ParseResult:
    return ParseResult(
        message_format=MessageFormat.JSON,
        parser_name="json-parser",
        parser_version="1.0.0",
        correlation_id="corr-1",
        success=True,
        duration_ms=1.25,
        data={"patient": "1"},
        metadata={"source": "unit-test"},
    )


def test_parse_result_is_immutable() -> None:
    result = build_success_result()

    with pytest.raises(AttributeError):
        result.success = False  # type: ignore[misc]


def test_parse_result_copies_and_freezes_metadata() -> None:
    metadata = {"source": "unit-test"}
    result = ParseResult(
        message_format=MessageFormat.JSON,
        parser_name="json-parser",
        parser_version="1.0.0",
        correlation_id="corr-1",
        success=True,
        duration_ms=1.0,
        metadata=metadata,
    )
    metadata["source"] = "changed"

    assert isinstance(result.metadata, MappingProxyType)
    assert result.metadata["source"] == "unit-test"
    with pytest.raises(TypeError):
        result.metadata["new"] = "value"  # type: ignore[index]


def test_success_result_cannot_contain_errors() -> None:
    with pytest.raises(ValueError, match="must not contain errors"):
        ParseResult(
            message_format=MessageFormat.JSON,
            parser_name="json-parser",
            parser_version="1.0.0",
            correlation_id="corr-1",
            success=True,
            duration_ms=1.0,
            errors=(ParseIssue(code="invalid", message="invalid"),),
        )


def test_failure_result_requires_error() -> None:
    with pytest.raises(ValueError, match="at least one error"):
        ParseResult(
            message_format=MessageFormat.JSON,
            parser_name="json-parser",
            parser_version="1.0.0",
            correlation_id="corr-1",
            success=False,
            duration_ms=1.0,
        )


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("parser_name", " ", "parser_name"),
        ("parser_version", " ", "parser_version"),
        ("correlation_id", " ", "correlation_id"),
    ],
)
def test_parse_result_rejects_blank_identity_fields(
    field: str,
    value: str,
    match: str,
) -> None:
    arguments = {
        "message_format": MessageFormat.JSON,
        "parser_name": "json-parser",
        "parser_version": "1.0.0",
        "correlation_id": "corr-1",
        "success": True,
        "duration_ms": 1.0,
    }
    arguments[field] = value

    with pytest.raises(ValueError, match=match):
        ParseResult(**arguments)  # type: ignore[arg-type]


def test_parse_issue_requires_code_and_message() -> None:
    with pytest.raises(ValueError, match="code"):
        ParseIssue(code=" ", message="invalid")
    with pytest.raises(ValueError, match="message"):
        ParseIssue(code="invalid", message=" ")
