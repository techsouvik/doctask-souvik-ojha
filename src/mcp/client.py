"""DocuMesh Machine Client SDK (SuperDocs Behavior #4: A machine can drive it).

Provides a programmatic, automated client for other programs, scripts, and agents
to drive the complete reconciliation lifecycle end-to-end without a web browser.
"""

from typing import Dict, Any, List, Optional
import httpx
from src.app.project_service import ProjectService
from src.app.finding_service import FindingService
from src.app.register_service import RegisterService
from src.models.domain import FindingStatus


class DocuMeshMachineClient:
    """Programmatic Machine Client for driving DocuMesh end-to-end."""

    def __init__(self, base_url: Optional[str] = None, tenant_id: str = "tenant_default"):
        """Initialize machine client.
        
        Args:
            base_url: If provided (e.g. 'http://localhost:8000'), calls HTTP REST API.
                      If None, executes in-process application services directly.
            tenant_id: Tenant context header.
        """
        self.base_url = base_url.rstrip("/") if base_url else None
        self.tenant_id = tenant_id

    def create_project(self, project_name: str, doc_folder: Optional[str] = None) -> str:
        """Create a new project workspace."""
        if self.base_url:
            resp = httpx.post(
                f"{self.base_url}/api/v1/projects",
                json={"project_name": project_name, "doc_folder": doc_folder},
                headers={"X-Tenant-ID": self.tenant_id}
            )
            resp.raise_for_status()
            return resp.json()["project_id"]
        else:
            return ProjectService.create_project(project_name, doc_folder=doc_folder, tenant_id=self.tenant_id)

    def run_audit(self, project_id: str) -> Dict[str, Any]:
        """Execute the 7-stage state machine up to the GATE / DELIVER stage."""
        if self.base_url:
            resp = httpx.post(
                f"{self.base_url}/api/v1/projects/{project_id}/run",
                headers={"X-Tenant-ID": self.tenant_id}
            )
            resp.raise_for_status()
            return resp.json()
        else:
            state = ProjectService.run_pipeline_for_project(project_id, tenant_id=self.tenant_id)
            return {
                "project_id": project_id,
                "status": state.status,
                "current_node": state.current_node,
                "documents_count": len(state.documents),
                "facts_count": len(state.facts),
                "findings_count": len(state.findings),
                "pending_findings_count": len(state.pending_findings)
            }

    def get_status(self, project_id: str) -> Dict[str, Any]:
        """Get live execution state and gate status."""
        if self.base_url:
            resp = httpx.get(
                f"{self.base_url}/api/v1/projects/{project_id}/status",
                headers={"X-Tenant-ID": self.tenant_id}
            )
            resp.raise_for_status()
            return resp.json()
        else:
            state = ProjectService.get_project_state(project_id, tenant_id=self.tenant_id)
            return {
                "project_id": project_id,
                "status": state.status,
                "current_node": state.current_node,
                "pending_findings_count": len(state.pending_findings),
                "register_ready": state.register is not None
            }

    def list_findings(self, project_id: str) -> List[Dict[str, Any]]:
        """List all identified discrepancies and findings."""
        if self.base_url:
            resp = httpx.get(
                f"{self.base_url}/api/v1/projects/{project_id}/findings",
                headers={"X-Tenant-ID": self.tenant_id}
            )
            resp.raise_for_status()
            return resp.json()["findings"]
        else:
            return [f.model_dump() for f in FindingService.get_findings(project_id)]

    def approve_finding(self, project_id: str, finding_id: str, approved: bool, feedback: str = "") -> Dict[str, Any]:
        """Explicitly approve or reject an individual finding at the Human/MCP Gate."""
        if self.base_url:
            resp = httpx.post(
                f"{self.base_url}/api/v1/projects/{project_id}/findings/approve",
                json={"finding_id": finding_id, "approved": approved, "feedback": feedback},
                headers={"X-Tenant-ID": self.tenant_id}
            )
            resp.raise_for_status()
            return resp.json()
        else:
            res = FindingService.decide_finding(project_id, finding_id, approved, feedback)
            state = ProjectService.get_project_state(project_id, tenant_id=self.tenant_id)
            return {
                "finding_id": finding_id,
                "new_status": res.get("new_status", "APPROVED" if approved else "REJECTED"),
                "remaining_pending": res.get("remaining_pending", len(state.pending_findings)),
                "pipeline_status": state.status
            }

    def batch_approve_all(self, project_id: str, approved_all: bool = True) -> Dict[str, Any]:
        """Batch approve all findings to clear the Human/MCP Gate."""
        if self.base_url:
            resp = httpx.post(
                f"{self.base_url}/api/v1/projects/{project_id}/findings/batch-approve",
                json={"approved_all": approved_all},
                headers={"X-Tenant-ID": self.tenant_id}
            )
            resp.raise_for_status()
            return resp.json()
        else:
            res = FindingService.batch_decide_findings(project_id, approved_all=approved_all)
            return {
                "project_id": project_id,
                "status": res.get("status"),
                "current_node": res.get("current_node", "DELIVER"),
                "register_generated": res.get("register_generated", True)
            }

    def get_register(self, project_id: str) -> Dict[str, Any]:
        """Retrieve the final reconciled Master Project Register deliverable."""
        if self.base_url:
            resp = httpx.get(
                f"{self.base_url}/api/v1/projects/{project_id}/register",
                headers={"X-Tenant-ID": self.tenant_id}
            )
            resp.raise_for_status()
            return resp.json()
        else:
            reg = RegisterService.get_project_register(project_id)
            return reg.model_dump() if reg else {}

    def export_report_html(self, project_id: str) -> str:
        """Export the executive boardroom-ready audit HTML deliverable."""
        if self.base_url:
            resp = httpx.get(
                f"{self.base_url}/api/v1/projects/{project_id}/export-report",
                headers={"X-Tenant-ID": self.tenant_id}
            )
            resp.raise_for_status()
            return resp.text
        else:
            return RegisterService.generate_executive_report_html(project_id)
