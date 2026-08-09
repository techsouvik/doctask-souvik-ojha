"""FastAPI API Routes for DocuMesh Engine with SSE Streaming & Graph Visuals."""

import json
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel

from src.graph.state import PipelineState
from src.graph.workflow import build_documesh_graph, run_pipeline
from src.models.domain import FindingStatus
from src.tools.artifacts import AsyncArtifactsTools

router = APIRouter(prefix="/api/v1")

# Global in-memory session store (backed by state machine)
_ACTIVE_STATES: Dict[str, PipelineState] = {}
_artifacts_tool = AsyncArtifactsTools()


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

    state.pending_findings = [f for f in state.findings if f.status == FindingStatus.PRESENTED]

    if not state.pending_findings:
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


@router.get("/projects/{project_id}/graph")
def get_knowledge_graph(project_id: str):
    """Return nodes and edges for Knowledge Graph visualizer."""
    if project_id not in _ACTIVE_STATES:
        trigger_run(project_id)

    state = _ACTIVE_STATES[project_id]
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


@router.get("/projects/{project_id}/export-report", response_class=HTMLResponse)
async def export_executive_report(project_id: str):
    """Export styled executive HTML deliverable report."""
    if project_id not in _ACTIVE_STATES:
        trigger_run(project_id)

    state = _ACTIVE_STATES[project_id]
    reg = state.register

    if not reg:
        raise HTTPException(status_code=400, detail="Complete human gate before exporting executive report.")

    approved_list = [f for f in state.findings if f.status == FindingStatus.APPROVED]

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Executive Document Reconciliation Report — {reg.project_name}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #1e293b; background: #f8fafc; }}
            .header {{ background: #0f172a; color: white; padding: 24px; border-radius: 8px; margin-bottom: 30px; }}
            .card {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
            th {{ background: #f1f5f9; font-weight: 600; color: #475569; }}
            .tag {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; }}
            .tag-critical {{ background: #ffe4e6; color: #9f1239; }}
            .tag-high {{ background: #fef3c7; color: #92400e; }}
            .tag-medium {{ background: #e0f2fe; color: #075985; }}
            .quote {{ background: #f8fafc; border-left: 3px solid #6366f1; padding: 8px 12px; font-style: italic; font-size: 13px; font-family: monospace; margin-top: 6px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 style="margin:0;">DocuMesh Executive Reconciliation Report</h1>
            <p style="margin:5px 0 0 0; opacity:0.8;">{reg.project_name} • Version {reg.version} • Hash: {reg.content_hash}</p>
        </div>

        <div class="card">
            <h2>Executive Summary</h2>
            <p>Processed <strong>{len(state.documents)} documents</strong> across the project pile. Reconciled <strong>{len(reg.entries)} core entity metrics</strong> and identified <strong>{len(approved_list)} confirmed findings</strong> requiring management attention.</p>
        </div>

        <div class="card">
            <h2>Active Approved Findings ({len(approved_list)})</h2>
            {"".join([f'''
                <div style="border-bottom: 1px solid #f1f5f9; padding-bottom: 15px; margin-bottom: 15px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="margin:0;">[{f.finding_id}] {f.title}</h3>
                        <span class="tag tag-{f.severity.value.lower()}">{f.severity.value}</span>
                    </div>
                    <p style="font-size:14px; color:#334155;">{f.description}</p>
                    <div class="quote"><strong>Source A ({f.source_a.filename}):</strong> "{f.source_a.exact_quote}"</div>
                    {f'<div class="quote"><strong>Source B ({f.source_b.filename}):</strong> "{f.source_b.exact_quote}"</div>' if f.source_b else ''}
                    <p style="font-size:13px; color:#4f46e5; margin-top:8px;"><strong>Recommendation:</strong> {f.recommendation}</p>
                </div>
            ''' for f in approved_list])}
        </div>

        <div class="card">
            <h2>Reconciled Project Register</h2>
            <table>
                <thead>
                    <tr><th>Metric</th><th>Reconciled Value</th><th>Status</th><th>Primary Source</th></tr>
                </thead>
                <tbody>
                    {"".join([f'''
                        <tr>
                            <td><strong>{e.title}</strong></td>
                            <td style="font-family:monospace;">{e.reconciled_value}</td>
                            <td><span class="tag">{e.status}</span></td>
                            <td>{e.primary_citation.filename} ({e.primary_citation.location})</td>
                        </tr>
                    ''' for e in reg.entries])}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)
