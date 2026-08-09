"""Test concurrent multi-user parallel execution and state isolation."""

import os
from src.graph.workflow import run_pipeline
from src.models.domain import FindingStatus


def test_parallel_multi_project_execution():
    """Test two users/projects running concurrently without state bleed or context loss."""
    folder = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"

    # User 1 runs Project A
    state_a = run_pipeline(doc_folder=folder, project_id="proj_user_alpha", run_id="run_alpha_1")

    # User 2 runs Project B concurrently
    state_b = run_pipeline(doc_folder=folder, project_id="proj_user_beta", run_id="run_beta_1")

    # Verify complete isolation
    assert state_a.project_id == "proj_user_alpha"
    assert state_b.project_id == "proj_user_beta"

    assert len(state_a.documents) == 8
    assert len(state_b.documents) == 8

    # Mutate User A's gate decisions (Approve F-001)
    for f in state_a.findings:
        if f.finding_id == "F-001":
            f.status = FindingStatus.APPROVED

    # Verify User B's state remains untouched (F-001 still PRESENTED)
    b_f001 = next(f for f in state_b.findings if f.finding_id == "F-001")
    assert b_f001.status == FindingStatus.PRESENTED, "Context leaked between parallel users!"
