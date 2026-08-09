"""Skills REST API Router for dynamic skill creation and execution."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.skills.models import Skill, SkillRule
from src.skills.registry import global_skill_registry
from src.models.domain import Severity, FindingType

router = APIRouter(prefix="/projects/{project_id}/skills", tags=["Skills & Playbooks"])


class RegisterSkillRequest(BaseModel):
    name: str
    description: str
    category: Optional[str] = "COMPLIANCE"
    rule_name: str
    finding_title: str
    finding_description: str
    severity: Optional[str] = "HIGH"
    recommendation: str
    resolution_action: Optional[str] = None


@router.get("")
def list_skills(project_id: str, category: Optional[str] = None):
    """List all registered skills/playbooks."""
    skills = global_skill_registry.list_skills(category)
    return {"project_id": project_id, "skills": [s.model_dump() for s in skills]}


@router.post("")
def register_user_skill(project_id: str, req: RegisterSkillRequest):
    """Register a new custom skill/playbook dynamically."""
    sev = Severity.HIGH
    if req.severity:
        try:
            sev = Severity[req.severity.upper()]
        except KeyError:
            sev = Severity.HIGH

    rule = SkillRule(
        rule_name=req.rule_name,
        condition_expression="user_defined_condition",
        finding_title=req.finding_title,
        finding_description=req.finding_description,
        severity=sev,
        recommendation=req.recommendation,
        resolution_action=req.resolution_action
    )

    skill = Skill(
        name=req.name,
        description=req.description,
        category=req.category or "CUSTOM",
        rules=[rule]
    )

    registered = global_skill_registry.register_skill(skill)
    return {"project_id": project_id, "status": "registered", "skill": registered.model_dump()}


@router.delete("/{skill_id}")
def delete_user_skill(project_id: str, skill_id: str):
    """Delete or unregister a skill."""
    deleted = global_skill_registry.delete_skill(skill_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Skill {skill_id} not found")

    return {"project_id": project_id, "status": "deleted", "skill_id": skill_id}
