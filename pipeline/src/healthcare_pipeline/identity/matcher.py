from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.identity.models import (
    IdentityCandidateMatch,
    IdentityRecord,
    IdentityResolutionStatus,
    MatchEvidence,
    MatchEvidenceType,
)
from healthcare_pipeline.identity.normalization import PatientIdentityNormalizer


@dataclass(frozen=True, slots=True)
class DeterministicPatientMatcher:
    """Conservative matcher: only a shared scoped identifier can be deterministic."""

    normalizer: PatientIdentityNormalizer = PatientIdentityNormalizer()

    def compare(self, source: IdentityRecord, candidate: IdentityRecord) -> IdentityCandidateMatch:
        if source.scope != candidate.scope:
            return IdentityCandidateMatch(candidate.record_id, IdentityResolutionStatus.NO_MATCH)

        source_features = self.normalizer.normalize(source.patient)
        candidate_features = self.normalizer.normalize(candidate.patient)
        evidence: list[MatchEvidence] = []

        identifier_matches = set(source_features.scoped_identifiers).intersection(
            candidate_features.scoped_identifiers
        )
        if identifier_matches:
            evidence.append(
                MatchEvidence(
                    MatchEvidenceType.SCOPED_IDENTIFIER_EXACT,
                    "patient.identifiers",
                    "patient.identifiers",
                )
            )

        if source_features.birth_date is not None and candidate_features.birth_date is not None:
            if source_features.birth_date == candidate_features.birth_date:
                evidence.append(
                    MatchEvidence(
                        MatchEvidenceType.BIRTH_DATE_EXACT,
                        "patient.birth_date",
                        "patient.birth_date",
                    )
                )
            else:
                evidence.append(
                    MatchEvidence(
                        MatchEvidenceType.BIRTH_DATE_CONFLICT,
                        "patient.birth_date",
                        "patient.birth_date",
                    )
                )

        if set(source_features.name_keys).intersection(candidate_features.name_keys):
            evidence.append(
                MatchEvidence(
                    MatchEvidenceType.NAME_EXACT,
                    "patient.names",
                    "patient.names",
                )
            )
        if set(source_features.phones).intersection(candidate_features.phones):
            evidence.append(
                MatchEvidence(
                    MatchEvidenceType.PHONE_EXACT,
                    "patient.telecom",
                    "patient.telecom",
                )
            )
        if set(source_features.emails).intersection(candidate_features.emails):
            evidence.append(
                MatchEvidence(
                    MatchEvidenceType.EMAIL_EXACT,
                    "patient.telecom",
                    "patient.telecom",
                )
            )
        if set(source_features.postal_codes).intersection(candidate_features.postal_codes):
            evidence.append(
                MatchEvidence(
                    MatchEvidenceType.POSTAL_CODE_EXACT,
                    "patient.addresses",
                    "patient.addresses",
                )
            )

        evidence_types = {item.evidence_type for item in evidence}
        if MatchEvidenceType.SCOPED_IDENTIFIER_EXACT in evidence_types:
            status = (
                IdentityResolutionStatus.CONFLICT
                if MatchEvidenceType.BIRTH_DATE_CONFLICT in evidence_types
                else IdentityResolutionStatus.DETERMINISTIC_MATCH
            )
        elif {
            MatchEvidenceType.NAME_EXACT,
            MatchEvidenceType.BIRTH_DATE_EXACT,
        }.issubset(evidence_types) and (
            MatchEvidenceType.PHONE_EXACT in evidence_types
            or MatchEvidenceType.EMAIL_EXACT in evidence_types
            or MatchEvidenceType.POSTAL_CODE_EXACT in evidence_types
        ):
            status = IdentityResolutionStatus.POSSIBLE_MATCH
        else:
            status = IdentityResolutionStatus.NO_MATCH

        return IdentityCandidateMatch(candidate.record_id, status, tuple(evidence))
