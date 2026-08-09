"""Findings & Gate API Router for Human/MCP Gate decisions."""

from typing import Optional, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.app.finding_service import FindingService

router = APIRouter(prefix="/projects/{project_id}/findings", tags=["Findings & Gate"])


class ApproveFindingRequest(BaseModel):
    finding_id: str
    approved: bool
    feedback: Optional[str] = None


class BatchApproveRequest(BaseModel):
    approved_all: bool = True
    decisions: Optional[Dict[str, bool]] = None


@router.get("")
def get_findings(project_id: str, status: Optional[str] = None):
    """List all findings for a project, optionally filtered by status."""
    findings = FindingService.get_findings(project_id, status)
    return {"project_id": project_id, "findings": [f.model_dump() for f in findings]}


@router.get("/{finding_id}")
def get_finding_detail(project_id: str, finding_id: str):
    """Get single finding detail."""
    findings = FindingService.get_findings(project_id)
    target = next((f for f in findings if f.finding_id == finding_id), None)

    if not target:
        raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found in project {project_id}")

    return target.model_dump()


@router.post("/approve")
def approve_finding(project_id: str, req: ApproveFindingRequest):
    """Approve or reject a finding at the Human/MCP Gate."""
    try:
        return FindingService.decide_finding(project_id, req.finding_id, req.approved, req.feedback)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/batch-approve")
def batch_approve_findings(project_id: str, req: BatchApproveRequest):
    """Batch approve or reject findings."""
    try:
        return FindingService.batch_decide_findings(project_id, req.approved_all, req.decisions)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
