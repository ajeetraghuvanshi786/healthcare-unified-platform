from __future__ import annotations

from enum import StrEnum

type ParsedData = object
type MetadataValue = str | int | float | bool | None
type Metadata = dict[str, MetadataValue]


class MessageFormat(StrEnum):
    HL7_V2 = "hl7_v2"
    FHIR_JSON = "fhir_json"
    FHIR_XML = "fhir_xml"
    CDA_XML = "cda_xml"
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    UNKNOWN = "unknown"
