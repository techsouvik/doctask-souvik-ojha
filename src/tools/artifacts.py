"""Scalable Async Artifact Generation & Management Tools."""

import os
import hashlib
import uuid
import json
import aiofiles
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class Artifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    project_id: str
    title: str
    artifact_type: str  # "html", "markdown", "json", "pdf"
    content_hash: str
    filepath: str
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AsyncArtifactsTools:
    """Async tools to create, store, version, and manage document deliverables and artifacts."""

    def __init__(self, artifacts_dir: str = "/Users/souvikojha/doctask-souvik-ojha/artifacts"):
        self.artifacts_dir = artifacts_dir
        os.makedirs(self.artifacts_dir, exist_ok=True)
        self._registry: Dict[str, Artifact] = {}

    async def create_artifact_async(
        self,
        project_id: str,
        title: str,
        content: str,
        artifact_type: str = "markdown"
    ) -> Artifact:
        """Create a versioned artifact asynchronously."""
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
        filename = f"{title.lower().replace(' ', '_')}_v1_{content_hash}.{artifact_type}"
        filepath = os.path.join(self.artifacts_dir, project_id, filename)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(content)

        artifact = Artifact(
            project_id=project_id,
            title=title,
            artifact_type=artifact_type,
            content_hash=content_hash,
            filepath=filepath,
            version=1
        )

        self._registry[artifact.artifact_id] = artifact
        return artifact

    async def get_artifact_async(self, artifact_id: str) -> Optional[Artifact]:
        """Retrieve an artifact by ID."""
        return self._registry.get(artifact_id)
