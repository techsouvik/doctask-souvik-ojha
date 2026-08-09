"""FastAPI API Routes delegating to Application Layer Services."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.app.project_service import ProjectService
from src.app.finding_service import FindingService
from src.app.register_service import RegisterService

router = APIRouter(prefix="/api/v1")


class CreateProjectRequest(BaseModel):
    project_name: str
    doc_folder: Optional[str] = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"


class ApproveFindingRequest(BaseModel):
    finding_id: str
    approved: bool
    feedback: Optional[str] = None


class BatchApproveRequest(BaseModel):
    approved_all: bool = True
    decisions: Optional[Dict[str, bool]] = None


@router.post("/projects")
def create_project(req: CreateProjectRequest):
    project_id = ProjectService.create_project(req.project_name, req.doc_folder)
    return {"project_id": project_id, "status": "created", "doc_folder": req.doc_folder}


@router.post("/projects/{project_id}/run")
def trigger_run(project_id: str):
    state = ProjectService.run_pipeline_for_project(project_id)
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
    state = ProjectService.get_project_state(project_id)
    return {
        "project_id": project_id,
        "status": state.status,
        "current_node": state.current_node,
        "pending_findings_count": len(state.pending_findings),
        "register_ready": state.register is not None
    }


@router.get("/projects/{project_id}/findings")
def get_findings(project_id: str, status: Optional[str] = None):
    findings = FindingService.get_findings(project_id, status)
    return {"project_id": project_id, "findings": [f.model_dump() for f in findings]}


@router.post("/projects/{project_id}/findings/approve")
def approve_finding(project_id: str, req: ApproveFindingRequest):
    try:
        return FindingService.decide_finding(project_id, req.finding_id, req.approved, req.feedback)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/{project_id}/findings/batch-approve")
def batch_approve_findings(project_id: str, req: BatchApproveRequest):
    try:
        return FindingService.batch_decide_findings(project_id, req.approved_all, req.decisions)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/projects/{project_id}/register")
def get_register(project_id: str):
    try:
        reg = RegisterService.get_register(project_id)
        return reg.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/export-report", response_class=HTMLResponse)
def export_executive_report(project_id: str):
    try:
        html_content = RegisterService.generate_executive_report_html(project_id)
        return HTMLResponse(content=html_content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/graph")
def get_knowledge_graph(project_id: str):
    """Return nodes and edges for Knowledge Graph visualizer."""
    state = ProjectService.get_project_state(project_id)
    nodes = []
    edges = []

    # Document Nodes
    for doc in state.documents:
        nodes.append({
            "id": doc.doc_id,
            "label": doc.filename,
            "type": "DOCUMENT",
            "doc_type": doc.doc_type.value,
            "status": "QUARANTINED" if doc.quarantined else "ACTIVE"
        })

    # Finding Nodes & Conflict Edges
    for f in state.findings:
        f_node_id = f.finding_id
        nodes.append({
            "id": f_node_id,
            "label": f.title,
            "type": "FINDING",
            "severity": f.severity.value,
            "status": f.status.value
        })

        if f.source_a and f.source_a.doc_id:
            edges.append({
                "source": f.source_a.doc_id,
                "target": f_node_id,
                "label": "SRC_A",
                "is_conflict": True
            })

        if f.source_b and f.source_b.doc_id:
            edges.append({
                "source": f.source_b.doc_id,
                "target": f_node_id,
                "label": "SRC_B",
                "is_conflict": True
            })

    return {"project_id": project_id, "nodes": nodes, "edges": edges}
