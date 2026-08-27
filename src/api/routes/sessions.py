"""Sessions & Chat Engine API Router with document-aware Q&A, SSE streaming, branching trees, and project conversion."""

import json
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.session.tree import SessionTreeManager
from src.session.chat_engine import ChatEngine
from src.app.project_service import ProjectService

router = APIRouter(prefix="/projects/{project_id}/sessions", tags=["Chat & Session Trees"])
_session_manager = SessionTreeManager()


class PostMessageRequest(BaseModel):
    content: str
    parent_node_id: Optional[str] = None


class BranchMessageRequest(BaseModel):
    parent_node_id: str
    content: str


class RenameSessionRequest(BaseModel):
    title: str


class ConvertToProjectRequest(BaseModel):
    new_project_name: str


@router.get("")
async def list_sessions(project_id: str):
    """List all chat sessions for a project."""
    session_list = []
    for tree_id, tree in _session_manager._trees.items():
        if tree.project_id == project_id:
            session_list.append({
                "tree_id": tree_id,
                "title": tree.title,
                "auto_named": tree.auto_named,
                "message_count": len(tree.nodes),
                "active_leaf_id": tree.active_leaf_id,
                "updated_at": tree.updated_at
            })

    return {"project_id": project_id, "sessions": session_list}


@router.get("/{tree_id}")
async def get_session_tree(project_id: str, tree_id: str):
    """Get active linear message thread for a conversation session."""
    tree = await _session_manager.get_or_create_tree(tree_id, project_id)
    thread = tree.get_thread()

    return {
        "tree_id": tree_id,
        "project_id": project_id,
        "title": tree.title,
        "auto_named": tree.auto_named,
        "active_leaf_id": tree.active_leaf_id,
        "thread": [node.model_dump() for node in thread]
    }


@router.post("/{tree_id}/messages")
async def post_session_message(project_id: str, tree_id: str, req: PostMessageRequest):
    """Send a user message and get a document-grounded AI response in chat."""
    result = await ChatEngine.process_user_chat(
        project_id=project_id,
        tree_id=tree_id,
        user_message=req.content,
        parent_node_id=req.parent_node_id,
        tree_manager=_session_manager
    )
    return result


@router.get("/{tree_id}/stream")
async def stream_session_message_get(
    project_id: str,
    tree_id: str,
    q: str = Query(..., description="User query message"),
    parent_node_id: Optional[str] = Query(None, description="Parent message node ID")
):
    """Server-Sent Events (SSE) streaming endpoint via GET."""
    return _build_sse_stream(project_id, tree_id, q, parent_node_id)


@router.post("/{tree_id}/stream")
async def stream_session_message_post(
    project_id: str,
    tree_id: str,
    req: PostMessageRequest
):
    """Server-Sent Events (SSE) streaming endpoint via POST."""
    return _build_sse_stream(project_id, tree_id, req.content, req.parent_node_id)


def _build_sse_stream(project_id: str, tree_id: str, content: str, parent_node_id: Optional[str]):
    async def event_generator():
        try:
            async for event in ChatEngine.process_user_chat_stream(
                project_id=project_id,
                tree_id=tree_id,
                user_message=content,
                parent_node_id=parent_node_id,
                tree_manager=_session_manager
            ):
                payload_str = json.dumps(event, default=str)
                yield f"data: {payload_str}\n\n"
        except Exception as e:
            err_payload = json.dumps({"type": "error", "error": str(e)})
            yield f"data: {err_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/{tree_id}/convert-to-project")
async def convert_session_to_project(project_id: str, tree_id: str, req: ConvertToProjectRequest):
    """Convert an independent conversation session thread into a formal, named Project Workspace."""
    state = ProjectService.get_project_state(project_id)
    new_project_id = ProjectService.create_project(req.new_project_name, doc_folder=state.doc_folder)

    new_state = ProjectService.get_project_state(new_project_id)
    new_state.documents = state.documents
    new_state.facts = state.facts
    new_state.findings = state.findings
    new_state.pending_findings = state.pending_findings
    new_state.register = state.register

    tree = await _session_manager.get_or_create_tree(tree_id, project_id)
    tree.project_id = new_project_id
    tree.title = req.new_project_name

    return {
        "status": "converted",
        "old_project_id": project_id,
        "new_project_id": new_project_id,
        "project_name": req.new_project_name,
        "documents_count": len(new_state.documents),
        "facts_count": len(new_state.facts)
    }


@router.post("/{tree_id}/branch")
async def branch_session_thread(project_id: str, tree_id: str, req: BranchMessageRequest):
    """Create a new branch in the conversation tree starting from a parent node_id."""
    try:
        user_node = await _session_manager.branch_from_node(tree_id, project_id, req.parent_node_id, req.content)
        result = await ChatEngine.process_user_chat(
            project_id=project_id,
            tree_id=tree_id,
            user_message=req.content,
            parent_node_id=user_node.id,
            tree_manager=_session_manager
        )
        result["branched_from_node_id"] = req.parent_node_id
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{tree_id}")
async def rename_session(project_id: str, tree_id: str, req: RenameSessionRequest):
    """Rename session title."""
    tree = await _session_manager.get_or_create_tree(tree_id, project_id)
    tree.title = req.title
    tree.auto_named = False
    return {"tree_id": tree_id, "new_title": tree.title}


@router.delete("/{tree_id}")
async def delete_session(project_id: str, tree_id: str):
    """Delete a chat session."""
    if tree_id in _session_manager._trees:
        del _session_manager._trees[tree_id]
        return {"status": "deleted", "tree_id": tree_id}
    raise HTTPException(status_code=404, detail=f"Session {tree_id} not found")
