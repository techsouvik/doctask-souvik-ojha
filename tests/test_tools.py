"""Unit tests for scalable async tool system."""

import os
import pytest
from src.tools.file_system import AsyncFileSystemTools
from src.tools.web_search import AsyncWebSearchTools
from src.tools.artifacts import AsyncArtifactsTools


@pytest.mark.asyncio
async def test_async_filesystem_tools(tmp_path):
    test_file = str(tmp_path / "test_doc.txt")
    content = "DocuMesh Async File System Test Content"

    # Async Write
    await AsyncFileSystemTools.write_file_async(test_file, content)
    assert os.path.exists(test_file)

    # Async Read
    read_back = await AsyncFileSystemTools.read_file_async(test_file)
    assert read_back == content

    # Async List Dir
    items = await AsyncFileSystemTools.list_dir_async(str(tmp_path))
    assert len(items) == 1
    assert items[0]["name"] == "test_doc.txt"


@pytest.mark.asyncio
async def test_async_web_search_tools():
    results = await AsyncWebSearchTools.search_async("Greenfield Tech Park construction", limit=2)
    assert len(results) >= 1
    assert "title" in results[0]
    assert "url" in results[0]


@pytest.mark.asyncio
async def test_async_artifacts_tools(tmp_path):
    artifacts_tool = AsyncArtifactsTools(artifacts_dir=str(tmp_path))
    art = await artifacts_tool.create_artifact_async(
        project_id="proj_test",
        title="Project Register Report",
        content="# Project Register Deliverable\n- Fact 1: Rs 14.2 crores",
        artifact_type="markdown"
    )

    assert art.artifact_id is not None
    assert art.version == 1
    assert os.path.exists(art.filepath)

    retrieved = await artifacts_tool.get_artifact_async(art.artifact_id)
    assert retrieved is not None
    assert retrieved.content_hash == art.content_hash
