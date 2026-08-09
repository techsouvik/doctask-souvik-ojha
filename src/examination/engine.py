"""Rule Examination Engine: 3-stage compliance checker + dynamic user-added skills evaluator."""

import os
import yaml
from typing import List, Dict, Any
from src.models.domain import ExtractedFact, Finding, DocumentMetadata
from src.reconciliation.detector import detect_conflicts
from src.skills.registry import global_skill_registry
from src.logging_config import get_logger

logger = get_logger("documesh.examination")


def run_rule_examination(facts: List[ExtractedFact], docs: List[DocumentMetadata]) -> List[Finding]:
    """Run Movement 2 Rule Examination (Internal -> Cross-Doc -> Contract) + User Skills."""
    logger.info("running_rule_examination", facts_count=len(facts), docs_count=len(docs))

    # 1. Base detector conflicts (planted errors & core contract rules)
    findings = detect_conflicts(facts)

    # 2. Dynamic User-Added Skills evaluation
    skill_findings = global_skill_registry.evaluate_skills_on_facts(facts, docs)
    findings.extend(skill_findings)

    logger.info("rule_examination_complete", static_findings_count=len(findings) - len(skill_findings), skill_findings_count=len(skill_findings), total_findings=len(findings))

    return findings


# Alias for backward compatibility
run_examination_pipeline = run_rule_examination
