"""Structured Tools and Handlers for the DocuMesh AI Orchestrator Agent."""

import json
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool

from src.app.project_service import ProjectService
from src.app.finding_service import FindingService
from src.app.register_service import RegisterService
from src.graph.time_travel import TimeTravelEngine
from src.reconciliation.search import HybridSearchIndex
from src.tools.artifacts import AsyncArtifactsTools
from src.logging_config import get_logger

logger = get_logger("documesh.orchestrator.tools")


@tool
def run_reconciliation_audit(project_id: str) -> str:
    """Execute the 7-stage LangGraph reconciliation state machine across the project document pile.
    Ingests files, classifies types, extracts grounded facts, runs arithmetic/cross-document checks,
    and pauses at the Human Gate if discrepancies exist."""
    state = ProjectService.run_pipeline_for_project(project_id)
    findings = state.pending_findings if state.pending_findings else state.findings
    return json.dumps({
        "status": "success",
        "project_id": project_id,
        "pipeline_status": state.status,
        "current_node": state.current_node,
        "documents_count": len(state.documents),
        "facts_count": len(state.facts),
        "findings_count": len(findings),
        "pending_gate_findings": len(state.pending_findings),
        "findings": [
            {
                "finding_id": f.finding_id,
                "title": f.title,
                "severity": getattr(f.severity, "value", str(f.severity)),
                "status": getattr(f.status, "value", str(f.status)),
                "resolution_action": f.resolution_action
            }
            for f in findings
        ]
    })


@tool
def get_project_status(project_id: str) -> str:
    """Retrieve current workspace status, active state machine node, and pending gate counts."""
    state = ProjectService.get_project_state(project_id)
    return json.dumps({
        "project_id": project_id,
        "status": state.status,
        "current_node": state.current_node,
        "documents_count": len(state.documents),
        "facts_count": len(state.facts),
        "findings_count": len(state.findings),
        "pending_findings_count": len(state.pending_findings),
        "register_finalized": state.register is not None
    })


@tool
def search_document_chunks(project_id: str, query: str, top_k: int = 5) -> str:
    """Perform hybrid BM25 and semantic search across all indexed document chunks in the project
    workspace to retrieve verbatim quotes, sections, and citations."""
    state = ProjectService.get_project_state(project_id)
    index = HybridSearchIndex()
    all_chunks = []
    for doc in state.documents:
        all_chunks.extend(doc.chunks)
    index.add_chunks(all_chunks)

    hits = index.search(query, top_k=top_k)
    results = [
        {
            "doc_name": chunk.doc_name,
            "section": chunk.section_title or "Main Section",
            "page": chunk.page_num or 1,
            "score": round(score, 4),
            "text": chunk.text
        }
        for chunk, score in hits
    ]
    return json.dumps({"query": query, "match_count": len(results), "results": results})


@tool
def list_project_documents(project_id: str) -> str:
    """List all ingested documents in the project pile, their classified types, chunk counts,
    and quarantine status."""
    state = ProjectService.get_project_state(project_id)
    docs = [
        {
            "filename": d.filename,
            "doc_id": d.doc_id,
            "doc_type": getattr(d.doc_type, "value", str(d.doc_type)),
            "chunks_count": len(d.chunks),
            "quarantined": d.quarantined,
            "quarantine_reason": d.quarantine_reason
        }
        for d in state.documents
    ]
    return json.dumps({"project_id": project_id, "total_documents": len(docs), "documents": docs})


@tool
def get_discrepancy_findings(project_id: str, status: Optional[str] = None) -> str:
    """Retrieve all detected discrepancy findings and conflicts for the project, including
    severity, conflicting quotes from Source A and Source B, and proposed remediation actions."""
    findings = FindingService.get_findings(project_id, status)
    results = []
    for f in findings:
        results.append({
            "finding_id": f.finding_id,
            "title": f.title,
            "severity": getattr(f.severity, "value", str(f.severity)),
            "status": getattr(f.status, "value", str(f.status)),
            "description": f.description,
            "source_a": {
                "filename": f.source_a.filename if f.source_a else None,
                "location": f.source_a.location if f.source_a else None,
                "quote": f.source_a.exact_quote if f.source_a else None
            } if f.source_a else None,
            "source_b": {
                "filename": f.source_b.filename if f.source_b else None,
                "location": f.source_b.location if f.source_b else None,
                "quote": f.source_b.exact_quote if f.source_b else None
            } if f.source_b else None,
            "resolution_action": f.resolution_action,
            "reviewer_feedback": f.reviewer_feedback
        })
    return json.dumps({"project_id": project_id, "total_findings": len(results), "findings": results})


@tool
def decide_finding(project_id: str, finding_id: str, approved: bool, feedback: Optional[str] = None) -> str:
    """Approve or reject a specific discrepancy finding at the Human Gate with optional reviewer feedback notes."""
    try:
        res = FindingService.decide_finding(project_id, finding_id, approved, feedback)
        return json.dumps({
            "status": "success",
            "project_id": project_id,
            "finding_id": finding_id,
            "decision": "APPROVED" if approved else "REJECTED",
            "feedback": feedback,
            "remaining_pending_findings": res.get("pending_findings_count", 0),
            "pipeline_status": res.get("status")
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def batch_approve_all_findings(project_id: str) -> str:
    """Batch approve all pending discrepancy findings at the Human Gate to clear the gate and
    compile the final Reconciled Project Register."""
    try:
        res = FindingService.batch_decide_findings(project_id, approved_all=True)
        return json.dumps({
            "status": "success",
            "project_id": project_id,
            "message": "All pending findings approved. State machine transitioned to DELIVER.",
            "pipeline_status": res.get("status")
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def get_reconciled_register(project_id: str) -> str:
    """Retrieve the canonical Reconciled Project Register containing reconciled metric values,
    corroboration status, and source citations."""
    try:
        reg = RegisterService.get_register(project_id)
        entries = [
            {
                "entity_key": e.entity_key,
                "title": e.title,
                "reconciled_value": e.reconciled_value,
                "unit": e.unit,
                "status": e.status,
                "citation": f"{e.primary_citation.filename} ({e.primary_citation.location})" if e.primary_citation else None
            }
            for e in reg.entries
        ]
        return json.dumps({
            "project_id": project_id,
            "version": reg.version,
            "total_metrics": len(entries),
            "entries": entries
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def rewind_state_machine(project_id: str, target_node: str) -> str:
    """Rewind the LangGraph state machine back to a completed node checkpoint
    (INGEST, CLASSIFY, EXTRACT, RECONCILE, EXAMINE)."""
    try:
        rewound = TimeTravelEngine.rewind_to_node(project_id, target_node)
        return json.dumps({
            "status": "success",
            "project_id": project_id,
            "rewound_to_node": rewound.current_node,
            "pipeline_status": rewound.status
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
async def create_audit_artifact(project_id: str, title: str, content: str) -> str:
    """Create a versioned, content-hashed deliverable markdown artifact report for the project."""
    try:
        tools = AsyncArtifactsTools()
        art = await tools.create_artifact_async(project_id, title, content)
        return json.dumps({
            "status": "success",
            "artifact_id": art.artifact_id,
            "title": art.title,
            "content_hash": art.content_hash
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


ORCHESTRATOR_TOOLS = [
    run_reconciliation_audit,
    get_project_status,
    search_document_chunks,
    list_project_documents,
    get_discrepancy_findings,
    decide_finding,
    batch_approve_all_findings,
    get_reconciled_register,
    rewind_state_machine,
    create_audit_artifact
]

ORCHESTRATOR_TOOL_MAP = {t.name: t for t in ORCHESTRATOR_TOOLS}


async def execute_tool_call(tool_name: str, args: Dict[str, Any]) -> Any:
    """Execute a tool by name with arguments and return result."""
    tool_fn = ORCHESTRATOR_TOOL_MAP.get(tool_name)
    if not tool_fn:
        return json.dumps({"status": "error", "message": f"Tool '{tool_name}' not found."})

    try:
        if tool_name == "create_audit_artifact":
            return await tool_fn.ainvoke(args)
        else:
            return tool_fn.invoke(args)
    except Exception as e:
        logger.error("tool_execution_failed", tool=tool_name, error=str(e))
        return json.dumps({"status": "error", "message": str(e)})
