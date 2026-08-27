"""Finding & Gate Application Service for managing Human/MCP Gate decisions."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from src.app.project_service import ProjectService, _ACTIVE_STATES
from src.graph.workflow import build_documesh_graph
from src.graph.state import PipelineState
from src.models.domain import Finding, FindingStatus
from src.models.database import save_checkpoint
from src.logging_config import get_logger

logger = get_logger("documesh.app.finding")


class FindingService:
    """Application service for retrieving findings and applying gate decisions."""

    @staticmethod
    def get_findings(project_id: str, status_filter: Optional[str] = None) -> List[Finding]:
        """Get all findings for a project, optionally filtered by status."""
        state = ProjectService.get_project_state(project_id)
        findings = state.findings

        if status_filter:
            sf_upper = status_filter.upper()
            findings = [f for f in findings if f.status.value == sf_upper or f.status == sf_upper]

        return findings

    @staticmethod
    def decide_finding(project_id: str, finding_id: str, approved: bool, feedback: Optional[str] = None) -> Dict[str, Any]:
        """Approve or reject a finding at the Human/MCP Gate and persist to database checkpoint."""
        state = ProjectService.get_project_state(project_id)
        target_finding = None

        for f in state.findings:
            if f.finding_id == finding_id:
                target_finding = f
                f.status = FindingStatus.APPROVED if approved else FindingStatus.REJECTED
                f.feedback = feedback
                f.decided_at = datetime.utcnow()
                f.decided_by = "Human Reviewer"
                break

        if not target_finding:
            raise ValueError(f"Finding ID {finding_id} not found in project {project_id}")

        # Update pending list
        state.pending_findings = [f for f in state.findings if f.status == FindingStatus.PRESENTED]
        logger.info("finding_decision_applied", project_id=project_id, finding_id=finding_id, approved=approved, remaining_pending=len(state.pending_findings))

        # Resume state machine if gate cleared
        if not state.pending_findings:
            logger.info("gate_cleared_resuming_graph", project_id=project_id)
            state.status = "COMPLETED"
            state.current_node = "DELIVER"
            approved_findings = [f for f in state.findings if f.status == FindingStatus.APPROVED]
            if state.register:
                state.register.approved_findings = approved_findings
                state.register.active_conflicts_count = len(approved_findings)
            _ACTIVE_STATES[project_id] = state
        else:
            _ACTIVE_STATES[project_id] = state

        # Persist updated state to DB checkpoint immediately
        save_checkpoint(project_id, state.current_node, state.model_dump())

        updated_state = _ACTIVE_STATES[project_id]
        return {
            "finding_id": finding_id,
            "new_status": target_finding.status.value,
            "remaining_pending": len(updated_state.pending_findings),
            "pipeline_status": updated_state.status,
            "decided_at": target_finding.decided_at.isoformat() if target_finding.decided_at else None,
            "decided_by": target_finding.decided_by
        }

    @staticmethod
    def batch_decide_findings(project_id: str, approved_all: bool = True, decisions: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """Apply batch decisions across all pending findings and persist to database checkpoint."""
        state = ProjectService.get_project_state(project_id)

        now = datetime.utcnow()
        for f in state.findings:
            if f.status == FindingStatus.PRESENTED:
                if decisions and f.finding_id in decisions:
                    decision = decisions[f.finding_id]
                else:
                    decision = approved_all

                f.status = FindingStatus.APPROVED if decision else FindingStatus.REJECTED
                f.decided_at = now
                f.decided_by = "Human Reviewer"
                if not decision and not f.feedback:
                    f.feedback = "Rejected in batch review"

        state.pending_findings = []
        state.status = "COMPLETED"
        state.current_node = "DELIVER"

        approved_findings = [f for f in state.findings if f.status == FindingStatus.APPROVED]
        if state.register:
            state.register.approved_findings = approved_findings
            state.register.active_conflicts_count = len(approved_findings)

        _ACTIVE_STATES[project_id] = state
        # Persist deliverable state to DB checkpoint
        save_checkpoint(project_id, "DELIVER", state.model_dump())

        logger.info("batch_findings_decisions_applied_and_persisted", project_id=project_id, approved_all=approved_all)
        updated_state = _ACTIVE_STATES[project_id]
        reg = updated_state.register
        return {
            "project_id": project_id,
            "status": updated_state.status,
            "register_hash": reg.content_hash if reg else None,
            "approved_count": len(approved_findings)
        }
