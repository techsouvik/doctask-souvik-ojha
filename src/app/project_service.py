"""Project Application Service for managing project lifecycle & pipeline execution."""

from typing import Dict, Any, Optional
from src.graph.state import PipelineState
from src.graph.workflow import run_pipeline, build_documesh_graph
from src.models.database import save_checkpoint, load_latest_checkpoint
from src.logging_config import get_logger

logger = get_logger("documesh.app.project")

# In-memory active states cache (synced with database checkpoints)
_ACTIVE_STATES: Dict[str, PipelineState] = {}


class ProjectService:
    """Application service for Project management and State Machine execution."""

    @staticmethod
    def create_project(project_name: str, doc_folder: Optional[str] = None, tenant_id: str = "tenant_default") -> str:
        """Create a new project workspace."""
        project_id = f"proj_{project_name.lower().replace(' ', '_')}"
        folder = doc_folder or "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"

        state = PipelineState(
            project_id=project_id,
            doc_folder=folder
        )
        _ACTIVE_STATES[project_id] = state
        logger.info("project_created", project_id=project_id, doc_folder=folder, tenant_id=tenant_id)
        return project_id

    @staticmethod
    def get_project_state(project_id: str) -> PipelineState:
        """Get or restore project pipeline state."""
        if project_id in _ACTIVE_STATES:
            return _ACTIVE_STATES[project_id]

        # Attempt restore from DB checkpoint
        checkpoint = load_latest_checkpoint(project_id)
        if checkpoint:
            logger.info("project_state_restored_from_checkpoint", project_id=project_id, node=checkpoint.get("current_node"))
            state = PipelineState(**checkpoint)
            _ACTIVE_STATES[project_id] = state
            return state

        # Default fallback
        folder = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
        state = run_pipeline(doc_folder=folder, project_id=project_id)
        _ACTIVE_STATES[project_id] = state
        return state

    @staticmethod
    def run_pipeline_for_project(project_id: str, run_id: str = "run_latest") -> PipelineState:
        """Trigger or resume pipeline state machine execution."""
        state = ProjectService.get_project_state(project_id)
        logger.info("triggering_pipeline_run", project_id=project_id, current_node=state.current_node)

        updated_state = run_pipeline(doc_folder=state.doc_folder, project_id=project_id, run_id=run_id)
        _ACTIVE_STATES[project_id] = updated_state
        return updated_state
