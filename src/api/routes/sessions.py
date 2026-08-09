"""Sessions & Chat Engine API Router with document-aware Q&A and branching trees."""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.session.tree import SessionTreeManager
from src.session.chat_engine import ChatEngine

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
