"""DocuMesh MCP Server for Machine-Driven Control (Behavior #4).

Exposes DocuMesh capabilities as a standard Model Context Protocol (MCP) server
so other agents, IDEs, and automated workflows can drive the entire reconciliation lifecycle.
"""

import json
from typing import Optional, Dict, Any

try:
    from mcp.server.mcpserver import MCPServer
    mcp = MCPServer("DocuMesh Engine MCP")
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("DocuMesh Engine MCP")
    except ImportError:
        # Graceful fallback mock decorator if mcp is not installed
        class FallbackMCP:
            def tool(self):
                def decorator(fn):
                    return fn
                return decorator
            def run(self):
                print("DocuMesh MCP Server running (fallback mode)")
        mcp = FallbackMCP()

from src.graph.state import PipelineState
from src.graph.workflow import run_pipeline, build_documesh_graph
from src.app.project_service import ProjectService, _ACTIVE_STATES
from src.models.domain import FindingStatus


@mcp.tool()
def run_documesh_analysis(
    project_id: str = "proj_greenfield_tech_park",
    doc_folder: str = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
) -> str:
    """Run DocuMesh document pile analysis up to the Human/MCP Approval Gate."""
    state = ProjectService.get_project_state(project_id)
    if not state.documents and doc_folder:
        state.doc_folder = doc_folder
    state = ProjectService.run_pipeline_for_project(project_id)
    return json.dumps({
        "project_id": project_id,
        "status": state.status,
        "current_node": state.current_node,
        "documents_count": len(state.documents),
        "facts_count": len(state.facts),
        "findings_count": len(state.findings),
        "pending_findings_count": len(state.pending_findings)
    }, indent=2)


@mcp.tool()
def get_documesh_status(project_id: str = "proj_greenfield_tech_park") -> str:
    """Check status of a DocuMesh project run."""
    state = ProjectService.get_project_state(project_id)
    return json.dumps({
        "project_id": project_id,
        "status": state.status,
        "current_node": state.current_node,
        "pending_findings_count": len(state.pending_findings),
        "register_ready": state.register is not None
    }, indent=2)


@mcp.tool()
def list_documesh_findings(project_id: str = "proj_greenfield_tech_park") -> str:
    """List all findings (including planted errors and cross-document contradictions) for a project."""
    state = ProjectService.get_project_state(project_id)
    return json.dumps([f.model_dump() for f in state.findings], indent=2, default=str)


@mcp.tool()
def approve_documesh_finding(
    project_id: str,
    finding_id: str,
    approved: bool,
    feedback: str = ""
) -> str:
    """Explicitly approve or reject a finding at the Human/MCP Gate."""
    state = ProjectService.get_project_state(project_id)
    target = None

    for f in state.findings:
        if f.finding_id == finding_id:
            target = f
            f.status = FindingStatus.APPROVED if approved else FindingStatus.REJECTED
            f.feedback = feedback
            break

    if not target:
        return json.dumps({"error": f"Finding ID {finding_id} not found"})

    state.pending_findings = [f for f in state.findings if f.status == FindingStatus.PRESENTED]

    # Resume graph if gate cleared
    if not state.pending_findings:
        graph = build_documesh_graph()
        final_dict = graph.invoke(state)
        if isinstance(final_dict, dict):
            _ACTIVE_STATES[project_id] = PipelineState(**final_dict)

    return json.dumps({
        "finding_id": finding_id,
        "new_status": target.status.value,
        "remaining_pending": len(_ACTIVE_STATES.get(project_id, state).pending_findings),
        "pipeline_status": _ACTIVE_STATES.get(project_id, state).status
    }, indent=2)


@mcp.tool()
def get_documesh_register(project_id: str = "proj_greenfield_tech_park") -> str:
    """Get the final reconciled Project Register deliverable."""
    state = ProjectService.get_project_state(project_id)
    if not state.register:
        return json.dumps({"error": "Register deliverable not ready. Approve pending findings at GATE first."})

    return json.dumps(state.register.model_dump(), indent=2, default=str)


if __name__ == "__main__":
    if hasattr(mcp, "run"):
        mcp.run()
    else:
        print("DocuMesh MCP Server ready.")
