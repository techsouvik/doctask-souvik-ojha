"""Project Application Service for managing project lifecycle & pipeline execution."""

import os
from typing import Dict, Any, Optional
from src.graph.state import PipelineState
from src.graph.workflow import run_pipeline
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

        if not doc_folder:
            # Create isolated empty folder for new workspace
            folder = f"/tmp/documesh_projects/{project_id}"
            os.makedirs(folder, exist_ok=True)
        else:
            folder = doc_folder

        state = PipelineState(
            project_id=project_id,
            doc_folder=folder,
            documents=[],
            facts=[],
            findings=[],
            pending_findings=[]
        )
        _ACTIVE_STATES[project_id] = state
        logger.info("project_created", project_id=project_id, doc_folder=folder, tenant_id=tenant_id)
        return project_id

    @staticmethod
    def get_project_state(project_id: str, tenant_id: str = "tenant_default") -> PipelineState:
        """Get or restore project pipeline state."""
        if project_id in _ACTIVE_STATES:
            return _ACTIVE_STATES[project_id]

        # Attempt restore from DB checkpoint
        checkpoint = load_latest_checkpoint(project_id, tenant_id=tenant_id)
        if checkpoint:
            logger.info("project_state_restored_from_checkpoint", project_id=project_id, tenant_id=tenant_id, node=checkpoint.get("current_node"))
            state = PipelineState(**checkpoint)
            _ACTIVE_STATES[project_id] = state
            return state

        # If Seed Greenfield project, load seed corpus
        if project_id in ["proj_greenfield_tech_park", "proj_live_demo", "proj_live_run_workspace"]:
            folder = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
            state = run_pipeline(doc_folder=folder, project_id=project_id)
            _ACTIVE_STATES[project_id] = state
            return state

        # Fresh empty project workspace for new user sessions
        folder = f"/tmp/documesh_projects/{project_id}"
        os.makedirs(folder, exist_ok=True)
        state = PipelineState(
            project_id=project_id,
            doc_folder=folder,
            documents=[],
            facts=[],
            findings=[],
            pending_findings=[]
        )
        _ACTIVE_STATES[project_id] = state
        return state

    @staticmethod
    def run_pipeline_for_project(project_id: str, run_id: str = "run_latest", tenant_id: str = "tenant_default") -> PipelineState:
        """Trigger or resume pipeline state machine execution with distributed lock protection."""
        from src.cache.redis_cache import cache_instance
        
        lock_key = f"pipeline:{tenant_id}:{project_id}"
        acquired = cache_instance.acquire_lock(lock_key, ttl_seconds=60)
        
        try:
            state = ProjectService.get_project_state(project_id, tenant_id=tenant_id)
            logger.info("triggering_pipeline_run", project_id=project_id, tenant_id=tenant_id, current_node=state.current_node)

            updated_state = run_pipeline(
                doc_folder=state.doc_folder,
                project_id=project_id,
                run_id=run_id,
                existing_state=state if state.documents else None
            )
            _ACTIVE_STATES[project_id] = updated_state
            return updated_state
        finally:
            if acquired:
                cache_instance.release_lock(lock_key)
