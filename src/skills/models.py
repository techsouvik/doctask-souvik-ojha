"""Data models for Dynamic Skill & Playbook Engine."""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from src.models.domain import DocumentType, Severity, FindingType


class SkillRule(BaseModel):
    rule_id: str = Field(default_factory=lambda: f"S_RUL_{uuid.uuid4().hex[:6]}")
    rule_name: str
    condition_expression: str  # e.g., "fact.entity_key == 'invoice:gstin' and fact.raw_value != '29AAAAA0000A1Z5'"
    finding_type: FindingType = FindingType.CONTRACT_TERM_MISMATCH
    severity: Severity = Severity.HIGH
    finding_title: str
    finding_description: str
    recommendation: str
    resolution_action: Optional[str] = None


class Skill(BaseModel):
    skill_id: str = Field(default_factory=lambda: f"skill_{uuid.uuid4().hex[:8]}")
    name: str
    description: str
    trigger_doc_types: List[DocumentType] = Field(default_factory=list)  # Target doc types
    trigger_keywords: List[str] = Field(default_factory=list)            # Trigger keywords in doc text
    category: str = "COMPLIANCE"
    version: int = 1
    rules: List[SkillRule] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True
