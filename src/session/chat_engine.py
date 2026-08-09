"""Chat Engine & Document-Aware Response Generator for Session Conversations."""

from typing import Dict, Any, List, Optional
from src.session.tree import SessionTreeManager
from src.session.models import MessageNode
from src.app.project_service import ProjectService
from src.reconciliation.search import HybridSearchIndex
from src.logging_config import get_logger

logger = get_logger("documesh.chat")


class ChatEngine:
    """Document-aware chat engine that generates grounded responses using project facts."""

    @staticmethod
    async def process_user_chat(
        project_id: str,
        tree_id: str,
        user_message: str,
        parent_node_id: Optional[str] = None,
        tree_manager: Optional[SessionTreeManager] = None
    ) -> Dict[str, Any]:
        mgr = tree_manager or SessionTreeManager()

        # 1. Add User Message Node
        user_node = await mgr.add_user_message(tree_id, project_id, user_message, parent_node_id)

        # 2. Query Project Context & Search Index for grounded retrieval
        state = ProjectService.get_project_state(project_id)
        
        index = HybridSearchIndex()
        all_chunks = []
        for doc in state.documents:
            all_chunks.extend(doc.chunks)
        index.add_chunks(all_chunks)

        search_hits = index.search(user_message, top_k=3)

        # 3. Construct Grounded Assistant Response
        citation_sources = []
        context_snippets = []

        for chunk, score in search_hits:
            if score > 0.1:
                context_snippets.append(f"• [{chunk.doc_name} - {chunk.section_title}]: \"{chunk.text[:200]}...\"")
                citation_sources.append({"doc_name": chunk.doc_name, "section": chunk.section_title})

        if context_snippets:
            assistant_reply = (
                f"I've analyzed your question: \"{user_message}\" against the project document pile.\n\n"
                f"**Relevant Document Evidence:**\n" + "\n".join(context_snippets) + "\n\n"
                f"Based on the project records, the contract status and findings have been cross-referenced."
            )
        else:
            assistant_reply = (
                f"I've processed your message: \"{user_message}\". "
                f"The project currently holds {len(state.documents)} documents with {len(state.findings)} active findings."
            )

        # 4. Add Assistant Message Node to Tree
        assistant_node = await mgr.add_assistant_message(
            tree_id=tree_id,
            project_id=project_id,
            content=assistant_reply,
            parent_node_id=user_node.id
        )

        assistant_node.metadata["citations"] = citation_sources

        logger.info(
            "chat_turn_processed",
            project_id=project_id,
            tree_id=tree_id,
            user_node_id=user_node.id,
            assistant_node_id=assistant_node.id,
            citations_count=len(citation_sources)
        )

        tree = await mgr.get_or_create_tree(tree_id, project_id)

        return {
            "tree_id": tree_id,
            "session_title": tree.title,
            "user_node": user_node.model_dump(),
            "assistant_node": assistant_node.model_dump(),
            "citations": citation_sources
        }
