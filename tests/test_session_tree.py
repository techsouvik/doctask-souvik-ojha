"""Unit test for Conversation Tree Branching and Auto-Naming."""

import pytest
from src.session.tree import SessionTreeManager


@pytest.mark.asyncio
async def test_conversation_tree_branching_and_autoname():
    manager = SessionTreeManager()
    tree_id = "tree_test_01"
    project_id = "proj_test_01"

    # First user message -> triggers auto-naming
    node1 = await manager.add_user_message(tree_id, project_id, "Please review the Greenfield Phase 1 status report for errors")
    tree = await manager.get_or_create_tree(tree_id, project_id)

    assert tree.auto_named is True
    assert "Review" in tree.title or "Greenfield" in tree.title

    # Assistant response
    node2 = await manager.add_assistant_message(tree_id, project_id, "I detected 5 planted errors in the status report and invoice.")

    thread1 = await manager.get_active_thread(tree_id)
    assert len(thread1) == 2
    assert thread1[0].id == node1.id
    assert thread1[1].id == node2.id

    # Branch from node1 (User's first message)
    node3_branch = await manager.branch_from_node(tree_id, project_id, node1.id, "Instead of status report, summarize the master plan")

    thread2 = await manager.get_active_thread(tree_id)
    assert len(thread2) == 2
    assert thread2[0].id == node1.id
    assert thread2[1].id == node3_branch.id
    assert thread2[1].id != node2.id  # Disbranched from original path
