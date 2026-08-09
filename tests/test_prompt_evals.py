"""Unit tests for Prompt Evaluation & Optimization Engine."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.evals.evaluator import PromptEvaluator
from src.evals.prompt_optimizer import PromptOptimizer, _mock_extractor_v2_v3

client = TestClient(app)


def test_prompt_evaluator_scoring():
    result = PromptEvaluator.evaluate_prompt("Test_Strict_Prompt", _mock_extractor_v2_v3)
    assert result.faithfulness_score == 1.0
    assert result.recall_score == 1.0
    assert result.injection_resistance_score == 1.0
    assert result.overall_score == 1.0


def test_prompt_optimizer_benchmark_api():
    # 1. Get Dataset API
    res_data = client.get("/api/v1/evals")
    assert res_data.status_code == 200
    assert res_data.json()["dataset_size"] == 3

    # 2. Run Evals Benchmark API
    res_run = client.post("/api/v1/evals/run")
    assert res_run.status_code == 200
    report = res_run.json()

    assert "winner_prompt_variant" in report
    assert report["winner_score"] > 0.8
    assert "V3_Enterprise_CoT" in report["winner_prompt_variant"] or "V2_Grounded_Strict" in report["winner_prompt_variant"]
    assert "system_prompt_text" in report
