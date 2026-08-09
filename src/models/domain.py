"""Domain data models and schemas for DocuMesh."""

from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    CONTRACT = "CONTRACT"
    AMENDMENT = "AMENDMENT"
    STATUS_REPORT = "STATUS_REPORT"
    INVOICE = "INVOICE"
    MEETING_MINUTES = "MEETING_MINUTES"
    MATERIAL_RECEIPT = "MATERIAL_RECEIPT"
    CORRESPONDENCE = "CORRESPONDENCE"
    OTHER = "OTHER"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class FindingType(str, Enum):
    INTERNAL_ARITHMETIC_ERROR = "INTERNAL_ARITHMETIC_ERROR"
    INTERNAL_QUANTITY_MISMATCH = "INTERNAL_QUANTITY_MISMATCH"
    CROSS_DOC_CONTRADICTION = "CROSS_DOC_CONTRADICTION"
    UNEARNED_PROGRESS_BILLING = "UNEARNED_PROGRESS_BILLING"
    CONTRACT_TERM_MISMATCH = "CONTRACT_TERM_MISMATCH"
    RECEIPT_PROGRESS_CONTRADICTION = "RECEIPT_PROGRESS_CONTRADICTION"
    PROMPT_INJECTION_WARNING = "PROMPT_INJECTION_WARNING"
    MISSING_DOCUMENT_REFERENCE = "MISSING_DOCUMENT_REFERENCE"


class FindingStatus(str, Enum):
    DETECTED = "DETECTED"
    PRESENTED = "PRESENTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"


class TextChunk(BaseModel):
    chunk_id: str
    doc_id: str
    doc_name: str
    section_title: Optional[str] = None
    page_num: Optional[int] = None
    text: str
    start_char: int
    end_char: int


class DocumentMetadata(BaseModel):
    doc_id: str
    project_id: str
    filename: str
    filepath: str
    format: str  # "docx", "pdf", "txt"
    checksum: str
    doc_type: DocumentType = DocumentType.OTHER
    classification_confidence: float = 1.0
    quarantined: bool = False
    quarantine_reason: Optional[str] = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    extracted_text: Optional[str] = None
    chunks: List[TextChunk] = Field(default_factory=list)


class SourceCitation(BaseModel):
    doc_id: str
    filename: str
    location: str  # e.g., "Section 4, paragraph 2" or "Page 2, Table 1"
    exact_quote: str


class ExtractedFact(BaseModel):
    fact_id: str
    project_id: str
    doc_id: str
    entity_type: str  # e.g., "CONTRACT_VALUE", "HANDOVER_DATE", "EXPENDITURE_SUM"
    entity_key: str   # canonical key e.g., "project:total_contract_value"
    attribute: str    # e.g., "value", "rate", "date"
    raw_value: str
    normalized_value: Union[int, float, str, Dict[str, Any]]
    unit: Optional[str] = None
    confidence: float = 1.0
    grounded: bool = True
    citation: SourceCitation
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


class Finding(BaseModel):
    finding_id: str
    project_id: str
    finding_type: FindingType
    severity: Severity
    title: str
    description: str
    source_a: SourceCitation
    source_b: Optional[SourceCitation] = None
    recommendation: str
    status: FindingStatus = FindingStatus.PRESENTED
    feedback: Optional[str] = None
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None  # "human" or "mcp" or "user_id"


class Rule(BaseModel):
    rule_id: str
    name: str
    check_type: str  # "ARITHMETIC", "PRESENCE", "CROSS_REFERENCE", "CONTRACT_MATCH"
    target_doc_type: DocumentType
    description: str
    severity: Severity


class ProjectRegisterEntry(BaseModel):
    entity_key: str
    title: str
    reconciled_value: Any
    unit: Optional[str] = None
    status: str  # "CORROBORATED", "SUPERSEDED", "CONTRADICTED", "SINGLE_SOURCE"
    primary_citation: SourceCitation
    history: List[Dict[str, Any]] = Field(default_factory=list)


class ProjectRegister(BaseModel):
    project_id: str
    project_name: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    content_hash: str
    entries: List[ProjectRegisterEntry] = Field(default_factory=list)
    approved_findings: List[Finding] = Field(default_factory=list)
    active_conflicts_count: int = 0


class NodeUsage(BaseModel):
    node_name: str
    calls_count: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    cost_usd: float = 0.0
    duration_ms: float = 0.0


class RunCostReport(BaseModel):
    run_id: str
    project_id: str
    total_cost_usd: float = 0.0
    total_duration_ms: float = 0.0
    node_breakdown: Dict[str, NodeUsage] = Field(default_factory=dict)
