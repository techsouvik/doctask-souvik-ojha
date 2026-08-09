"""LangGraph Pipeline State Schema."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from src.models.domain import (
    DocumentMetadata, ExtractedFact, Finding, ProjectRegister, RunCostReport
)


class PipelineState(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    project_id: str = "proj_greenfield_tech_park"
    run_id: str = "run_default"
    doc_folder: str = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
    documents: List[DocumentMetadata] = Field(default_factory=list)
    facts: List[ExtractedFact] = Field(default_factory=list)
    findings: List[Finding] = Field(default_factory=list)
    register: Optional[ProjectRegister] = None
    current_node: str = "INIT"
    status: str = "IN_PROGRESS"  # IN_PROGRESS, AWAITING_HUMAN_GATE, COMPLETED, FAILED
    pending_findings: List[Finding] = Field(default_factory=list)
    cost_report: Optional[RunCostReport] = None
    errors: List[str] = Field(default_factory=list)
