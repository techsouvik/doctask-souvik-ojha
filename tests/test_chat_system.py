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
