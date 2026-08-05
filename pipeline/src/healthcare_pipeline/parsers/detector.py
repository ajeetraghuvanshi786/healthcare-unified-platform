from __future__ import annotations

import csv
import io
import json
import xml.etree.ElementTree as ET

from healthcare_pipeline.parsers.exceptions import InvalidPayloadError
from healthcare_pipeline.parsers.metrics import NoOpParserMetrics, ParserMetrics
from healthcare_pipeline.parsers.types import MessageFormat


class MessageFormatDetector:
    def __init__(self, metrics: ParserMetrics | None = None) -> None:
        self._metrics = metrics or NoOpParserMetrics()

    def detect(self, payload: bytes) -> MessageFormat:
        if not isinstance(payload, bytes):
            raise TypeError("payload must be provided as bytes")
        if not payload:
            raise InvalidPayloadError("payload must not be empty")

        text = self._decode(payload)
        normalized = text.lstrip("\ufeff \t\r\n")

        detected = self._detect_text(normalized)
        self._metrics.record_detection(detected)
        return detected

    @staticmethod
    def _decode(payload: bytes) -> str:
        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError:
            return ""

    def _detect_text(self, text: str) -> MessageFormat:
        if not text:
            return MessageFormat.UNKNOWN
        if self._is_hl7_v2(text):
            return MessageFormat.HL7_V2
        if text.startswith("{") or text.startswith("["):
            return self._detect_json(text)
        if text.startswith("<"):
            return self._detect_xml(text)
        if self._is_csv(text):
            return MessageFormat.CSV
        return MessageFormat.UNKNOWN

    @staticmethod
    def _is_hl7_v2(text: str) -> bool:
        first_line = text.splitlines()[0] if text.splitlines() else text
        return len(first_line) >= 4 and first_line[:3] in {"MSH", "FHS", "BHS"} and first_line[3] not in {" ", "\t"}

    @staticmethod
    def _detect_json(text: str) -> MessageFormat:
        try:
            document = json.loads(text)
        except json.JSONDecodeError:
            return MessageFormat.UNKNOWN
        if isinstance(document, dict) and isinstance(document.get("resourceType"), str):
            return MessageFormat.FHIR_JSON
        return MessageFormat.JSON

    @staticmethod
    def _detect_xml(text: str) -> MessageFormat:
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            return MessageFormat.UNKNOWN
        local_name = root.tag.rsplit("}", maxsplit=1)[-1]
        namespace = root.tag[1:].split("}", maxsplit=1)[0] if root.tag.startswith("{") else ""
        if local_name == "ClinicalDocument":
            return MessageFormat.CDA_XML
        if namespace == "http://hl7.org/fhir" or root.attrib.get("xmlns") == "http://hl7.org/fhir":
            return MessageFormat.FHIR_XML
        return MessageFormat.XML

    @staticmethod
    def _is_csv(text: str) -> bool:
        lines = [line for line in text.splitlines() if line.strip()]
        if len(lines) < 2:
            return False
        try:
            sample = "\n".join(lines[:20])
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
            rows = list(csv.reader(io.StringIO(sample), dialect))
        except (csv.Error, UnicodeError):
            return False
        widths = {len(row) for row in rows if row}
        return len(widths) == 1 and next(iter(widths), 0) > 1
