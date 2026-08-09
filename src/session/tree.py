"""Async Conversation Tree Manager with Auto-Naming and Branching."""

from typing import Dict, Optional, List
from src.session.models import ConversationTree, MessageNode
from src.session.naming import generate_session_title


class SessionTreeManager:
    """Async manager for conversation trees, branching, and auto-naming."""

    def __init__(self):
        self._trees: Dict[str, ConversationTree] = {}

    async def get_or_create_tree(self, tree_id: str, project_id: str) -> ConversationTree:
        """Get existing tree or create a new one."""
        if tree_id not in self._trees:
            self._trees[tree_id] = ConversationTree(tree_id=tree_id, project_id=project_id)
        return self._trees[tree_id]

    async def add_user_message(self, tree_id: str, project_id: str, content: str, parent_node_id: Optional[str] = None) -> MessageNode:
        """Add user message and trigger auto-naming if first message."""
        tree = await self.get_or_create_tree(tree_id, project_id)
        node = tree.add_message(role="user", content=content, parent_id=parent_node_id)

        # Auto-name session on first user message
        if not tree.auto_named and len(tree.nodes) <= 2:
            tree.title = generate_session_title(content)
            tree.auto_named = True

        return node

    async def add_assistant_message(self, tree_id: str, project_id: str, content: str, parent_node_id: Optional[str] = None) -> MessageNode:
        """Add assistant response node."""
        tree = await self.get_or_create_tree(tree_id, project_id)
        return tree.add_message(role="assistant", content=content, parent_id=parent_node_id)

    async def branch_from_node(self, tree_id: str, project_id: str, node_id: str, new_user_message: str) -> MessageNode:
        """Create a new branch in the conversation tree starting from a specific parent node."""
        tree = await self.get_or_create_tree(tree_id, project_id)
        if node_id not in tree.nodes:
            raise ValueError(f"Node ID {node_id} not found in tree {tree_id}")

        return tree.add_message(role="user", content=new_user_message, parent_id=node_id)

    async def get_active_thread(self, tree_id: str) -> List[MessageNode]:
        """Get linear message history from root to active leaf."""
        if tree_id not in self._trees:
            return []
        return self._trees[tree_id].get_thread()
