"""Test process checkpointing and resume capabilities (Behavior #2)."""

import os
from src.models.database import save_checkpoint, load_latest_checkpoint
from src.graph.state import PipelineState
from src.graph.workflow import run_pipeline


def test_checkpoint_persistence_and_resume():
    """Test saving checkpoint to SQLite database and reloading state."""
    project_id = "test_proj_checkpoint_001"
    
    # Run initial pipeline
    folder = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
    state = run_pipeline(doc_folder=folder, project_id=project_id, run_id="chk_run_1")

    # Load latest checkpoint from DB
    loaded = load_latest_checkpoint(project_id)
    assert loaded is not None, "Failed to load checkpoint from database!"
    assert loaded["current_node"] == "GATE"
    assert loaded["status"] == "AWAITING_HUMAN_GATE"
    assert len(loaded["pending_findings"]) == 5

    # Simulate process death & restart: restore PipelineState from loaded checkpoint
    restored_state = PipelineState(
        project_id=project_id,
        current_node=loaded["current_node"],
        status=loaded["status"],
        findings=state.findings,
        pending_findings=state.pending_findings,
        documents=state.documents,
        facts=state.facts,
        register=state.register
    )

    assert len(restored_state.documents) == 8
    assert len(restored_state.facts) >= 15
    assert len(restored_state.findings) == 5
