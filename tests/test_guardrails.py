"""Unit tests for Chat Guardrails, Gibberish Filtering, and Help Onboarding."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)
PROJECT_ID = "proj_greenfield_tech_park"
TREE_ID = "tree_guardrail_test"


def test_gibberish_detection():
    # Test random mash
    res = client.post(
        f"/api/v1/projects/{PROJECT_ID}/sessions/{TREE_ID}/messages",
        json={"content": "asdfghjklqwerty"}
    )
    assert res.status_code == 200
    content = res.json()["assistant_node"]["content"].lower()
    assert "typo" in content or "didn't quite catch" in content or "accidental" in content

    # Test repeated characters
    res_rep = client.post(
        f"/api/v1/projects/{PROJECT_ID}/sessions/{TREE_ID}/messages",
        json={"content": "?????????"}
    )
    assert res_rep.status_code == 200
    content_rep = res_rep.json()["assistant_node"]["content"].lower()
    assert "typo" in content_rep or "didn't quite catch" in content_rep


def test_help_and_onboarding():
    res = client.post(
        f"/api/v1/projects/{PROJECT_ID}/sessions/{TREE_ID}/messages",
        json={"content": "how does this work? I don't understand the product"}
    )
    assert res.status_code == 200
    content = res.json()["assistant_node"]["content"].lower()
    assert "documesh" in content
    assert "reconciliation" in content
    assert "langgraph" in content or "human-in-the-loop" in content


def test_model_diagnostics_query():
    res = client.post(
        f"/api/v1/projects/{PROJECT_ID}/sessions/{TREE_ID}/messages",
        json={"content": "Which model are you using for llm?"}
    )
    assert res.status_code == 200
    content = res.json()["assistant_node"]["content"].lower()
    assert "model" in content
    assert "provider" in content
    assert "offline" in content or "gpt-4o" in content or "claude" in content or "llama" in content


def test_off_topic_redirection():
    res = client.post(
        f"/api/v1/projects/{PROJECT_ID}/sessions/{TREE_ID}/messages",
        json={"content": "tell me a joke about cats"}
    )
    assert res.status_code == 200
    content = res.json()["assistant_node"]["content"].lower()
    assert "reconciliation" in content or "contract" in content or "audit" in content
