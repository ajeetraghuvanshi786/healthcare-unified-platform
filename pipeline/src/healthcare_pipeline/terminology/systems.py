from healthcare_pipeline.terminology.models import TerminologySystem

LOINC = TerminologySystem(
    name="LOINC",
    canonical_uri="http://loinc.org",
    oid="2.16.840.1.113883.6.1",
    aliases=(
        "LN",
        "LOINC",
        "2.16.840.1.113883.6.1",
        "urn:oid:2.16.840.1.113883.6.1",
    ),
)

SNOMED_CT = TerminologySystem(
    name="SNOMED CT",
    canonical_uri="http://snomed.info/sct",
    oid="2.16.840.1.113883.6.96",
    aliases=(
        "SCT",
        "SNOMED",
        "SNOMED CT",
        "SNOMEDCT",
        "2.16.840.1.113883.6.96",
        "urn:oid:2.16.840.1.113883.6.96",
    ),
)

RXNORM = TerminologySystem(
    name="RxNorm",
    canonical_uri="http://www.nlm.nih.gov/research/umls/rxnorm",
    oid="2.16.840.1.113883.6.88",
    aliases=(
        "RXNORM",
        "RXN",
        "2.16.840.1.113883.6.88",
        "urn:oid:2.16.840.1.113883.6.88",
    ),
)

UCUM = TerminologySystem(
    name="UCUM",
    canonical_uri="http://unitsofmeasure.org",
    oid="2.16.840.1.113883.6.8",
    aliases=(
        "UCUM",
        "2.16.840.1.113883.6.8",
        "urn:oid:2.16.840.1.113883.6.8",
    ),
)

ICD10_CM = TerminologySystem(
    name="ICD-10-CM",
    canonical_uri="http://hl7.org/fhir/sid/icd-10-cm",
    oid="2.16.840.1.113883.6.90",
    aliases=(
        "ICD10CM",
        "ICD-10-CM",
        "2.16.840.1.113883.6.90",
        "urn:oid:2.16.840.1.113883.6.90",
        "http://terminology.hl7.org/CodeSystem/icd10CM",
    ),
)

NDC = TerminologySystem(
    name="NDC",
    canonical_uri="http://hl7.org/fhir/sid/ndc",
    oid="2.16.840.1.113883.6.69",
    aliases=(
        "NDC",
        "2.16.840.1.113883.6.69",
        "urn:oid:2.16.840.1.113883.6.69",
    ),
)

CPT = TerminologySystem(
    name="CPT",
    canonical_uri="http://www.ama-assn.org/go/cpt",
    oid="2.16.840.1.113883.6.12",
    aliases=(
        "CPT",
        "CPT4",
        "2.16.840.1.113883.6.12",
        "urn:oid:2.16.840.1.113883.6.12",
    ),
)

DEFAULT_TERMINOLOGY_SYSTEMS: tuple[TerminologySystem, ...] = (
    LOINC,
    SNOMED_CT,
    RXNORM,
    UCUM,
    ICD10_CM,
    NDC,
    CPT,
)
