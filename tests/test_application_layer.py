"""Unit tests for Application Layer Services (ProjectService, FindingService, RegisterService)."""

import pytest
from src.app.project_service import ProjectService
from src.app.finding_service import FindingService
from src.app.register_service import RegisterService
from src.config import settings


def test_application_layer_services():
    project_name = "Application Layer Test"
    project_id = ProjectService.create_project(project_name, doc_folder=settings.seed_corpus_dir)

    assert project_id == "proj_application_layer_test"

    # Trigger run
    state = ProjectService.run_pipeline_for_project(project_id)
    assert state.status == "AWAITING_HUMAN_GATE"
    assert len(state.pending_findings) > 0

    # Batch decide findings via service
    batch_res = FindingService.batch_decide_findings(project_id, approved_all=True)
    assert batch_res["status"] == "COMPLETED"

    # Get register via service
    register = RegisterService.get_reconciled_register(project_id)
    assert register is not None
    assert len(register.entries) > 0
