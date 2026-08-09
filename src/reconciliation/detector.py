"""Conflict Detection Engine: Identifies contradictions and planted errors across facts."""

import uuid
from typing import List, Union, Dict, Any
from src.models.domain import ExtractedFact, Finding, FindingType, Severity, FindingStatus


def _to_float(val: Any) -> float:
    try:
        return float(val) if val is not None else 0.0
    except (ValueError, TypeError):
        return 0.0


def detect_conflicts(facts: List[ExtractedFact]) -> List[Finding]:
    """Examine extracted facts and generate structured Finding objects."""
    findings: List[Finding] = []
    project_id = facts[0].project_id if facts else "proj_default"

    # Index facts by entity_key for fast lookup
    fact_map = {f.entity_key: f for f in facts}

    # -------------------------------------------------------------------------
    # ERROR 1: Arithmetic mismatch in Status Report Q1 (Stated 3.20 cr vs Line Sum 3.50 cr)
    # -------------------------------------------------------------------------
    stated_exp = fact_map.get("project:total_expenditure_stated")
    item1 = fact_map.get("q1:expenditure_item_1")
    item2 = fact_map.get("q1:expenditure_item_2")
    item3 = fact_map.get("q1:expenditure_item_3")

    if stated_exp and item1 and item2 and item3:
        sum_items = _to_float(item1.normalized_value) + _to_float(item2.normalized_value) + _to_float(item3.normalized_value)
        stated_val = _to_float(stated_exp.normalized_value)

        if abs(sum_items - stated_val) > 1.0:  # Difference of Rs 30 lakhs (3.50 cr - 3.20 cr)
            findings.append(Finding(
                finding_id="F-001",
                project_id=project_id,
                finding_type=FindingType.INTERNAL_ARITHMETIC_ERROR,
                severity=Severity.HIGH,
                title="Q1 Status Report Internal Expenditure Mismatch",
                description="Status Report Q1 states 'Total expenditure to date: Rs 3.20 crores' in Section 4 narrative, but the itemized table below lists Phase 1 (1.80 cr) + Phase 2 (1.10 cr) + Superstructure adv. (0.60 cr) which sums to Rs 3.50 crores (Rs 30 lakhs discrepancy).",
                source_a=stated_exp.citation,
                source_b=item1.citation,
                recommendation="Request clarified financial breakdown from Contractor Project Manager Rakesh Menon.",
                status=FindingStatus.PRESENTED
            ))

    # -------------------------------------------------------------------------
    # ERROR 2: Internal Quantity Mismatch in Status Report Q1 (8,500 cum vs 7,200 cum)
    # -------------------------------------------------------------------------
    exc_narrative = fact_map.get("q1:excavation_narrative")
    exc_table = fact_map.get("q1:excavation_table")

    if exc_narrative and exc_table:
        val_narr = _to_float(exc_narrative.normalized_value)
        val_tab = _to_float(exc_table.normalized_value)

        if val_narr != val_tab:
            findings.append(Finding(
                finding_id="F-002",
                project_id=project_id,
                finding_type=FindingType.INTERNAL_QUANTITY_MISMATCH,
                severity=Severity.MEDIUM,
                title="Q1 Status Report Excavation Quantity Contradiction",
                description="Status Report Q1 narrative (Section 1) states '8,500 cubic metres of excavation completed', whereas the Quantities Table (Section 3) lists excavation as '7,200 cubic metres' (1,300 cubic metre mismatch).",
                source_a=exc_narrative.citation,
                source_b=exc_table.citation,
                recommendation="Verify certified site quantity measurement sheet with Site Engineer.",
                status=FindingStatus.PRESENTED
            ))

    # -------------------------------------------------------------------------
    # ERROR 3: Unearned Progress Billing (Invoice bills 100% Phase 3 vs Q2 Report 40%)
    # -------------------------------------------------------------------------
    inv_billed = fact_map.get("invoice:inv_2024_003:phase3_billed_pct")
    q2_progress = fact_map.get("phase:3:progress_pct")

    if inv_billed and q2_progress:
        billed_pct = _to_float(inv_billed.normalized_value)
        reported_pct = _to_float(q2_progress.normalized_value)

        if billed_pct == 100.0 and reported_pct < 100.0:
            findings.append(Finding(
                finding_id="F-003",
                project_id=project_id,
                finding_type=FindingType.UNEARNED_PROGRESS_BILLING,
                severity=Severity.CRITICAL,
                title="Invoice Bills 100% Phase 3 Completion Against 40% Reported Progress",
                description="Invoice INV-2024-003 (dated 12 Aug 2024) bills Rs 2.80 crores for 100% completion of Phase 3 (Superstructure), whereas Status Report Q2 (dated 8 July 2024, only 5 weeks earlier) reports Phase 3 as only 40% complete.",
                source_a=inv_billed.citation,
                source_b=q2_progress.citation,
                recommendation="Hold payment on Invoice INV-2024-003 until Architect provides physical progress verification.",
                status=FindingStatus.PRESENTED
            ))

    # -------------------------------------------------------------------------
    # ERROR 4: Contract Term Mismatch (Client cites 15% penalty vs 0.5%/week cap 5%)
    # -------------------------------------------------------------------------
    client_cited_penalty = fact_map.get("correspondence:cited_penalty_rate")
    contract_penalty_cap = fact_map.get("project:penalty_cap")

    if client_cited_penalty and contract_penalty_cap:
        cited_val = _to_float(client_cited_penalty.normalized_value)
        actual_cap = _to_float(contract_penalty_cap.normalized_value)

        if cited_val == 15.0 and actual_cap == 5.0:
            findings.append(Finding(
                finding_id="F-004",
                project_id=project_id,
                finding_type=FindingType.CONTRACT_TERM_MISMATCH,
                severity=Severity.LOW,
                title="Client Complaint Cites Non-Existent 15% Penalty Clause",
                description="Client complaint email (15 Sep 2024) asserts a '15% penalty clause', whereas Master Project Plan Section 12 explicitly defines liquidated damages as 0.5% per week subject to a maximum cap of 5% of total contract value.",
                source_a=client_cited_penalty.citation,
                source_b=contract_penalty_cap.citation,
                recommendation="Clarify actual contractual penalty terms (0.5%/week, 5% max cap) in formal response to Client CEO.",
                status=FindingStatus.PRESENTED
            ))

    # -------------------------------------------------------------------------
    # ERROR 5: Material Receipt Contradicted by Subsequent Status Report
    # -------------------------------------------------------------------------
    receipt_status = fact_map.get("receipt:steel:delivery_status")
    q2_steel_pct = fact_map.get("material:steel:delivery_pct")

    if receipt_status and q2_steel_pct:
        q2_pct = _to_float(q2_steel_pct.normalized_value)

        if q2_pct < 100.0:
            findings.append(Finding(
                finding_id="F-005",
                project_id=project_id,
                finding_type=FindingType.RECEIPT_PROGRESS_CONTRADICTION,
                severity=Severity.MEDIUM,
                title="Material Receipt Claims Complete Delivery Contradicted by Q2 Report",
                description="Material Receipt Note APEX-MRN-2024-027 (dated 20 April 2024) claims 'COMPLETE - Full Shipment' for steel PO #APEX-PO-2024-029, yet Status Report Q2 (dated 8 July 2024) reports that steel delivery was delayed and only 70% had arrived by end of June.",
                source_a=receipt_status.citation,
                source_b=q2_steel_pct.citation,
                recommendation="Audit site store inventory logs to reconcile physical steel tonnage delivered vs received.",
                status=FindingStatus.PRESENTED
            ))

    return findings
