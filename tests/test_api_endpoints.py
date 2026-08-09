"""Comprehensive End-to-End API Router Test Suite."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)
PROJECT_ID = "proj_api_suite_test"


def test_health_endpoint():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


def test_full_api_surface_workflow():
    # 1. Create Project
    res = client.post("/api/v1/projects", json={"project_name": "API Suite Test"})
    assert res.status_code == 200
    assert res.json()["project_id"] == PROJECT_ID

    # 2. Trigger Run
    res_run = client.post(f"/api/v1/projects/{PROJECT_ID}/run")
    assert res_run.status_code == 200
    assert res_run.json()["status"] == "AWAITING_HUMAN_GATE"
    assert res_run.json()["pending_findings_count"] == 5

    # 3. List Documents
    res_docs = client.get(f"/api/v1/projects/{PROJECT_ID}/documents")
    assert res_docs.status_code == 200
    assert len(res_docs.json()["documents"]) == 8

    # 4. List Findings with Resolution Actions
    res_findings = client.get(f"/api/v1/projects/{PROJECT_ID}/findings")
    assert res_findings.status_code == 200
    findings = res_findings.json()["findings"]
    assert len(findings) == 5
    assert "resolution_action" in findings[0]
    assert findings[0]["resolution_action"] is not None

    # 5. Timeline API
    res_timeline = client.get(f"/api/v1/projects/{PROJECT_ID}/timeline")
    assert res_timeline.status_code == 200
    assert len(res_timeline.json()["timeline_events"]) == 8

    # 6. Analytics API
    res_analytics = client.get(f"/api/v1/projects/{PROJECT_ID}/analytics")
    assert res_analytics.status_code == 200
    assert res_analytics.json()["total_cost_usd"] > 0

    # 7. Hybrid Search
    res_search = client.post(f"/api/v1/projects/{PROJECT_ID}/search", json={"query": "penalty clause liquidated damages", "top_k": 3})
    assert res_search.status_code == 200
    assert len(res_search.json()["results"]) == 3

    # 8. Session Message & Tree
    res_msg = client.post(f"/api/v1/projects/{PROJECT_ID}/sessions/tree_001/messages", json={"content": "Analyze the penalty terms in contract"})
    assert res_msg.status_code == 200
    assert "user_node" in res_msg.json()

    user_node_id = res_msg.json()["user_node"]["id"]

    # 9. Session Branching
    res_branch = client.post(f"/api/v1/projects/{PROJECT_ID}/sessions/tree_001/branch", json={"parent_node_id": user_node_id, "content": "Branching into milestone billing analysis"})
    assert res_branch.status_code == 200
    assert res_branch.json()["branched_from_node_id"] == user_node_id

    # 10. Batch Approve Findings at GATE
    res_approve = client.post(f"/api/v1/projects/{PROJECT_ID}/findings/batch-approve", json={"approved_all": True})
    assert res_approve.status_code == 200
    assert res_approve.json()["status"] == "COMPLETED"

    # 11. Get Register
    res_reg = client.get(f"/api/v1/projects/{PROJECT_ID}/register")
    assert res_reg.status_code == 200
    assert len(res_reg.json()["entries"]) >= 15

    # 12. Create Artifact
    res_art = client.post(f"/api/v1/projects/{PROJECT_ID}/artifacts", json={"title": "Audit Summary", "content": "# Audit Report\nAll findings approved."})
    assert res_art.status_code == 200
    assert "artifact_id" in res_art.json()

    # 13. Export HTML Executive Report
    res_report = client.get(f"/api/v1/projects/{PROJECT_ID}/export-report")
    assert res_report.status_code == 200
    assert "DocuMesh Executive Reconciliation Report" in res_report.text
