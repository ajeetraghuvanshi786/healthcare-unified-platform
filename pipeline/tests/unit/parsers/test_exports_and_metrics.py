from healthcare_pipeline import parsers
from healthcare_pipeline.parsers import MessageFormat, NoOpParserMetrics


def test_parser_package_exports_are_resolvable() -> None:
    for name in parsers.__all__:
        assert hasattr(parsers, name)


def test_noop_metrics_accepts_detection_and_parse_measurements() -> None:
    metrics = NoOpParserMetrics()

    metrics.record_detection(MessageFormat.HL7_V2)
    metrics.record_parse(
        message_format=MessageFormat.HL7_V2,
        parser_name="hl7-parser",
        success=True,
        duration_ms=1.2,
    )
