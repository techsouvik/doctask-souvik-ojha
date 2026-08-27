"""Test suite for DocuMesh MCP Server and Machine Client (Behavior #4: A machine can drive it)."""

import pytest
from src.mcp.client import DocuMeshMachineClient
from src.mcp.server import (
    run_documesh_analysis,
    get_documesh_status,
    list_documesh_findings,
    approve_documesh_finding,
    get_documesh_register
)


def test_machine_client_end_to_end_flow():
    """Test that DocuMeshMachineClient can drive the full audit flow programmatically."""
    client = DocuMeshMachineClient(tenant_id="tenant_auto_machine")
    corpus = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
    project_id = client.create_project("Machine Driven Audit", doc_folder=corpus)

    # 1. Trigger Audit
    run_res = client.run_audit(project_id)
    assert run_res["status"] == "AWAITING_HUMAN_GATE"
    assert run_res["documents_count"] == 8
    assert run_res["findings_count"] == 5

    # 2. Check Status
    status = client.get_status(project_id)
    assert status["status"] == "AWAITING_HUMAN_GATE"
    assert status["pending_findings_count"] == 5

    # 3. List Findings
    findings = client.list_findings(project_id)
    assert len(findings) == 5
    finding_0 = findings[0]
    assert "finding_id" in finding_0

    # 4. Item-by-Item Gate Decision via Machine Client
    dec_res = client.approve_finding(project_id, finding_0["finding_id"], approved=True, feedback="Approved by automated agent")
    assert dec_res["new_status"] == "APPROVED"
    assert dec_res["remaining_pending"] == 4

    # 5. Batch Approve Remaining
    batch_res = client.batch_approve_all(project_id, approved_all=True)
    assert batch_res["status"] == "COMPLETED"
    assert batch_res["register_generated"] is True

    # 6. Retrieve Register
    register = client.get_register(project_id)
    assert "entries" in register
    assert len(register["entries"]) >= 15

    # 7. Export Executive Report HTML
    report_html = client.export_report_html(project_id)
    assert "DocuMesh Executive Reconciliation Report" in report_html


def test_mcp_server_tools_direct_invocation():
    """Test that MCP server tools can be called directly by an external MCP client/agent."""
    project_id = "proj_mcp_direct_test"
    corpus = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"

    # 1. Run analysis tool
    analysis_raw = run_documesh_analysis(project_id=project_id, doc_folder=corpus)
    assert "AWAITING_HUMAN_GATE" in analysis_raw

    # 2. Status tool
    status_raw = get_documesh_status(project_id=project_id)
    assert "pending_findings_count" in status_raw

    # 3. List findings tool
    findings_raw = list_documesh_findings(project_id=project_id)
    assert "F001" in findings_raw or "finding_id" in findings_raw
