from enum import StrEnum


class TenantStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class OrganizationType(StrEnum):
    HEALTH_SYSTEM = "health_system"
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    PHYSICIAN_PRACTICE = "physician_practice"
    LABORATORY = "laboratory"
    PHARMACY = "pharmacy"
    PAYER = "payer"
    CLEARINGHOUSE = "clearinghouse"
    PUBLIC_HEALTH_AGENCY = "public_health_agency"
    HEALTH_INFORMATION_EXCHANGE = "health_information_exchange"
    DEPARTMENT = "department"
    OTHER = "other"


class OrganizationIdentifierType(StrEnum):
    NPI = "npi"
    CLIA = "clia"
    TAX_ID = "tax_id"
    PAYER_ID = "payer_id"
    PHARMACY_ID = "pharmacy_id"
    STATE_LICENSE = "state_license"
    INTERNAL = "internal"
    OTHER = "other"


class LocationStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class LocationMode(StrEnum):
    INSTANCE = "instance"
    KIND = "kind"


class LocationType(StrEnum):
    CAMPUS = "campus"
    BUILDING = "building"
    WING = "wing"
    FLOOR = "floor"
    DEPARTMENT = "department"
    WARD = "ward"
    ROOM = "room"
    BED = "bed"
    CLINIC = "clinic"
    LABORATORY = "laboratory"
    PHARMACY = "pharmacy"
    MOBILE_UNIT = "mobile_unit"
    VIRTUAL = "virtual"
    OTHER = "other"


class SourceSystemType(StrEnum):
    EHR = "ehr"
    LABORATORY_INFORMATION_SYSTEM = "laboratory_information_system"
    PHARMACY_SYSTEM = "pharmacy_system"
    CLAIMS_SYSTEM = "claims_system"
    PACS = "pacs"
    RADIOLOGY_INFORMATION_SYSTEM = "radiology_information_system"
    INTERFACE_ENGINE = "interface_engine"
    PATIENT_PORTAL = "patient_portal"
    MOBILE_APPLICATION = "mobile_application"
    FILE_IMPORT = "file_import"
    EXTERNAL_API = "external_api"
    OTHER = "other"


class DataStandard(StrEnum):
    FHIR_R4 = "fhir_r4"
    HL7_V2 = "hl7_v2"
    X12 = "x12"
    NCPDP = "ncpdp"
    DICOM = "dicom"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    CUSTOM = "custom"
    
class IngestionBatchStatus(StrEnum):
    RECEIVING = "receiving"
    RECEIVED = "received"
    PROCESSING = "processing"
    PARTIALLY_COMPLETED = "partially_completed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RawRecordStatus(StrEnum):
    RECEIVED = "received"
    DUPLICATE = "duplicate"
    QUEUED = "queued"
    PROCESSING = "processing"
    VALIDATED = "validated"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestionTransport(StrEnum):
    REST_API = "rest_api"
    FHIR_API = "fhir_api"
    MLLP = "mllp"
    SFTP = "sftp"
    FILE_UPLOAD = "file_upload"
    MESSAGE_BROKER = "message_broker"
    DATABASE_IMPORT = "database_import"
    DICOMWEB = "dicomweb"
    MANUAL = "manual"
    OTHER = "other"


class PayloadEncoding(StrEnum):
    UTF_8 = "utf_8"
    UTF_16 = "utf_16"
    ASCII = "ascii"
    BASE64 = "base64"
    BINARY = "binary"
    OTHER = "other"


class CompressionType(StrEnum):
    NONE = "none"
    GZIP = "gzip"
    ZIP = "zip"
    ZSTD = "zstd"
    OTHER = "other"

class ProcessingJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    RETRY_SCHEDULED = "retry_scheduled"
    SUCCEEDED = "succeeded"
    PARTIALLY_SUCCEEDED = "partially_succeeded"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"
    CANCELLED = "cancelled"


class ProcessingStage(StrEnum):
    RECEIPT_VALIDATION = "receipt_validation"
    STRUCTURAL_VALIDATION = "structural_validation"
    SEMANTIC_VALIDATION = "semantic_validation"
    TERMINOLOGY_VALIDATION = "terminology_validation"
    TRANSFORMATION = "transformation"
    PATIENT_MATCHING = "patient_matching"
    CANONICALIZATION = "canonicalization"
    FHIR_MAPPING = "fhir_mapping"
    PERSISTENCE = "persistence"
    PUBLICATION = "publication"


class ValidationSeverity(StrEnum):
    INFORMATION = "information"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


class ValidationCategory(StrEnum):
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    TERMINOLOGY = "terminology"
    BUSINESS_RULE = "business_rule"
    SECURITY = "security"
    PRIVACY = "privacy"


class ValidationOutcome(StrEnum):
    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"


class TransformationStatus(StrEnum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class DeadLetterStatus(StrEnum):
    OPEN = "open"
    RETRY_SCHEDULED = "retry_scheduled"
    REPROCESSING = "reprocessing"
    RESOLVED = "resolved"
    DISCARDED = "discarded"


class ErrorRecoverability(StrEnum):
    RETRYABLE = "retryable"
    NON_RETRYABLE = "non_retryable"
    UNKNOWN = "unknown"


class CheckpointStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    INVALIDATED = "invalidated"
