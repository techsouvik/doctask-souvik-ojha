"""Comprehensive test suite for Scalability, Multi-Tenancy Isolation, and In-Flight Crash Recovery."""

import os
import time
import asyncio
import pytest
from src.app.project_service import ProjectService
from src.models.database import save_checkpoint, load_latest_checkpoint, save_cached_facts_db, load_cached_facts_db
from src.models.domain import DocumentMetadata, DocumentType, ExtractedFact, SourceCitation, FindingStatus
from src.extraction.extractor import extract_facts
from src.graph.workflow import run_pipeline


def test_per_document_atomic_cache_and_resume():
    """Test that extracted facts are saved atomically per-document and reused on resume."""
    tenant_id = "tenant_test_scaling"
    project_id = "proj_test_cache_resume"
    doc_id = "doc_contract_001"
    checksum = f"sha256_mock_hash_{time.time()}"

    # 1. Verify initially no cached facts
    cached = load_cached_facts_db(project_id, checksum, tenant_id=tenant_id)
    assert cached is None

    # 2. Save facts for document
    mock_facts = [
        {
            "fact_id": "f001",
            "project_id": project_id,
            "doc_id": doc_id,
            "entity_type": "CONTRACT_VALUE",
            "entity_key": "project:value",
            "attribute": "value",
            "raw_value": "Rs 10 cr",
            "normalized_value": 100000000.0,
            "unit": "INR",
            "grounded": True,
            "citation": {
                "doc_id": doc_id,
                "filename": "contract.docx",
                "location": "Sec 1",
                "exact_quote": "Rs 10 cr"
            }
        }
    ]
    save_cached_facts_db(project_id, doc_id, checksum, mock_facts, tenant_id=tenant_id)

    # 3. Verify retrieved accurately in 0ms without re-extraction
    retrieved = load_cached_facts_db(project_id, checksum, tenant_id=tenant_id)
    assert retrieved is not None
    assert len(retrieved) == 1
    assert retrieved[0]["entity_key"] == "project:value"
    assert retrieved[0]["normalized_value"] == 100000000.0


def test_in_flight_crash_resumption_preserves_finished_work():
    """Test that a run stopped midway resumes from its latest checkpoint without losing finished work."""
    corpus = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
    project_id = ProjectService.create_project("Test Crash Workspace", doc_folder=corpus)
    
    # 1. Run pipeline and let it pause at GATE
    state = ProjectService.run_pipeline_for_project(project_id)
    assert state.status == "AWAITING_HUMAN_GATE"
    assert len(state.documents) == 8
    assert len(state.facts) >= 15
    assert len(state.findings) == 5

    # 2. Simulate process kill by clearing in-memory cache
    from src.app.project_service import _ACTIVE_STATES
    _ACTIVE_STATES.pop(project_id, None)

    # 3. Check DB checkpoint is restored correctly
    restored_state = ProjectService.get_project_state(project_id)
    assert restored_state.project_id == project_id
    assert restored_state.status == "AWAITING_HUMAN_GATE"
    assert len(restored_state.documents) == 8
    assert len(restored_state.facts) >= 15
    assert len(restored_state.findings) == 5


def test_multi_tenant_isolation():
    """Test that Tenant A and Tenant B data never collide."""
    tenant_a = "tenant_alpha"
    tenant_b = "tenant_beta"
    proj_a = ProjectService.create_project("Alpha Workspace", tenant_id=tenant_a)
    proj_b = ProjectService.create_project("Beta Workspace", tenant_id=tenant_b)

    # Checkpoint for Tenant A
    save_checkpoint(proj_a, "EXTRACT", {"status": "TENANT_A_DATA"}, tenant_id=tenant_a)
    # Checkpoint for Tenant B
    save_checkpoint(proj_b, "EXTRACT", {"status": "TENANT_B_DATA"}, tenant_id=tenant_b)

    cp_a = load_latest_checkpoint(proj_a, tenant_id=tenant_a)
    cp_b = load_latest_checkpoint(proj_b, tenant_id=tenant_b)

    assert cp_a["status"] == "TENANT_A_DATA"
    assert cp_b["status"] == "TENANT_B_DATA"


@pytest.mark.asyncio
async def test_concurrent_distributed_locks():
    """Test that distributed locks handle concurrent triggers without corruption."""
    corpus = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
    project_id = ProjectService.create_project("Lock Concurrency Workspace", doc_folder=corpus)
    
    def trigger_run():
        return ProjectService.run_pipeline_for_project(project_id)

    loop = asyncio.get_event_loop()
    # Run 4 parallel triggers at the exact same instant
    tasks = [loop.run_in_executor(None, trigger_run) for _ in range(4)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 4
    for r in results:
        assert r.status in ["AWAITING_HUMAN_GATE", "COMPLETED"]
        assert len(r.documents) == 8
