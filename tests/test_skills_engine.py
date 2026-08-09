"""Unit tests for Dynamic Skill & Playbook Engine."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.skills.models import Skill, SkillRule
from src.skills.registry import global_skill_registry
from src.models.domain import Severity

client = TestClient(app)
PROJECT_ID = "proj_skills_test"


def test_dynamic_skill_lifecycle_and_api():
    # 1. List Default Skills via API
    res_list = client.get(f"/api/v1/projects/{PROJECT_ID}/skills")
    assert res_list.status_code == 200
    skills = res_list.json()["skills"]
    assert len(skills) >= 1

    # 2. Register Custom User Skill via API
    res_reg = client.post(
        f"/api/v1/projects/{PROJECT_ID}/skills",
        json={
            "name": "Safety Test Certificate Auditor",
            "description": "Requires certified safety test report for all steel shipments",
            "category": "SAFETY",
            "rule_name": "Missing Safety Certificate Check",
            "finding_title": "Safety Test Certificate Missing for Steel Delivery",
            "finding_description": "Steel delivery MRN-027 missing certified tensile strength test report",
            "severity": "CRITICAL",
            "recommendation": "Obtain ISO safety certificate from supplier before site clearance.",
            "resolution_action": "REQUIRE_SAFETY_CERTIFICATE: Request ISO certified tensile strength report."
        }
    )

    assert res_reg.status_code == 200
    reg_data = res_reg.json()
    skill_id = reg_data["skill"]["skill_id"]
    assert skill_id.startswith("skill_")

    # 3. List Skills with Category Filter
    res_cat = client.get(f"/api/v1/projects/{PROJECT_ID}/skills?category=SAFETY")
    assert res_cat.status_code == 200
    assert len(res_cat.json()["skills"]) == 1

    # 4. Delete Skill
    res_del = client.delete(f"/api/v1/projects/{PROJECT_ID}/skills/{skill_id}")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "deleted"
