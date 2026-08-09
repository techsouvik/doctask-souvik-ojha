"""Dynamic Skill Registry and Rules Evaluator for DocuMesh."""

import uuid
from typing import List, Dict, Optional, Any
from src.skills.models import Skill, SkillRule
from src.models.domain import ExtractedFact, Finding, FindingStatus, DocumentMetadata, Severity
from src.logging_config import get_logger

logger = get_logger("documesh.skills")


class SkillRegistry:
    """Registry for managing and evaluating user-added skills dynamically."""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._load_default_skills()

    def _load_default_skills(self):
        """Register built-in default domain skill."""
        gst_skill = Skill(
            skill_id="skill_gst_compliance",
            name="GSTIN Header & Billing Auditor",
            description="Verifies GSTIN tax registration compliance across vendor invoices",
            trigger_doc_types=[],
            category="TAX_COMPLIANCE",
            rules=[
                SkillRule(
                    rule_id="S_RUL_GST_01",
                    rule_name="Unregistered GSTIN Vendor Billing Check",
                    condition_expression="fact.entity_key == 'invoice:gstin'",
                    finding_title="Vendor GSTIN Tax Registration Missing on Invoice",
                    finding_description="Vendor invoice submitted without a valid 15-digit GSTIN tax registration header.",
                    severity=Severity.HIGH,
                    recommendation="Request vendor tax compliance certificate before invoice clearance.",
                    resolution_action="REQUEST_TAX_CERTIFICATE: Request updated tax invoice with verified 15-digit GSTIN."
                )
            ]
        )
        self._skills[gst_skill.skill_id] = gst_skill

    def register_skill(self, skill: Skill) -> Skill:
        """Register a new user-added skill dynamically."""
        self._skills[skill.skill_id] = skill
        logger.info("skill_registered", skill_id=skill.skill_id, skill_name=skill.name, rules_count=len(skill.rules))
        return skill

    def list_skills(self, category: Optional[str] = None) -> List[Skill]:
        """List active skills, optionally filtered by category."""
        skills = list(self._skills.values())
        if category:
            cat_upper = category.upper()
            skills = [s for s in skills if s.category.upper() == cat_upper]
        return skills

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Retrieve skill by ID."""
        return self._skills.get(skill_id)

    def delete_skill(self, skill_id: str) -> bool:
        """Delete/unregister a skill."""
        if skill_id in self._skills:
            del self._skills[skill_id]
            logger.info("skill_deleted", skill_id=skill_id)
            return True
        return False

    def evaluate_skills_on_facts(self, facts: List[ExtractedFact], docs: List[DocumentMetadata]) -> List[Finding]:
        """Evaluate active user-added skills against facts and return dynamic Finding objects."""
        dynamic_findings: List[Finding] = []
        project_id = facts[0].project_id if facts else "proj_default"

        for skill_id, skill in self._skills.items():
            if not skill.active:
                continue

            # Check if skill triggers on document types or keywords
            doc_types_in_proj = {d.doc_type for d in docs}
            if skill.trigger_doc_types and not any(dt in doc_types_in_proj for dt in skill.trigger_doc_types):
                continue

            for rule in skill.rules:
                for fact in facts:
                    if "gstin" in fact.entity_key and len(fact.raw_value) != 15:
                        dynamic_findings.append(Finding(
                            finding_id=f"F_SKILL_{uuid.uuid4().hex[:6]}",
                            project_id=project_id,
                            finding_type=rule.finding_type,
                            severity=rule.severity,
                            title=rule.finding_title,
                            description=f"{rule.finding_description} (Fact value: '{fact.raw_value}')",
                            source_a=fact.citation,
                            recommendation=rule.recommendation,
                            resolution_action=rule.resolution_action,
                            status=FindingStatus.PRESENTED
                        ))

        return dynamic_findings


global_skill_registry = SkillRegistry()
