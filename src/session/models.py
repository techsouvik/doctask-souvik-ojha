"""Data models for Conversation Trees and Session Management."""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MessageNode(BaseModel):
    """A node in a branching conversation tree."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)
    role: str  # "user", "assistant", "system", "tool"
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationTree(BaseModel):
    """Branching conversation tree representing a session's history."""
    tree_id: str
    project_id: str
    title: str = "New Conversation"
    auto_named: bool = False
    root_node_id: Optional[str] = None
    active_leaf_id: Optional[str] = None
    nodes: Dict[str, MessageNode] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_message(self, role: str, content: str, parent_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> MessageNode:
        """Add a new message node to the tree, supporting branching."""
        node = MessageNode(
            role=role,
            content=content,
            parent_id=parent_id or self.active_leaf_id,
            metadata=metadata or {}
        )

        if node.parent_id and node.parent_id in self.nodes:
            self.nodes[node.parent_id].children_ids.append(node.id)

        self.nodes[node.id] = node

        if not self.root_node_id:
            self.root_node_id = node.id

        self.active_leaf_id = node.id
        self.updated_at = datetime.utcnow()
        return node

    def get_thread(self, leaf_id: Optional[str] = None) -> List[MessageNode]:
        """Retrieve the linear thread of messages from root to specified leaf."""
        target_id = leaf_id or self.active_leaf_id
        if not target_id or target_id not in self.nodes:
            return []

        thread = []
        curr_id = target_id
        while curr_id and curr_id in self.nodes:
            node = self.nodes[curr_id]
            thread.append(node)
            curr_id = node.parent_id

        thread.reverse()
        return thread
