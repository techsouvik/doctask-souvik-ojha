"""Comprehensive Offline Test Suite for DocuMesh Engine (Behavior #7)."""

import os
import pytest
from src.graph.workflow import run_pipeline
from src.models.domain import FindingStatus


def test_full_pipeline_detects_all_planted_errors():
    """Test full pipeline execution on seed corpus without requiring an API key.
    
    Verifies that all 5 planted cross-document errors are detected.
    """
    folder = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
    assert os.path.exists(folder), "Seed corpus directory missing!"

    state = run_pipeline(doc_folder=folder, project_id="test_proj_offline", run_id="test_run_1")

    # 1. Check ingestion
    assert len(state.documents) == 8, f"Expected 8 documents, got {len(state.documents)}"

    # 2. Check classification
    doc_types = [d.doc_type.value for d in state.documents]
    assert "CONTRACT" in doc_types
    assert "STATUS_REPORT" in doc_types
    assert "INVOICE" in doc_types
    assert "MATERIAL_RECEIPT" in doc_types
    assert "CORRESPONDENCE" in doc_types

    # 3. Check fact extraction & grounding
    assert len(state.facts) >= 15, f"Expected >= 15 facts, got {len(state.facts)}"
    for f in state.facts:
        assert f.grounded, f"Fact {f.entity_key} failed grounding check!"

    # 4. Check findings (All 5 planted errors MUST be detected)
    finding_ids = [f.finding_id for f in state.findings]
    assert "F-001" in finding_ids, "Error 1 (Q1 arithmetic mismatch) not detected!"
    assert "F-002" in finding_ids, "Error 2 (Q1 excavation mismatch) not detected!"
    assert "F-003" in finding_ids, "Error 3 (Invoice progress mismatch) not detected!"
    assert "F-004" in finding_ids, "Error 4 (Client 15% penalty mismatch) not detected!"
    assert "F-005" in finding_ids, "Error 5 (Material receipt contradiction) not detected!"

    # 5. Check Gate Status
    assert state.status == "AWAITING_HUMAN_GATE"
    assert len(state.pending_findings) == 5


def test_human_gate_approval_flow():
    """Test resolving pending findings at the Human/MCP Gate."""
    folder = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
    state = run_pipeline(doc_folder=folder, project_id="test_proj_gate", run_id="test_run_gate")

    assert len(state.pending_findings) == 5

    # Simulate approving F-001 and F-003, rejecting F-002, F-004, F-005
    for f in state.findings:
        if f.finding_id in ["F-001", "F-003"]:
            f.status = FindingStatus.APPROVED
        else:
            f.status = FindingStatus.REJECTED

    # Re-run graph with gate cleared
    from src.graph.workflow import build_documesh_graph
    graph = build_documesh_graph()
    final_dict = graph.invoke(state)

    assert final_dict["status"] == "COMPLETED"
    assert final_dict["register"] is not None
    assert final_dict["register"]["active_conflicts_count"] == 2
