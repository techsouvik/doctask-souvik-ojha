"""Artifacts API Router for versioned deliverables."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.tools.artifacts import AsyncArtifactsTools

router = APIRouter(prefix="/projects/{project_id}/artifacts", tags=["Artifacts & Deliverables"])
_artifacts_tool = AsyncArtifactsTools()


class CreateArtifactRequest(BaseModel):
    title: str
    content: str
    artifact_type: Optional[str] = "markdown"


@router.post("")
async def create_artifact(project_id: str, req: CreateArtifactRequest):
    """Create a versioned, content-hashed deliverable artifact."""
    artifact = await _artifacts_tool.create_artifact_async(
        project_id=project_id,
        title=req.title,
        content=req.content,
        artifact_type=req.artifact_type or "markdown"
    )
    return artifact.model_dump()


@router.get("/{artifact_id}")
async def get_artifact(project_id: str, artifact_id: str):
    """Retrieve an artifact by ID."""
    artifact = await _artifacts_tool.get_artifact_async(artifact_id)
    if not artifact or artifact.project_id != project_id:
        raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found in project {project_id}")

    return artifact.model_dump()
