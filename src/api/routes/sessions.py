"""Sessions & Conversation Trees API Router."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.session.tree import SessionTreeManager

router = APIRouter(prefix="/projects/{project_id}/sessions", tags=["Sessions & Conversation Trees"])
_session_manager = SessionTreeManager()


class PostMessageRequest(BaseModel):
    content: str
    parent_node_id: Optional[str] = None


class BranchMessageRequest(BaseModel):
    parent_node_id: str
    content: str


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
    """Post a user message to the conversation session."""
    user_node = await _session_manager.add_user_message(tree_id, project_id, req.content, req.parent_node_id)

    # Simulated AI response for conversation thread
    ai_response = f"I've processed your message regarding: '{user_node.content}'. Running document reconciliation checks..."
    assistant_node = await _session_manager.add_assistant_message(tree_id, project_id, ai_response, user_node.id)

    tree = await _session_manager.get_or_create_tree(tree_id, project_id)

    return {
        "tree_id": tree_id,
        "title": tree.title,
        "user_node": user_node.model_dump(),
        "assistant_node": assistant_node.model_dump()
    }


@router.post("/{tree_id}/branch")
async def branch_session_thread(project_id: str, tree_id: str, req: BranchMessageRequest):
    """Create a new branch in the conversation tree starting from a parent node_id."""
    try:
        user_node = await _session_manager.branch_from_node(tree_id, project_id, req.parent_node_id, req.content)
        ai_response = f"Branch created from node {req.parent_node_id}. Processing new direction..."
        assistant_node = await _session_manager.add_assistant_message(tree_id, project_id, ai_response, user_node.id)

        tree = await _session_manager.get_or_create_tree(tree_id, project_id)

        return {
            "tree_id": tree_id,
            "title": tree.title,
            "branched_from_node_id": req.parent_node_id,
            "user_node": user_node.model_dump(),
            "assistant_node": assistant_node.model_dump()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
