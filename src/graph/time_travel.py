"""LangGraph Time Travel & State Rewind Engine (LangGraph v1.2+ Features)."""

from typing import Dict, Any, List, Optional
from src.graph.workflow import build_documesh_graph
from src.graph.state import PipelineState
from src.app.project_service import ProjectService, _ACTIVE_STATES
from src.models.database import load_latest_checkpoint, save_checkpoint
from src.logging_config import get_logger

logger = get_logger("documesh.graph.time_travel")


class TimeTravelEngine:
    """Engine for inspecting state history and rewinding LangGraph state machines."""

    @staticmethod
    def get_project_history(project_id: str) -> List[Dict[str, Any]]:
        """Get history of node checkpoints for time-travel inspection."""
        from src.models.database import get_db_engine, CheckpointModel
        get_db_engine()
        from src.models.database import _SESSION_FACTORY

        if _SESSION_FACTORY is None:
            return []

        session = _SESSION_FACTORY()
        try:
            checkpoints = session.query(CheckpointModel).filter(
                CheckpointModel.project_id == project_id
            ).order_by(CheckpointModel.seq_id.asc()).all()

            history = []
            for cp in checkpoints:
                history.append({
                    "checkpoint_id": cp.id,
                    "seq_id": cp.seq_id,
                    "node_name": cp.node_name,
                    "created_at": cp.created_at
                })
            return history
        finally:
            session.close()

    @staticmethod
    def rewind_to_node(project_id: str, target_node_name: str, state_overrides: Optional[Dict[str, Any]] = None) -> PipelineState:
        """Rewind graph state back to a target node (e.g. EXTRACT, CLASSIFY) and re-branch execution."""
        from src.models.database import get_db_engine, CheckpointModel
        import json
        get_db_engine()
        from src.models.database import _SESSION_FACTORY

        if _SESSION_FACTORY is None:
            raise ValueError(f"Database not initialized for time travel on project {project_id}")

        session = _SESSION_FACTORY()
        try:
            target_cp = session.query(CheckpointModel).filter(
                CheckpointModel.project_id == project_id,
                CheckpointModel.node_name == target_node_name.upper()
            ).order_by(CheckpointModel.seq_id.desc()).first()

            if target_cp is None or target_cp.state_json is None:
                raise ValueError(f"No checkpoint found for node {target_node_name} in project {project_id}")

            state_data = json.loads(str(target_cp.state_json))

            # Apply state overrides if provided
            if state_overrides:
                state_data.update(state_overrides)

            rewound_state = PipelineState(**state_data)
            _ACTIVE_STATES[project_id] = rewound_state

            logger.info("time_travel_rewind_success", project_id=project_id, rewound_to_node=target_node_name)
            return rewound_state
        finally:
            session.close()
