"""Unit tests for Backend Application Layer Services."""

import pytest
from src.app.project_service import ProjectService
from src.app.finding_service import FindingService
from src.app.register_service import RegisterService


def test_application_layer_services():
    project_name = "Application Layer Test"
    project_id = ProjectService.create_project(project_name)

    assert project_id == "proj_application_layer_test"

    # Trigger run
    state = ProjectService.run_pipeline_for_project(project_id)
    assert state.status == "AWAITING_HUMAN_GATE"
    assert len(state.pending_findings) == 5

    # Retrieve findings via FindingService
    findings = FindingService.get_findings(project_id)
    assert len(findings) == 5

    # Approve F-001
    res1 = FindingService.decide_finding(project_id, "F-001", approved=True, feedback="Verified by site engineer")
    assert res1["new_status"] == "APPROVED"
    assert res1["remaining_pending"] == 4

    # Batch approve remaining
    res2 = FindingService.batch_decide_findings(project_id, approved_all=True)
    assert res2["status"] == "COMPLETED"

    # Get Register & HTML Report
    reg = RegisterService.get_register(project_id)
    assert reg.version == 1
    assert len(reg.entries) >= 15

    html = RegisterService.generate_executive_report_html(project_id)
    assert "DocuMesh Executive Reconciliation Report" in html
    assert "Greenfield Tech Park" in html
