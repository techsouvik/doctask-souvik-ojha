"""Projects API Router for workspace management & pipeline execution."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.app.project_service import ProjectService, _ACTIVE_STATES
from src.app.register_service import RegisterService

router = APIRouter(prefix="/projects", tags=["Projects"])


class CreateProjectRequest(BaseModel):
    project_name: str
    doc_folder: Optional[str] = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"


@router.post("")
def create_project(req: CreateProjectRequest):
    """Create a new project workspace."""
    project_id = ProjectService.create_project(req.project_name, req.doc_folder)
    return {"project_id": project_id, "status": "created", "doc_folder": req.doc_folder}


@router.get("")
def list_projects():
    """List active project workspaces."""
    return {"projects": list(_ACTIVE_STATES.keys())}


@router.post("/{project_id}/run")
def trigger_run(project_id: str):
    """Trigger or resume pipeline state machine execution."""
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


@router.get("/{project_id}/status")
def get_status(project_id: str):
    """Get project status and checkpoint information."""
    state = ProjectService.get_project_state(project_id)
    return {
        "project_id": project_id,
        "status": state.status,
        "current_node": state.current_node,
        "pending_findings_count": len(state.pending_findings),
        "register_ready": state.register is not None
    }


@router.get("/{project_id}/register")
def get_register(project_id: str):
    """Get final reconciled Project Register deliverable."""
    try:
        reg = RegisterService.get_register(project_id)
        return reg.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/export-report", response_class=HTMLResponse)
def export_executive_report(project_id: str):
    """Export executive HTML deliverable report."""
    try:
        html_content = RegisterService.generate_executive_report_html(project_id)
        return HTMLResponse(content=html_content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/graph")
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
