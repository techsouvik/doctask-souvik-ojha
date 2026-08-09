"""Prompt Evaluator Engine scoring Faithfulness, Recall, Injection Resistance, and Accuracy."""

from typing import List, Dict, Any
from pydantic import BaseModel, Field
from src.evals.dataset import EVAL_DATASET, EvalTestCase
from src.extraction.grounding import verify_grounding
from src.classification.security import scan_for_prompt_injection
from src.logging_config import get_logger

logger = get_logger("documesh.evals")


class PromptEvalResult(BaseModel):
    prompt_name: str
    total_cases: int
    faithfulness_score: float  # 0.0 to 1.0 (Verbatim quote grounding)
    recall_score: float        # 0.0 to 1.0 (Fact extraction completeness)
    injection_resistance_score: float  # 0.0 to 1.0 (Security quarantine effectiveness)
    overall_score: float       # Weighted average


class PromptEvaluator:
    """Evaluates system prompt variants against the benchmark eval dataset."""

    @staticmethod
    def evaluate_prompt(prompt_name: str, extraction_fn: Any) -> PromptEvalResult:
        """Run evaluation dataset against an extraction function/prompt and return scores."""
        total_cases = len(EVAL_DATASET)
        faithfulness_hits = 0
        total_grounding_checks = 0
        recall_hits = 0
        total_expected_facts = 0
        injection_blocked = 0
        total_injection_cases = 0

        for case in EVAL_DATASET:
            if case.contains_injection:
                total_injection_cases += 1
                # Check if prompt injection is caught
                is_inj, _, _ = scan_for_prompt_injection(case.input_text)
                if is_inj:
                    injection_blocked += 1
                continue

            # Run extraction function
            extracted_facts = extraction_fn(case)
            total_expected_facts += len(case.expected_facts)

            # Check recall
            extracted_keys = {f.get("entity_key") for f in extracted_facts}
            for exp in case.expected_facts:
                if exp["entity_key"] in extracted_keys:
                    recall_hits += 1

            # Check faithfulness / quote grounding
            for f in extracted_facts:
                quote = f.get("exact_quote", "")
                if quote:
                    total_grounding_checks += 1
                    if verify_grounding(quote, case.input_text):
                        faithfulness_hits += 1

        faithfulness = (faithfulness_hits / total_grounding_checks) if total_grounding_checks > 0 else 1.0
        recall = (recall_hits / total_expected_facts) if total_expected_facts > 0 else 1.0
        injection_res = (injection_blocked / total_injection_cases) if total_injection_cases > 0 else 1.0

        overall = (faithfulness * 0.4) + (recall * 0.4) + (injection_res * 0.2)

        result = PromptEvalResult(
            prompt_name=prompt_name,
            total_cases=total_cases,
            faithfulness_score=round(faithfulness, 4),
            recall_score=round(recall, 4),
            injection_resistance_score=round(injection_res, 4),
            overall_score=round(overall, 4)
        )

        logger.info(
            "eval_completed",
            prompt_name=prompt_name,
            overall_score=result.overall_score,
            faithfulness=result.faithfulness_score,
            recall=result.recall_score
        )

        return result
