"""Rule Examination Engine: 3-stage compliance & contract rule checker (Movement 2)."""

import os
import yaml
from typing import List, Dict, Any
from src.models.domain import ExtractedFact, Finding, Rule, Severity, DocumentType
from src.reconciliation.detector import detect_conflicts


def load_default_rules() -> List[Rule]:
    """Load system rules from YAML definition."""
    rules_path = os.path.join(os.path.dirname(__file__), "rules.yaml")
    if not os.path.exists(rules_path):
        return []

    with open(rules_path, "r") as f:
        data = yaml.safe_load(f)

    rules = []
    for r in data.get("rules", []):
        rules.append(Rule(
            rule_id=r["rule_id"],
            name=r["name"],
            check_type=r["check_type"],
            target_doc_type=DocumentType(r["target_doc_type"]),
            description=r["description"],
            severity=Severity(r["severity"])
        ))
    return rules


def run_examination_pipeline(facts: List[ExtractedFact]) -> List[Finding]:
    """Execute 3-stage examination pipeline across facts."""
    # Run conflict detector (executes Stage 1, Stage 2, and Stage 3 checks)
    findings = detect_conflicts(facts)
    return findings
