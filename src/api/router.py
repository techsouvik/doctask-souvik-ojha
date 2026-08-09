"""FastAPI API Routes for DocuMesh Engine."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.graph.state import PipelineState
from src.graph.workflow import build_documesh_graph, run_pipeline
from src.models.domain import FindingStatus

router = APIRouter(prefix="/api/v1")

# Global in-memory session store (backed by state machine)
_ACTIVE_STATES: Dict[str, PipelineState] = {}


class CreateProjectRequest(BaseModel):
    project_name: str
    doc_folder: Optional[str] = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"


class ApproveFindingRequest(BaseModel):
    finding_id: str
    approved: bool
    feedback: Optional[str] = None


class BatchApproveRequest(BaseModel):
    approved_all: bool = True
    decisions: Optional[Dict[str, bool]] = None  # finding_id -> bool


@router.post("/projects")
def create_project(req: CreateProjectRequest):
    project_id = f"proj_{req.project_name.lower().replace(' ', '_')}"
    state = PipelineState(
        project_id=project_id,
        doc_folder=req.doc_folder or "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
    )
    _ACTIVE_STATES[project_id] = state
    return {"project_id": project_id, "status": "created", "doc_folder": state.doc_folder}


@router.post("/projects/{project_id}/run")
def trigger_run(project_id: str):
    folder = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
    if project_id in _ACTIVE_STATES:
        folder = _ACTIVE_STATES[project_id].doc_folder

    state = run_pipeline(doc_folder=folder, project_id=project_id, run_id="run_latest")
    _ACTIVE_STATES[project_id] = state

    return {
        "project_id": project_id,
        "status": state.status,
        "current_node": state.current_node,
        "documents_count": len(state.documents),
        "facts_count": len(state.facts),
        "findings_count": len(state.findings),
        "pending_findings_count": len(state.pending_findings)
    }


@router.get("/projects/{project_id}/status")
def get_status(project_id: str):
    if project_id not in _ACTIVE_STATES:
        trigger_run(project_id)

    state = _ACTIVE_STATES[project_id]
    return {
        "project_id": project_id,
        "status": state.status,
        "current_node": state.current_node,
        "pending_findings_count": len(state.pending_findings),
        "register_ready": state.register is not None
    }


@router.get("/projects/{project_id}/findings")
def get_findings(project_id: str, status: Optional[str] = None):
    if project_id not in _ACTIVE_STATES:
        trigger_run(project_id)

    state = _ACTIVE_STATES[project_id]
    findings = state.findings

    if status:
        findings = [f for f in findings if f.status.value == status.upper()]

    return {"project_id": project_id, "findings": [f.model_dump() for f in findings]}


@router.post("/projects/{project_id}/findings/approve")
def approve_finding(project_id: str, req: ApproveFindingRequest):
    if project_id not in _ACTIVE_STATES:
        raise HTTPException(status_code=404, detail="Project not found")

    state = _ACTIVE_STATES[project_id]
    target_finding = None

    for f in state.findings:
        if f.finding_id == req.finding_id:
            target_finding = f
            f.status = FindingStatus.APPROVED if req.approved else FindingStatus.REJECTED
            f.feedback = req.feedback
            break

    if not target_finding:
        raise HTTPException(status_code=404, detail="Finding ID not found")

    # Update pending list
    state.pending_findings = [f for f in state.findings if f.status == FindingStatus.PRESENTED]

    # If all pending findings resolved, resume graph execution to DELIVER
    if not state.pending_findings:
        print(f"All findings resolved for project {project_id}. Resuming graph to DELIVER...")
        graph = build_documesh_graph()
        final_dict = graph.invoke(state)
        if isinstance(final_dict, dict):
            _ACTIVE_STATES[project_id] = PipelineState(**final_dict)

    return {
        "finding_id": req.finding_id,
        "new_status": target_finding.status.value,
        "remaining_pending": len(_ACTIVE_STATES[project_id].pending_findings),
        "pipeline_status": _ACTIVE_STATES[project_id].status
    }


@router.post("/projects/{project_id}/findings/batch-approve")
def batch_approve_findings(project_id: str, req: BatchApproveRequest):
    if project_id not in _ACTIVE_STATES:
        raise HTTPException(status_code=404, detail="Project not found")

    state = _ACTIVE_STATES[project_id]

    for f in state.findings:
        if f.status == FindingStatus.PRESENTED:
            if req.decisions and f.finding_id in req.decisions:
                decision = req.decisions[f.finding_id]
            else:
                decision = req.approved_all

            f.status = FindingStatus.APPROVED if decision else FindingStatus.REJECTED

    state.pending_findings = []

    # Resume graph execution
    graph = build_documesh_graph()
    final_dict = graph.invoke(state)
    if isinstance(final_dict, dict):
        _ACTIVE_STATES[project_id] = PipelineState(**final_dict)

    reg = _ACTIVE_STATES[project_id].register
    return {
        "project_id": project_id,
        "status": _ACTIVE_STATES[project_id].status,
        "register_hash": reg.content_hash if reg else None
    }


@router.get("/projects/{project_id}/register")
def get_register(project_id: str):
    if project_id not in _ACTIVE_STATES:
        trigger_run(project_id)

    state = _ACTIVE_STATES[project_id]
    if not state.register:
        raise HTTPException(status_code=400, detail="Register deliverable not yet generated. Complete human gate first.")

    return state.register.model_dump()
