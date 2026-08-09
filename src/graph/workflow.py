"""LangGraph Workflow definition and runner for DocuMesh."""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from src.graph.state import PipelineState
from src.graph.nodes import (
    node_ingest, node_classify, node_extract, node_reconcile,
    node_examine, node_gate, node_deliver
)


def route_after_examine(state: PipelineState) -> Literal["node_gate", "node_deliver"]:
    """Conditional edge: Route to GATE if pending findings exist, else DELIVER."""
    pending = [f for f in state.findings if f.status.value == "PRESENTED" or f.status == "PRESENTED"]
    if pending:
        return "node_gate"
    return "node_deliver"


def route_after_gate(state: PipelineState) -> Literal["node_deliver", "__end__"]:
    """Conditional edge: Route to DELIVER if gate is cleared, else pause at END."""
    pending = [f for f in state.findings if f.status.value == "PRESENTED" or f.status == "PRESENTED"]
    if not pending:
        return "node_deliver"
    return "__end__"  # Pauses state machine at gate for human decision


def build_documesh_graph():
    """Build and compile the complete DocuMesh LangGraph State Machine."""
    builder = StateGraph(PipelineState)

    # Add nodes
    builder.add_node("node_ingest", node_ingest)
    builder.add_node("node_classify", node_classify)
    builder.add_node("node_extract", node_extract)
    builder.add_node("node_reconcile", node_reconcile)
    builder.add_node("node_examine", node_examine)
    builder.add_node("node_gate", node_gate)
    builder.add_node("node_deliver", node_deliver)

    # Set entry point
    builder.set_entry_point("node_ingest")

    # Add standard linear edges
    builder.add_edge("node_ingest", "node_classify")
    builder.add_edge("node_classify", "node_extract")
    builder.add_edge("node_extract", "node_reconcile")
    builder.add_edge("node_reconcile", "node_examine")

    # Conditional routing after EXAMINE
    builder.add_conditional_edges(
        "node_examine",
        route_after_examine,
        {
            "node_gate": "node_gate",
            "node_deliver": "node_deliver"
        }
    )

    # Conditional routing after GATE
    builder.add_conditional_edges(
        "node_gate",
        route_after_gate,
        {
            "node_deliver": "node_deliver",
            "__end__": END
        }
    )

    builder.add_edge("node_deliver", END)

    return builder.compile()


def run_pipeline(
    doc_folder: str = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park",
    project_id: str = "proj_greenfield_tech_park",
    run_id: str = "run_001"
) -> PipelineState:
    """Execute the pipeline from start to GATE/DELIVER."""
    graph = build_documesh_graph()
    initial_state = PipelineState(
        project_id=project_id,
        run_id=run_id,
        doc_folder=doc_folder
    )

    final_state_dict = graph.invoke(initial_state)
    if isinstance(final_state_dict, dict):
        return PipelineState(**final_state_dict)
    return final_state_dict
