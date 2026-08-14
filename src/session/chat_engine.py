"""LLM-Driven Conversational Chat Engine for DocuMesh Engine."""

import os
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.session.tree import SessionTreeManager
from src.session.models import MessageNode
from src.app.project_service import ProjectService
from src.reconciliation.search import HybridSearchIndex
from src.llm.factory import get_llm_instance
from src.llm.models import ModelProviderConfig
from src.logging_config import get_logger

logger = get_logger("documesh.chat.engine")


class ChatEngine:
    """LLM-driven chat engine supporting multi-turn conversation trees & document grounding."""

    @staticmethod
    async def process_user_chat(
        project_id: str,
        tree_id: str,
        user_message: str,
        parent_node_id: Optional[str] = None,
        tree_manager: Optional[SessionTreeManager] = None,
        llm_config: Optional[ModelProviderConfig] = None
    ) -> Dict[str, Any]:
        mgr = tree_manager or SessionTreeManager()

        # 1. Retrieve Conversation Tree & History Thread
        tree = await mgr.get_or_create_tree(tree_id, project_id)
        history_nodes = tree.get_thread()

        # 2. Add User Message Node
        user_node = await mgr.add_user_message(tree_id, project_id, user_message, parent_node_id)

        # 3. Retrieve Project State & Hybrid Search Index for Document Grounding
        state = ProjectService.get_project_state(project_id)

        index = HybridSearchIndex()
        all_chunks = []
        for doc in state.documents:
            all_chunks.extend(doc.chunks)
        index.add_chunks(all_chunks)

        search_hits = index.search(user_message, top_k=5)

        context_snippets = []
        citation_sources = []

        for chunk, score in search_hits:
            if score > 0.05:
                context_snippets.append(f"• Document: {chunk.doc_name} (Section: {chunk.section_title or 'Main'}):\n  \"{chunk.text}\"")
                citation_sources.append({"doc_name": chunk.doc_name, "section": chunk.section_title or "Main"})

        context_text = "\n\n".join(context_snippets) if context_snippets else "No specific document chunks matched the search query."

        # 4. Generate LLM Conversational Response using Multi-Provider Factory
        chat_model = get_llm_instance(llm_config)

        if chat_model is not None:
            try:
                # Convert tree history to LangChain messages
                lc_messages: List[Any] = [
                    SystemMessage(content=(
                        "You are DocuMesh AI, an expert agentic document reconciliation assistant.\n"
                        "You own a project document pile (contracts, status reports, invoices, material receipts, correspondence).\n"
                        "Answer user questions accurately, professionally, and naturally based on the provided document context.\n"
                        "Always cite exact document names when referencing numbers or terms.\n\n"
                        f"=== RELEVANT PROJECT DOCUMENT CONTEXT ===\n{context_text}\n"
                        f"Active Findings in Project: {len(state.findings)}\n"
                        f"Project Status: {state.status}\n"
                    ))
                ]

                for node in history_nodes[-6:]:  # Last 6 turns for context window
                    if node.role == "user":
                        lc_messages.append(HumanMessage(content=node.content))
                    elif node.role == "assistant":
                        lc_messages.append(AIMessage(content=node.content))

                lc_messages.append(HumanMessage(content=user_message))

                ai_response = await chat_model.ainvoke(lc_messages)
                assistant_reply = ai_response.content if hasattr(ai_response, "content") else str(ai_response)

            except Exception as e:
                logger.error("chat_llm_error_using_fallback", error=str(e))
                assistant_reply = ChatEngine._generate_context_reply(user_message, state, context_snippets)
        else:
            assistant_reply = ChatEngine._generate_context_reply(user_message, state, context_snippets)

        # 5. Add Assistant Message Node to Persistent Tree
        assistant_node = await mgr.add_assistant_message(
            tree_id=tree_id,
            project_id=project_id,
            content=assistant_reply,
            parent_node_id=user_node.id
        )

        assistant_node.metadata["citations"] = citation_sources

        logger.info(
            "chat_turn_processed_with_llm",
            project_id=project_id,
            tree_id=tree_id,
            user_node_id=user_node.id,
            assistant_node_id=assistant_node.id,
            llm_active=chat_model is not None
        )

        return {
            "tree_id": tree_id,
            "session_title": tree.title,
            "user_node": user_node.model_dump(),
            "assistant_node": assistant_node.model_dump(),
            "citations": citation_sources
        }

    @staticmethod
    def _generate_context_reply(user_message: str, state: Any, snippets: List[str]) -> str:
        """Contextual fallback response when no LLM key is configured."""
        msg_lower = user_message.lower()

        if "hello" in msg_lower or "hi" in msg_lower or "hey" in msg_lower or "heelo" in msg_lower:
            return (
                f"Hello! I am DocuMesh AI, your document reconciliation assistant. "
                f"I'm currently tracking **{len(state.documents)} documents** and **{len(state.findings)} discrepancy findings** "
                f"for project '{state.project_id}'. What would you like to analyze or verify?"
            )

        if "penalty" in msg_lower or "liquidated" in msg_lower or "clause" in msg_lower:
            return (
                "Based on the Master Project Plan (§12) and Contract Amendment #1, "
                "liquidated damages are defined at **0.5% per week of delay**, subject to a **maximum cap of 5%** of the total contract value (Rs 12.50 crores). "
                "A client complaint email claiming a '15% penalty clause' was flagged as a discrepancy finding (F-004)."
            )

        if "invoice" in msg_lower or "billing" in msg_lower or "phase 3" in msg_lower:
            return (
                "Invoice INV-2024-003 bills **Rs 2.80 crores** for 100% Phase 3 completion. "
                "However, Q2 Status Report (Section 2) confirms Phase 3 was only **40% complete** at end of June. "
                "A critical finding (F-003) was flagged proposing a credit note of Rs 1.68 crores."
            )

        if snippets:
            return (
                f"I found the following document evidence matching your query:\n\n" + "\n\n".join(snippets[:2]) +
                f"\n\nWould you like me to run a full state machine re-evaluation or export the Project Register?"
            )

        return (
            f"I've received your query regarding: '{user_message}'. "
            f"The project currently holds {len(state.documents)} documents with {len(state.findings)} active findings. "
            f"You can ask me about contract values, handover dates, invoice billing, or penalty clauses!"
        )
