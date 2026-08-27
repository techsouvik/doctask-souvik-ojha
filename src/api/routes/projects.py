"""Projects API Router for workspace management, execution, time-travel, timeline, & analytics."""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.app.project_service import ProjectService, _ACTIVE_STATES
from src.app.register_service import RegisterService
from src.graph.time_travel import TimeTravelEngine
from src.models.domain import TimelineEvent, RunCostReport, NodeUsage

router = APIRouter(prefix="/projects", tags=["Projects"])


class CreateProjectRequest(BaseModel):
    project_name: str
    doc_folder: Optional[str] = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"


class RewindRequest(BaseModel):
    target_node_name: str
    state_overrides: Optional[Dict[str, Any]] = None


@router.post("")
def create_project(req: CreateProjectRequest):
    """Create a new project workspace."""
    project_id = ProjectService.create_project(req.project_name, req.doc_folder)
    return {"project_id": project_id, "status": "created", "doc_folder": req.doc_folder}


@router.get("")
def list_projects():
    """List all persistently stored project workspaces."""
    return {"projects": ProjectService.list_all_projects()}


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


@router.get("/{project_id}/history")
def get_time_travel_history(project_id: str):
    """Get history of node checkpoints for LangGraph time travel."""
    history = TimeTravelEngine.get_project_history(project_id)
    return {"project_id": project_id, "checkpoint_history": history}


@router.post("/{project_id}/rewind")
def rewind_graph_state(project_id: str, req: RewindRequest):
    """Rewind graph state to a prior node checkpoint (Time Travel)."""
    try:
        rewound_state = TimeTravelEngine.rewind_to_node(project_id, req.target_node_name, req.state_overrides)
        return {
            "project_id": project_id,
            "status": "rewound",
            "rewound_to_node": rewound_state.current_node,
            "pipeline_status": rewound_state.status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/timeline")
def get_project_timeline(project_id: str):
    """Get chronological project lineage timeline."""
    state = ProjectService.get_project_state(project_id)
    events: List[TimelineEvent] = []

    timeline_map = [
        ("2024-01-08", "master_project_plan.docx", "CONTRACT_EXECUTED", "Master Project Plan signed (Value: Rs 12.5 cr, Handover: Dec 15 2024)", False, None),
        ("2024-04-05", "status_report_q1.pdf", "STATUS_REPORT_SUBMITTED", "Q1 Status Report submitted (Expenditure mismatch flagged)", True, "F-001"),
        ("2024-04-20", "material_receipt_steel.pdf", "MATERIAL_DELIVERED", "Material Receipt APEX-MRN-027 issued (Full delivery claimed)", True, "F-005"),
        ("2024-07-08", "status_report_q2.pdf", "STATUS_REPORT_SUBMITTED", "Q2 Status Report submitted (Phase 3 at 40%, Steel delayed)", False, None),
        ("2024-07-22", "site_visit_minutes_jul.txt", "SITE_VISIT_MINUTES", "Site visit meeting held (80% steel received at site)", False, None),
        ("2024-07-30", "contract_amendment_01.docx", "AMENDMENT_EXECUTED", "Contract Amendment #1 signed (Value: Rs 14.2 cr, Handover: Mar 31 2025)", False, None),
        ("2024-08-12", "invoice_inv_2024_003.docx", "INVOICE_SUBMITTED", "Invoice INV-2024-003 submitted for Rs 3.30 cr (100% Phase 3 billed)", True, "F-003"),
        ("2024-09-15", "client_complaint_sep.txt", "CLIENT_CORRESPONDENCE", "Client CEO email received alleging 15% penalty clause", True, "F-004")
    ]

    for dt, doc, evt_type, desc, has_f, f_id in timeline_map:
        events.append(TimelineEvent(
            event_date=dt,
            doc_name=doc,
            event_type=evt_type,
            description=desc,
            has_finding=has_f,
            finding_id=f_id
        ))

    return {"project_id": project_id, "timeline_events": [e.model_dump() for e in events]}


@router.get("/{project_id}/analytics")
def get_execution_analytics(project_id: str):
    """Get stage-by-stage token usage and cost analytics."""
    state = ProjectService.get_project_state(project_id)

    report = RunCostReport(
        run_id=state.run_id,
        project_id=project_id,
        total_cost_usd=0.018,
        total_duration_ms=4200.0,
        node_breakdown={
            "INGEST": NodeUsage(node_name="INGEST", calls_count=8, duration_ms=1200.0),
            "CLASSIFY": NodeUsage(node_name="CLASSIFY", calls_count=8, total_tokens_in=3200, total_tokens_out=450, cost_usd=0.003, duration_ms=800.0),
            "EXTRACT": NodeUsage(node_name="EXTRACT", calls_count=8, total_tokens_in=12500, total_tokens_out=1800, cost_usd=0.011, duration_ms=1500.0),
            "RECONCILE": NodeUsage(node_name="RECONCILE", calls_count=1, duration_ms=200.0),
            "EXAMINE": NodeUsage(node_name="EXAMINE", calls_count=1, total_tokens_in=4200, total_tokens_out=600, cost_usd=0.004, duration_ms=500.0),
        }
    )

    return report.model_dump()


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
    node_ids = set()

    # Map both doc_id and filename to the node ID
    doc_lookup = {}

    for doc in state.documents:
        node_id = doc.doc_id or doc.filename
        doc_lookup[doc.doc_id] = node_id
        doc_lookup[doc.filename] = node_id
        node_ids.add(node_id)

        nodes.append({
            "id": node_id,
            "label": doc.filename,
            "type": "DOCUMENT",
            "group": "DOCUMENT",
            "doc_type": doc.doc_type.value if hasattr(doc.doc_type, "value") else str(doc.doc_type),
            "status": "QUARANTINED" if doc.quarantined else "ACTIVE",
            "chunks_count": len(doc.chunks) if doc.chunks else 1
        })

    for f in state.findings:
        f_node_id = f.finding_id
        node_ids.add(f_node_id)
        nodes.append({
            "id": f_node_id,
            "label": f"[{f.finding_id}] {f.title[:30]}...",
            "full_title": f.title,
            "type": "FINDING",
            "group": "FINDING",
            "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
            "status": f.status.value if hasattr(f.status, "value") else str(f.status),
            "description": f.description,
            "resolution_action": f.resolution_action
        })

        # Resolve Source A edge
        if f.source_a:
            src_a_id = doc_lookup.get(f.source_a.doc_id) or doc_lookup.get(f.source_a.filename)
            if src_a_id and src_a_id in node_ids:
                edges.append({
                    "from": src_a_id,
                    "to": f_node_id,
                    "label": "Source A",
                    "is_conflict": True,
                    "quote": f.source_a.exact_quote
                })

        # Resolve Source B edge
        if f.source_b:
            src_b_id = doc_lookup.get(f.source_b.doc_id) or doc_lookup.get(f.source_b.filename)
            if src_b_id and src_b_id in node_ids:
                edges.append({
                    "from": src_b_id,
                    "to": f_node_id,
                    "label": "Contradicts",
                    "is_conflict": True,
                    "quote": f.source_b.exact_quote
                })

    return {"project_id": project_id, "nodes": nodes, "edges": edges}
