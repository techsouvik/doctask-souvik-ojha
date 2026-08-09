"""LangGraph node handlers for DocuMesh state machine."""

import os
import time
import hashlib
from typing import Dict, Any, List
from src.graph.state import PipelineState
from src.ingestion.pipeline import ingest_file
from src.classification.classifier import classify_document
from src.extraction.extractor import extract_facts
from src.reconciliation.resolver import resolve_entity_history
from src.examination.engine import run_examination_pipeline
from src.models.domain import ProjectRegister, FindingStatus


def node_ingest(state: PipelineState) -> Dict[str, Any]:
    """1. INGEST NODE: Recursively scan doc_folder and ingest all files."""
    start_t = time.time()
    folder = state.doc_folder
    ingested_docs = list(state.documents)
    existing_checksums = [d.checksum for d in ingested_docs]

    print(f"\n[NODE 1: INGEST] Scanning folder: {folder}")

    for root, _, files in os.walk(folder):
        for fname in sorted(files):
            if fname.startswith(".") or fname.endswith(".md") or fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            doc = ingest_file(fpath, state.project_id, existing_checksums)
            if doc:
                ingested_docs.append(doc)
                existing_checksums.append(doc.checksum)
                print(f"  ✓ Ingested: {fname} ({doc.format.upper()}, {len(doc.chunks)} chunks)")

    print(f"  Total documents in session: {len(ingested_docs)}")

    return {
        "documents": [d.model_dump() for d in ingested_docs],
        "current_node": "INGEST",
        "status": "IN_PROGRESS"
    }


def node_classify(state: PipelineState) -> Dict[str, Any]:
    """2. CLASSIFY NODE: Classify documents & run prompt injection quarantine check."""
    classified_docs = []

    print("\n[NODE 2: CLASSIFY] Classifying document types & security check...")
    for doc in state.documents:
        updated_doc = classify_document(doc)
        classified_docs.append(updated_doc)
        status_symbol = "🚨 QUARANTINED" if updated_doc.quarantined else f"✓ {updated_doc.doc_type.value}"
        print(f"  {updated_doc.filename} -> {status_symbol} (conf: {updated_doc.classification_confidence:.2f})")

    return {
        "documents": [d.model_dump() for d in classified_docs],
        "current_node": "CLASSIFY",
        "status": "IN_PROGRESS"
    }


def node_extract(state: PipelineState) -> Dict[str, Any]:
    """3. EXTRACT NODE: Extract facts from non-quarantined documents."""
    all_facts = []

    print("\n[NODE 3: EXTRACT] Extracting structured facts with grounding citations...")
    for doc in state.documents:
        if doc.quarantined:
            print(f"  ⚠️ Skipping extraction for quarantined document: {doc.filename}")
            continue

        facts = extract_facts(doc)
        all_facts.extend(facts)
        print(f"  ✓ Extracted {len(facts)} grounded facts from {doc.filename}")

    return {
        "facts": [f.model_dump() for f in all_facts],
        "current_node": "EXTRACT",
        "status": "IN_PROGRESS"
    }


def node_reconcile(state: PipelineState) -> Dict[str, Any]:
    """4. RECONCILE NODE: Resolve facts into entity histories and draft register."""
    print("\n[NODE 4: RECONCILE] Grouping facts by canonical entity_key...")
    entries = resolve_entity_history(state.facts)

    reg_hash = hashlib.sha256(str([e.model_dump() for e in entries]).encode()).hexdigest()[:12]
    register = ProjectRegister(
        project_id=state.project_id,
        project_name="Greenfield Tech Park - Phase 1",
        version=1,
        content_hash=reg_hash,
        entries=entries,
        active_conflicts_count=0
    )

    print(f"  ✓ Resolved {len(entries)} entity keys across {len(state.facts)} facts. Register hash: {reg_hash}")

    return {
        "register": register.model_dump(),
        "current_node": "RECONCILE",
        "status": "IN_PROGRESS"
    }


def node_examine(state: PipelineState) -> Dict[str, Any]:
    """5. EXAMINE NODE: Run 3-stage rule examination engine & conflict detector."""
    print("\n[NODE 5: EXAMINE] Executing 3-stage compliance & contract rule checks...")
    findings = run_examination_pipeline(state.facts)

    # Preserve any existing human/MCP decisions for findings
    existing_map = {f.finding_id: f for f in state.findings}
    for f in findings:
        if f.finding_id in existing_map:
            prev = existing_map[f.finding_id]
            if prev.status != FindingStatus.PRESENTED:
                f.status = prev.status
                f.feedback = prev.feedback

    pending = [f for f in findings if f.status == FindingStatus.PRESENTED]
    print(f"  🚨 Detected {len(findings)} findings ({len(pending)} pending human approval)")

    for f in findings:
        status_str = f" [{f.status.value}]" if f.status != FindingStatus.PRESENTED else ""
        print(f"    - [{f.severity.value}] {f.finding_id}: {f.title}{status_str}")

    return {
        "findings": [f.model_dump() for f in findings],
        "pending_findings": [f.model_dump() for f in pending],
        "current_node": "EXAMINE",
        "status": "AWAITING_HUMAN_GATE" if pending else "IN_PROGRESS"
    }


def node_gate(state: PipelineState) -> Dict[str, Any]:
    """6. GATE NODE: Human-in-the-loop / MCP approval gate."""
    print("\n[NODE 6: GATE] Checking human/MCP approval decisions...")
    pending = [f for f in state.findings if f.status == FindingStatus.PRESENTED]

    if pending:
        print(f"  ⏸️ Pipeline paused at GATE: {len(pending)} findings awaiting human decision.")
        return {
            "pending_findings": [f.model_dump() for f in pending],
            "current_node": "GATE",
            "status": "AWAITING_HUMAN_GATE"
        }

    print("  ✓ All findings resolved by human/MCP. Proceeding to delivery.")
    return {
        "pending_findings": [],
        "current_node": "GATE",
        "status": "IN_PROGRESS"
    }


def node_deliver(state: PipelineState) -> Dict[str, Any]:
    """7. DELIVER NODE: Produce final Project Register deliverable."""
    print("\n[NODE 7: DELIVER] Finalizing Project Register deliverable...")
    approved = [f for f in state.findings if f.status == FindingStatus.APPROVED]

    if state.register:
        state.register.approved_findings = approved
        state.register.active_conflicts_count = len(approved)

    print(f"  ✅ DELIVERABLE READY: Reconciled Register + {len(approved)} approved findings.")
    return {
        "register": state.register.model_dump() if state.register else None,
        "current_node": "DELIVER",
        "status": "COMPLETED"
    }
