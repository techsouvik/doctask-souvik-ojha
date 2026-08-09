"""Evals REST API Router for prompt benchmarking & optimization."""

from typing import Dict, Any
from fastapi import APIRouter
from src.evals.dataset import EVAL_DATASET
from src.evals.prompt_optimizer import PromptOptimizer

router = APIRouter(prefix="/evals", tags=["Prompt Evals & Optimization"])


@router.get("")
def list_eval_dataset():
    """List benchmark evaluation dataset test cases."""
    return {
        "dataset_size": len(EVAL_DATASET),
        "test_cases": [
            {
                "case_id": c.case_id,
                "filename": c.filename,
                "doc_type": c.doc_type,
                "expected_facts_count": len(c.expected_facts),
                "contains_injection": c.contains_injection
            }
            for c in EVAL_DATASET
        ]
    }


@router.post("/run")
def run_prompt_evals():
    """Trigger prompt evaluation benchmark across system prompt variants and return winning prompt."""
    benchmark_report = PromptOptimizer.run_optimization_benchmark()
    return benchmark_report
