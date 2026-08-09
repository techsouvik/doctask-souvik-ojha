"""LangGraph node handlers for DocuMesh state machine with persistent DB checkpointing & Redis caching."""

import os
import time
import hashlib
from typing import Dict, Any
from src.graph.state import PipelineState
from src.ingestion.pipeline import ingest_file
from src.classification.classifier import classify_document
from src.extraction.extractor import extract_facts
from src.reconciliation.resolver import resolve_entity_history
from src.examination.engine import run_examination_pipeline
from src.models.domain import ProjectRegister, FindingStatus
from src.models.database import save_checkpoint
from src.cache.redis_cache import cache_instance
from src.logging_config import get_logger

logger = get_logger("documesh.pipeline")


def node_ingest(state: PipelineState) -> Dict[str, Any]:
    """1. INGEST NODE: Recursively scan doc_folder and ingest all files."""
    folder = state.doc_folder
    logger.info("node_start", node="INGEST", doc_folder=folder, project_id=state.project_id)

    ingested_docs = list(state.documents)
    existing_checksums = [d.checksum for d in ingested_docs]

    for root, _, files in os.walk(folder):
        for fname in sorted(files):
            if fname.startswith(".") or fname.endswith(".md") or fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            doc = ingest_file(fpath, state.project_id, existing_checksums)
            if doc:
                ingested_docs.append(doc)
                existing_checksums.append(doc.checksum)
                logger.info("file_ingested", filename=fname, format=doc.format, chunks=len(doc.chunks))

    logger.info("ingest_completed", total_docs=len(ingested_docs))

    res = {
        "documents": [d.model_dump() for d in ingested_docs],
        "current_node": "INGEST",
        "status": "IN_PROGRESS"
    }
    save_checkpoint(state.project_id, "INGEST", res)
    return res


def node_classify(state: PipelineState) -> Dict[str, Any]:
    """2. CLASSIFY NODE: Classify documents & run prompt injection quarantine check."""
    logger.info("node_start", node="CLASSIFY", project_id=state.project_id)
    classified_docs = []

    for doc in state.documents:
        updated_doc = classify_document(doc)
        classified_docs.append(updated_doc)
        if updated_doc.quarantined:
            logger.warning("document_quarantined", filename=updated_doc.filename, reason=updated_doc.quarantine_reason)
        else:
            logger.info("document_classified", filename=updated_doc.filename, doc_type=updated_doc.doc_type.value, confidence=updated_doc.classification_confidence)

    res = {
        "documents": [d.model_dump() for d in classified_docs],
        "current_node": "CLASSIFY",
        "status": "IN_PROGRESS"
    }
    save_checkpoint(state.project_id, "CLASSIFY", res)
    return res


def node_extract(state: PipelineState) -> Dict[str, Any]:
    """3. EXTRACT NODE: Extract facts from non-quarantined documents with caching."""
    logger.info("node_start", node="EXTRACT", project_id=state.project_id)
    all_facts = []

    for doc in state.documents:
        if doc.quarantined:
            logger.warning("skipping_quarantined_doc", filename=doc.filename)
            continue

        cache_key = f"facts:{doc.checksum}"
        cached_facts = cache_instance.get(cache_key)

        if cached_facts:
            logger.info("facts_cache_hit", filename=doc.filename, fact_count=len(cached_facts))
            facts = cached_facts
        else:
            facts = extract_facts(doc)
            cache_instance.set(cache_key, [f.model_dump() for f in facts], ttl_seconds=3600)
            logger.info("facts_extracted", filename=doc.filename, fact_count=len(facts))

        all_facts.extend(facts)

    res = {
        "facts": [f if isinstance(f, dict) else f.model_dump() for f in all_facts],
        "current_node": "EXTRACT",
        "status": "IN_PROGRESS"
    }
    save_checkpoint(state.project_id, "EXTRACT", res)
    return res


def node_reconcile(state: PipelineState) -> Dict[str, Any]:
    """4. RECONCILE NODE: Resolve facts into entity histories and draft register."""
    logger.info("node_start", node="RECONCILE", project_id=state.project_id)
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

    logger.info("reconciliation_complete", entity_keys_resolved=len(entries), content_hash=reg_hash)

    res = {
        "register": register.model_dump(),
        "current_node": "RECONCILE",
        "status": "IN_PROGRESS"
    }
    save_checkpoint(state.project_id, "RECONCILE", res)
    return res


def node_examine(state: PipelineState) -> Dict[str, Any]:
    """5. EXAMINE NODE: Run 3-stage rule examination engine & conflict detector."""
    logger.info("node_start", node="EXAMINE", project_id=state.project_id)
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
    logger.info("examination_complete", total_findings=len(findings), pending_approval=len(pending))

    res = {
        "findings": [f.model_dump() for f in findings],
        "pending_findings": [f.model_dump() for f in pending],
        "current_node": "EXAMINE",
        "status": "AWAITING_HUMAN_GATE" if pending else "IN_PROGRESS"
    }
    save_checkpoint(state.project_id, "EXAMINE", res)
    return res


def node_gate(state: PipelineState) -> Dict[str, Any]:
    """6. GATE NODE: Human-in-the-loop / MCP approval gate."""
    logger.info("node_start", node="GATE", project_id=state.project_id)
    pending = [f for f in state.findings if f.status == FindingStatus.PRESENTED]

    if pending:
        logger.info("gate_paused_awaiting_decisions", pending_count=len(pending))
        res = {
            "pending_findings": [f.model_dump() for f in pending],
            "current_node": "GATE",
            "status": "AWAITING_HUMAN_GATE"
        }
        save_checkpoint(state.project_id, "GATE", res)
        return res

    logger.info("gate_cleared_all_findings_resolved")
    res = {
        "pending_findings": [],
        "current_node": "GATE",
        "status": "IN_PROGRESS"
    }
    save_checkpoint(state.project_id, "GATE", res)
    return res


def node_deliver(state: PipelineState) -> Dict[str, Any]:
    """7. DELIVER NODE: Produce final Project Register deliverable."""
    logger.info("node_start", node="DELIVER", project_id=state.project_id)
    approved = [f for f in state.findings if f.status == FindingStatus.APPROVED]

    if state.register:
        state.register.approved_findings = approved
        state.register.active_conflicts_count = len(approved)

    logger.info("deliverable_ready", approved_findings_count=len(approved))
    res = {
        "register": state.register.model_dump() if state.register else None,
        "current_node": "DELIVER",
        "status": "COMPLETED"
    }
    save_checkpoint(state.project_id, "DELIVER", res)
    return res
