"""Unit tests for LangGraph v1.2+ Features (Time Travel & Cross-Run Memory Store)."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.graph.time_travel import TimeTravelEngine
from src.graph.store import global_cross_run_store

client = TestClient(app)
PROJECT_ID = "proj_langgraph_v1_test"


def test_langgraph_v1_store_and_time_travel():
    # 1. Test Cross-Run Memory Store
    global_cross_run_store.put_preference(
        namespace="tenant_default",
        key="alias_map",
        value={"Apex Construction Ltd": "Apex", "Apex Const Co": "Apex"}
    )

    alias_map = global_cross_run_store.get_preference("tenant_default", "alias_map")
    assert alias_map is not None
    assert alias_map["Apex Construction Ltd"] == "Apex"

    # 2. Run Pipeline & Save Checkpoints
    client.post("/api/v1/projects", json={"project_name": "LangGraph V1 Test"})
    client.post(f"/api/v1/projects/{PROJECT_ID}/run")

    # 3. Query Time Travel Checkpoint History
    res_hist = client.get(f"/api/v1/projects/{PROJECT_ID}/history")
    assert res_hist.status_code == 200
    checkpoints = res_hist.json()["checkpoint_history"]
    assert len(checkpoints) >= 5
    node_names = [cp["node_name"] for cp in checkpoints]
    assert "INGEST" in node_names
    assert "CLASSIFY" in node_names
    assert "EXTRACT" in node_names

    # 4. Rewind Time Travel to CLASSIFY node
    res_rewind = client.post(
        f"/api/v1/projects/{PROJECT_ID}/rewind",
        json={"target_node_name": "CLASSIFY"}
    )
    assert res_rewind.status_code == 200
    assert res_rewind.json()["rewound_to_node"] == "CLASSIFY"
