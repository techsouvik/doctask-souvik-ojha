"""LangGraph node handlers for DocuMesh state machine with persistent DB checkpointing & Redis caching."""

import os
import time
import hashlib
from typing import Dict, Any
from src.graph.state import PipelineState
from src.ingestion.pipeline import ingest_file
from src.classification.classifier import classify_document
from src.extraction.extractor import extract_facts
from src.reconciliation.resolver import reconcile_facts
from src.examination.engine import run_examination_pipeline
from src.models.domain import FindingStatus, Finding, ExtractedFact
from src.models.database import save_checkpoint, save_cached_facts_db, load_cached_facts_db
from src.cache.redis_cache import cache_instance
from src.logging_config import get_logger

logger = get_logger("documesh.graph.nodes")


def node_ingest(state: PipelineState) -> Dict[str, Any]:
    """1. INGEST NODE: Scan directory recursively, SHA-256 dedup, parse DOCX/PDF/TXT, chunk."""
    logger.info("node_start", node="INGEST", project_id=state.project_id, doc_folder=state.doc_folder)

    if state.documents:
        documents = state.documents
    else:
        documents = []
        doc_dir = state.doc_folder or "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"

        if os.path.exists(doc_dir):
            for root, _, files in os.walk(doc_dir):
                for fname in sorted(files):
                    if fname.startswith(".") or not fname.lower().endswith((".docx", ".pdf", ".txt")):
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        doc = ingest_file(fpath, state.project_id)
                        if doc:
                            documents.append(doc)
                    except Exception as e:
                        logger.error("ingest_doc_failed_quarantined", file=fname, error=str(e))

    logger.info("ingest_completed", total_docs=len(documents))
    state.current_node = "INGEST"
    save_checkpoint(state.project_id, "INGEST", state.model_dump())
    return {
        "documents": documents,
        "current_node": "INGEST",
        "status": "IN_PROGRESS"
    }


def node_classify(state: PipelineState) -> Dict[str, Any]:
    """2. CLASSIFY NODE: Hybrid classification & prompt injection quarantine scanner."""
    logger.info("node_start", node="CLASSIFY", project_id=state.project_id)
    classified_docs = []

    for doc in state.documents:
        try:
            updated_doc = classify_document(doc)
            classified_docs.append(updated_doc)
        except Exception as e:
            logger.error("classify_doc_failed_quarantined", doc_id=doc.doc_id, error=str(e))
            doc.quarantined = True
            doc.quarantine_reason = f"Classification exception: {str(e)}"
            classified_docs.append(doc)

    state.current_node = "CLASSIFY"
    save_checkpoint(state.project_id, "CLASSIFY", state.model_dump())
    return {
        "documents": classified_docs,
        "current_node": "CLASSIFY",
        "status": "IN_PROGRESS"
    }


def node_extract(state: PipelineState) -> Dict[str, Any]:
    """3. EXTRACT NODE: Multi-tiered cached extraction with crash-proof fault tolerance."""
    logger.info("node_start", node="EXTRACT", project_id=state.project_id)
    all_facts = []

    for doc in state.documents:
        if doc.quarantined:
            continue

        # 1. Check Redis Cache
        cached_facts = cache_instance.get_cached_fact(doc.checksum)
        
        # 2. Check Persistent DB Cache
        if not cached_facts:
            cached_facts = load_cached_facts_db(state.project_id, doc.checksum)

        if cached_facts:
            logger.info("facts_cache_hit", filename=doc.filename, fact_count=len(cached_facts))
            facts = [ExtractedFact(**f) if isinstance(f, dict) else f for f in cached_facts]
        else:
            try:
                facts = extract_facts(doc)
                facts_dump = [f.model_dump() for f in facts]
                # Save to both Redis and DB
                cache_instance.set_cached_fact(doc.checksum, facts_dump)
                save_cached_facts_db(state.project_id, doc.doc_id, doc.checksum, facts_dump)
            except Exception as e:
                logger.error("extract_doc_failed_quarantined", doc_id=doc.doc_id, error=str(e))
                doc.quarantined = True
                doc.quarantine_reason = f"Extraction failure: {str(e)}"
                continue

        all_facts.extend(facts)

    state.current_node = "EXTRACT"
    save_checkpoint(state.project_id, "EXTRACT", state.model_dump())
    return {
        "facts": all_facts,
        "current_node": "EXTRACT",
        "status": "IN_PROGRESS"
    }


def node_reconcile(state: PipelineState) -> Dict[str, Any]:
    """4. RECONCILE NODE: Group facts by entity_key, resolve canonical register."""
    logger.info("node_start", node="RECONCILE", project_id=state.project_id)
    register = reconcile_facts(state.project_id, "Greenfield Tech Park - Phase 1", state.facts)

    state.current_node = "RECONCILE"
    save_checkpoint(state.project_id, "RECONCILE", state.model_dump())
    return {
        "register": register,
        "current_node": "RECONCILE",
        "status": "IN_PROGRESS"
    }


def node_examine(state: PipelineState) -> Dict[str, Any]:
    """5. EXAMINE NODE: Run 3-stage rule examination engine + user skills."""
    logger.info("node_start", node="EXAMINE", project_id=state.project_id)

    # Run examination engine on facts and documents
    new_findings = run_examination_pipeline(state.facts, state.documents)

    # Preserve any existing findings that were already decided
    existing_decisions = {f.finding_id: f for f in state.findings if f.status != FindingStatus.PRESENTED}
    final_findings = []

    for f in new_findings:
        if f.finding_id in existing_decisions:
            final_findings.append(existing_decisions[f.finding_id])
        else:
            final_findings.append(f)

    pending = [f for f in final_findings if f.status == FindingStatus.PRESENTED]

    state.current_node = "EXAMINE"
    save_checkpoint(state.project_id, "EXAMINE", state.model_dump())
    return {
        "findings": final_findings,
        "pending_findings": pending,
        "current_node": "EXAMINE",
        "status": "IN_PROGRESS"
    }


def node_gate(state: PipelineState) -> Dict[str, Any]:
    """6. GATE NODE: Human / MCP Gate approval pause."""
    logger.info("node_start", node="GATE", project_id=state.project_id)

    pending = [f for f in state.findings if f.status == FindingStatus.PRESENTED]

    state.current_node = "GATE"
    if pending:
        logger.info("gate_paused_awaiting_decisions", pending_count=len(pending))
        state.status = "AWAITING_HUMAN_GATE"
        save_checkpoint(state.project_id, "GATE", state.model_dump())
        return {
            "pending_findings": pending,
            "current_node": "GATE",
            "status": "AWAITING_HUMAN_GATE"
        }

    state.status = "GATE_APPROVED"
    save_checkpoint(state.project_id, "GATE", state.model_dump())
    return {
        "pending_findings": [],
        "current_node": "GATE",
        "status": "GATE_APPROVED"
    }


def node_deliver(state: PipelineState) -> Dict[str, Any]:
    """7. DELIVER NODE: Compile final reconciled Project Register deliverable."""
    logger.info("node_start", node="DELIVER", project_id=state.project_id)

    approved_findings = [f for f in state.findings if f.status == FindingStatus.APPROVED]

    if state.register:
        state.register.approved_findings = approved_findings
        state.register.active_conflicts_count = len(approved_findings)

    state.current_node = "DELIVER"
    state.status = "COMPLETED"
    save_checkpoint(state.project_id, "DELIVER", state.model_dump())
    return {
        "register": state.register,
        "current_node": "DELIVER",
        "status": "COMPLETED"
    }
