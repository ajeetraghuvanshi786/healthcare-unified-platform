from __future__ import annotations

from healthcare_pipeline.parsers.exceptions import InvalidPayloadError


class HL7PayloadDecoder:
    """Decode exact HL7 payload bytes without interpreting message structure.

    HL7 v2 is commonly transported as UTF-8 in modern integrations. This
    decoder deliberately accepts only UTF-8 for the first implementation so
    invalid or ambiguous byte sequences are rejected instead of being silently
    replaced and corrupting clinical data.
    """

    _UTF8_BOM = b"\xef\xbb\xbf"

    def decode(self, payload: bytes) -> str:
        """Return decoded HL7 text after removing an optional UTF-8 BOM."""

        if not isinstance(payload, bytes):
            raise TypeError("payload must be provided as bytes")
        if not payload:
            raise InvalidPayloadError("HL7 payload must not be empty")

        payload_without_bom = (
            payload[len(self._UTF8_BOM) :]
            if payload.startswith(self._UTF8_BOM)
            else payload
        )
        if not payload_without_bom:
            raise InvalidPayloadError("HL7 payload must contain message content")

        try:
            decoded = payload_without_bom.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise InvalidPayloadError("HL7 payload is not valid UTF-8") from exc

        if "\x00" in decoded:
            raise InvalidPayloadError("HL7 payload must not contain NUL characters")
        if not decoded:
            raise InvalidPayloadError("HL7 payload must contain message content")

        return decoded
