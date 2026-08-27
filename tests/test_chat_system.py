"""Unit tests for Chat Engine and Document-Aware Session Messaging."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)
PROJECT_ID = "proj_chat_test"
TREE_ID = "tree_chat_001"


def test_document_aware_chat_system():
    # 1. Create & Run Project
    client.post("/api/v1/projects", json={"project_name": "Chat Test"})
    client.post(f"/api/v1/projects/{PROJECT_ID}/run")

    # 2. Send Chat Message about Penalty Clause
    res = client.post(
        f"/api/v1/projects/{PROJECT_ID}/sessions/{TREE_ID}/messages",
        json={"content": "What is the penalty clause rate in the master project plan?"}
    )
    assert res.status_code == 200
    data = res.json()

    assert data["tree_id"] == TREE_ID
    assert "user_node" in data
    assert "assistant_node" in data
    assert "0.5%" in data["assistant_node"]["content"] or "liquidated damages" in data["assistant_node"]["content"] or "master_project_plan" in data["assistant_node"]["content"]

    # 3. List Sessions for Project
    res_list = client.get(f"/api/v1/projects/{PROJECT_ID}/sessions")
    assert res_list.status_code == 200
    sessions = res_list.json()["sessions"]
    assert len(sessions) == 1
    assert sessions[0]["tree_id"] == TREE_ID

    # 4. Rename Session
    res_rename = client.patch(
        f"/api/v1/projects/{PROJECT_ID}/sessions/{TREE_ID}",
        json={"title": "Master Plan Penalty Clause Discussion"}
    )
    assert res_rename.status_code == 200
    assert res_rename.json()["new_title"] == "Master Plan Penalty Clause Discussion"

    # 5. Delete Session
    res_del = client.delete(f"/api/v1/projects/{PROJECT_ID}/sessions/{TREE_ID}")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "deleted"


def test_sse_streaming_and_settings_endpoints():
    # 1. Test LLM Settings GET
    res_settings = client.get("/api/v1/settings/llm")
    assert res_settings.status_code == 200
    data = res_settings.json()
    assert "provider" in data
    assert "providers_available" in data

    # 2. Test LLM Settings Update
    res_update = client.post(
        "/api/v1/settings/llm",
        json={"provider": "openai_compatible", "model_name": "llama3.2", "base_url": "http://localhost:11434/v1"}
    )
    assert res_update.status_code == 200
    assert res_update.json()["status"] == "updated"

    # 3. Test SSE Stream via GET
    res_get_stream = client.get(
        "/api/v1/projects/proj_greenfield_tech_park/sessions/tree_sse_test/stream?q=What+is+the+penalty+clause?"
    )
    assert res_get_stream.status_code == 200
    assert "text/event-stream" in res_get_stream.headers["content-type"]
    assert "data: " in res_get_stream.text

    # 4. Test SSE Stream via POST
    res_post_stream = client.post(
        "/api/v1/projects/proj_greenfield_tech_park/sessions/tree_sse_test/stream",
        json={"content": "What is the penalty clause?"}
    )
    assert res_post_stream.status_code == 200
    assert "text/event-stream" in res_post_stream.headers["content-type"]
    assert "data: " in res_post_stream.text


def test_orchestrator_agent_actions():
    orch_proj = "proj_orchestrator_test"
    orch_tree = "tree_orch_001"
    client.post("/api/v1/projects", json={"project_name": "Orchestrator Test"})

    # 1. Natural Language Instruction: Run audit
    res_audit = client.post(
        f"/api/v1/projects/{orch_proj}/sessions/{orch_tree}/messages",
        json={"content": "Please run a reconciliation audit across all our documents"}
    )
    assert res_audit.status_code == 200
    audit_data = res_audit.json()
    assert "audit" in audit_data["assistant_node"]["content"].lower() or "discrepanc" in audit_data["assistant_node"]["content"].lower()
    assert audit_data["action_payload"] is not None
    assert audit_data["action_payload"]["type"] == "GATE_FINDINGS"

    # 2. Natural Language Instruction: Approve finding
    res_appr = client.post(
        f"/api/v1/projects/{orch_proj}/sessions/{orch_tree}/messages",
        json={"content": "Approve finding F-003"}
    )
    assert res_appr.status_code == 200
    assert "approved" in res_appr.json()["assistant_node"]["content"].lower()

    # 3. Natural Language Instruction: Create artifact
    res_art = client.post(
        f"/api/v1/projects/{orch_proj}/sessions/{orch_tree}/messages",
        json={"content": "Create an executive audit report artifact summarizing the project"}
    )
    assert res_art.status_code == 200
    assert "artifact" in res_art.json()["assistant_node"]["content"].lower()

    # 4. Natural Language Instruction: Batch approve all
    res_batch = client.post(
        f"/api/v1/projects/{orch_proj}/sessions/{orch_tree}/messages",
        json={"content": "Batch approve all findings and finalize the register"}
    )
    assert res_batch.status_code == 200
    assert "approved" in res_batch.json()["assistant_node"]["content"].lower() or "register" in res_batch.json()["assistant_node"]["content"].lower()
