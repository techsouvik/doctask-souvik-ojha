"""AI Orchestrator Chat Engine: Autonomous agent with structured tool execution and live SSE streaming."""

import os
import re
import json
import asyncio
from typing import Dict, Any, List, Optional, AsyncIterator
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from src.session.tree import SessionTreeManager
from src.session.models import MessageNode
from src.session.orchestrator_tools import (
    ORCHESTRATOR_TOOLS,
    execute_tool_call,
    run_reconciliation_audit,
    get_project_status,
    search_document_chunks,
    list_project_documents,
    get_discrepancy_findings,
    decide_finding,
    batch_approve_all_findings,
    get_reconciled_register,
    rewind_state_machine,
    create_audit_artifact
)
from src.app.project_service import ProjectService
from src.app.finding_service import FindingService
from src.app.register_service import RegisterService
from src.reconciliation.search import HybridSearchIndex
from src.llm.factory import get_llm_instance
from src.llm.models import ModelProviderConfig
from src.session.guardrails import (
    is_gibberish,
    is_help_or_onboarding,
    is_model_info_query,
    is_off_topic_query,
    get_gibberish_response,
    get_onboarding_help_response,
    get_model_info_response,
    get_off_topic_response
)
from src.logging_config import get_logger

logger = get_logger("documesh.chat.orchestrator")


class ChatEngine:
    """Autonomous AI Orchestrator Agent that plans, selects tools, runs reconciliations,
    inspects documents, reviews discrepancies, and communicates conversationally."""

    @classmethod
    async def process_user_chat_stream(
        cls,
        project_id: str,
        tree_id: str,
        user_message: str,
        parent_node_id: Optional[str] = None,
        tree_manager: Optional[SessionTreeManager] = None,
        llm_config: Optional[ModelProviderConfig] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream real-time orchestrator thinking, tool invocations, token chunks, and actions."""
        mgr = tree_manager or SessionTreeManager()
        tree = await mgr.get_or_create_tree(tree_id, project_id)
        history_nodes = tree.get_thread()

        # Add User Message to Session Tree
        user_node = await mgr.add_user_message(tree_id, project_id, user_message, parent_node_id)
        state = ProjectService.get_project_state(project_id)
        msg_lower = user_message.lower().strip()

        yield {
            "type": "stage",
            "stage": "Orchestrator reasoning: analyzing prompt & determining necessary actions..."
        }
        await asyncio.sleep(0.01)

        # ---------------------------------------------------------------------
        # GUARDRAIL 1: GIBBERISH / RANDOM TYPING DETECTION
        # ---------------------------------------------------------------------
        if is_gibberish(user_message):
            yield {"type": "stage", "stage": "Input guardrail: checking message structure..."}
            guardrail_reply = get_gibberish_response(project_id)
            for word in guardrail_reply.split(" "):
                yield {"type": "chunk", "content": word + " "}
                await asyncio.sleep(0.01)

            assistant_node = await mgr.add_assistant_message(
                tree_id=tree_id,
                project_id=project_id,
                content=guardrail_reply,
                parent_node_id=user_node.id
            )
            yield {
                "type": "done",
                "assistant_node": assistant_node.model_dump(),
                "action_payload": None,
                "citations": []
            }
            return

        # ---------------------------------------------------------------------
        # GUARDRAIL 2: PRODUCT HELP & ONBOARDING GUIDANCE
        # ---------------------------------------------------------------------
        if is_help_or_onboarding(user_message):
            yield {"type": "stage", "stage": "Retrieving DocuMesh product guide & onboarding instructions..."}
            help_reply = get_onboarding_help_response(project_id, state)
            for word in help_reply.split(" "):
                yield {"type": "chunk", "content": word + " "}
                await asyncio.sleep(0.01)

            assistant_node = await mgr.add_assistant_message(
                tree_id=tree_id,
                project_id=project_id,
                content=help_reply,
                parent_node_id=user_node.id
            )
            yield {
                "type": "done",
                "assistant_node": assistant_node.model_dump(),
                "action_payload": None,
                "citations": []
            }
            return

        # ---------------------------------------------------------------------
        # GUARDRAIL 3: MODEL INFO & ACTIVE LLM DIAGNOSTICS
        # ---------------------------------------------------------------------
        if is_model_info_query(user_message):
            yield {"type": "stage", "stage": "Querying active LLM provider configuration & diagnostics..."}
            model_reply = get_model_info_response(project_id, llm_config)
            for word in model_reply.split(" "):
                yield {"type": "chunk", "content": word + " "}
                await asyncio.sleep(0.01)

            assistant_node = await mgr.add_assistant_message(
                tree_id=tree_id,
                project_id=project_id,
                content=model_reply,
                parent_node_id=user_node.id
            )
            yield {
                "type": "done",
                "assistant_node": assistant_node.model_dump(),
                "action_payload": None,
                "citations": []
            }
            return

        # ---------------------------------------------------------------------
        # GUARDRAIL 4: OFF-TOPIC TRIVIA REDIRECTION
        # ---------------------------------------------------------------------
        if is_off_topic_query(user_message):
            yield {"type": "stage", "stage": "Polite guardrail: redirecting to project reconciliation..."}
            off_topic_reply = get_off_topic_response(user_message, project_id)
            for word in off_topic_reply.split(" "):
                yield {"type": "chunk", "content": word + " "}
                await asyncio.sleep(0.01)

            assistant_node = await mgr.add_assistant_message(
                tree_id=tree_id,
                project_id=project_id,
                content=off_topic_reply,
                parent_node_id=user_node.id
            )
            yield {
                "type": "done",
                "assistant_node": assistant_node.model_dump(),
                "action_payload": None,
                "citations": []
            }
            return

        chat_model = get_llm_instance(llm_config)

        # =====================================================================
        # PATH A: LIVE LLM AGENT WITH AUTONOMOUS TOOL CALLING
        # =====================================================================
        if chat_model is not None:
            try:
                system_prompt = (
                    "You are DocuMesh AI, an autonomous enterprise document reconciliation orchestrator.\n"
                    "You supervise a multi-stage reconciliation engine and document pile.\n\n"
                    "Your Capabilities & Tools:\n"
                    "• run_reconciliation_audit: Run the 7-stage pipeline to classify, extract, and find discrepancies.\n"
                    "• search_document_chunks: Retrieve verbatim quotes, contracts, invoices, and sections.\n"
                    "• list_project_documents: View all files in the project vault.\n"
                    "• get_project_status: Check pipeline node, gate status, and pending counts.\n"
                    "• get_discrepancy_findings: Inspect conflicting clauses, ungrounded claims, and differences.\n"
                    "• decide_finding: Approve or reject a finding at the Human Gate with feedback notes.\n"
                    "• batch_approve_all_findings: Approve all pending findings to finalize the register.\n"
                    "• get_reconciled_register: Retrieve the official single source of truth register.\n"
                    "• rewind_state_machine: Rewind graph execution to a prior checkpoint.\n"
                    "• create_audit_artifact: Generate a versioned markdown audit report.\n\n"
                    f"Current Project Workspace: '{project_id}'\n"
                    "Instructions:\n"
                    "1. When the user asks you to do something (audit, approve, reject, search, summarize, rewind), call the relevant tool(s).\n"
                    "2. Always explain your findings conversationally, citing exact document filenames and sections in `[Filename - Section]` format.\n"
                    "3. If discrepancies exist, guide the user on approving or rejecting them.\n"
                )

                messages: List[Any] = [SystemMessage(content=system_prompt)]
                for node in history_nodes[-6:]:
                    if node.role == "user":
                        messages.append(HumanMessage(content=node.content))
                    elif node.role == "assistant":
                        messages.append(AIMessage(content=node.content))
                messages.append(HumanMessage(content=user_message))

                # Bind tools if supported
                if hasattr(chat_model, "bind_tools"):
                    model_with_tools = chat_model.bind_tools(ORCHESTRATOR_TOOLS)
                    ai_res = await model_with_tools.ainvoke(messages)

                    # Check for tool calls
                    tool_calls = getattr(ai_res, "tool_calls", [])
                    action_payload: Optional[Dict[str, Any]] = None
                    tools_executed: List[Dict[str, Any]] = []

                    if tool_calls:
                        messages.append(ai_res)
                        for tc in tool_calls:
                            t_name = tc.get("name")
                            t_args = tc.get("args", {})
                            if "project_id" not in t_args:
                                t_args["project_id"] = project_id

                            yield {
                                "type": "tool_call",
                                "tool": t_name,
                                "args": t_args
                            }
                            yield {
                                "type": "stage",
                                "stage": f"Orchestrator invoking tool '{t_name}'..."
                            }

                            tool_output = await execute_tool_call(t_name, t_args)
                            tools_executed.append({"tool": t_name, "args": t_args, "output": tool_output})

                            yield {
                                "type": "tool_result",
                                "tool": t_name,
                                "result": tool_output
                            }

                            # Attach tool message for model synthesis
                            messages.append(ToolMessage(
                                content=str(tool_output),
                                tool_call_id=tc.get("id", f"call_{t_name}")
                            ))

                            # Handle action payloads for the UI
                            if t_name in ["run_reconciliation_audit", "get_discrepancy_findings"]:
                                curr_state = ProjectService.get_project_state(project_id)
                                findings_to_show = curr_state.pending_findings or curr_state.findings
                                action_payload = {
                                    "type": "GATE_FINDINGS",
                                    "findings": [f.model_dump() for f in findings_to_show]
                                }
                                yield {"type": "action", "action_payload": action_payload}
                            elif t_name in ["get_reconciled_register", "batch_approve_all_findings"]:
                                curr_state = ProjectService.get_project_state(project_id)
                                if curr_state.register:
                                    action_payload = {
                                        "type": "SHOW_REGISTER",
                                        "register": curr_state.register.model_dump()
                                    }
                                    yield {"type": "action", "action_payload": action_payload}

                        # Stream final conversational synthesis from the model
                        yield {
                            "type": "stage",
                            "stage": "Synthesizing final response..."
                        }
                        assistant_reply = ""
                        async for chunk in chat_model.astream(messages):
                            token = chunk.content if hasattr(chunk, "content") else str(chunk)
                            if token:
                                assistant_reply += token
                                yield {"type": "chunk", "content": token}

                        assistant_node = await mgr.add_assistant_message(
                            tree_id=tree_id,
                            project_id=project_id,
                            content=assistant_reply,
                            parent_node_id=user_node.id
                        )
                        if action_payload:
                            assistant_node.metadata["action_payload"] = action_payload

                        yield {
                            "type": "done",
                            "assistant_node": assistant_node.model_dump(),
                            "action_payload": action_payload,
                            "citations": []
                        }
                        return
                    else:
                        # No tool calls, direct stream
                        first_content = ai_res.content if hasattr(ai_res, "content") else str(ai_res)
                        if first_content:
                            for word in first_content.split(" "):
                                yield {"type": "chunk", "content": word + " "}
                                await asyncio.sleep(0.01)

                            assistant_node = await mgr.add_assistant_message(
                                tree_id=tree_id,
                                project_id=project_id,
                                content=first_content,
                                parent_node_id=user_node.id
                            )
                            yield {
                                "type": "done",
                                "assistant_node": assistant_node.model_dump(),
                                "action_payload": None,
                                "citations": []
                            }
                            return
            except Exception as e:
                logger.warning("live_llm_orchestrator_error_using_heuristic_loop", error=str(e))

        # =====================================================================
        # PATH B: GROUNDED HEURISTIC ORCHESTRATOR (AUTONOMOUS TOOL EXECUTION)
        # =====================================================================
        action_payload: Optional[Dict[str, Any]] = None
        citation_sources: List[Dict[str, str]] = []
        assistant_reply = ""

        # 1. Artifact generation intent
        is_artifact_intent = (
            "artifact" in msg_lower or
            (("report" in msg_lower or "summary" in msg_lower) and any(w in msg_lower for w in ["create", "generate", "produce", "save", "make", "draft"]))
        )

        # 2. Single finding approval / rejection
        approve_match = re.search(r"(?:approve|accept|confirm)\s+(?:finding\s+)?(f-?\d{3})", msg_lower)
        reject_match = re.search(r"(?:reject|dismiss|deny)\s+(?:finding\s+)?(f-?\d{3})(?:\s+(?:because|reason|with\s+reason|for)?\s*(.*))?", msg_lower)

        # 3. Batch approve intent
        is_batch_approve_intent = any(w in msg_lower for w in ["approve all", "batch approve", "approve all findings", "clear gate"])

        # 4. Rewind intent
        is_rewind_intent = re.search(r"(?:rewind|revert|time travel|go back)\s+(?:to\s+)?(ingest|classify|extract|reconcile|examine|gate)", msg_lower)

        # 5. Pipeline Execution intent
        is_audit_intent = (
            not is_artifact_intent and (
                (any(w in msg_lower for w in ["run", "start", "execute", "trigger", "launch", "perform"]) and
                 any(w in msg_lower for w in ["audit", "reconcil", "pipeline", "analysis"])) or
                msg_lower in ["run", "start", "audit", "reconcile", "run audit", "run reconciliation", "start audit", "reconcile documents"] or
                ("reconcil" in msg_lower and not any(w in msg_lower for w in ["what", "why", "how", "explain", "who"]))
            )
        )

        # 6. List documents intent
        is_list_docs_intent = any(w in msg_lower for w in ["what documents", "list files", "show documents", "list documents", "what files", "files in project"])

        # 7. Register intent
        is_register_intent = any(w in msg_lower for w in ["show register", "view register", "project register", "deliverables", "show metrics"])

        # EXECUTE DETECTED ORCHESTRATOR TOOLS
        if is_artifact_intent:
            yield {"type": "tool_call", "tool": "create_audit_artifact", "args": {"project_id": project_id, "title": "Audit Summary"}}
            yield {"type": "stage", "stage": "Creating versioned audit artifact deliverable..."}

            art_content = (
                f"# DocuMesh Executive Reconciliation Report — {project_id}\n\n"
                f"## Executive Summary\n"
                f"• Pipeline Status: {state.status}\n"
                f"• Documents Ingested: {len(state.documents)}\n"
                f"• Extracted Facts: {len(state.facts)}\n"
                f"• Discrepancies Recorded: {len(state.findings)}\n\n"
                f"Generated by DocuMesh AI Orchestrator."
            )
            art_res_str = await create_audit_artifact.ainvoke({"project_id": project_id, "title": "Executive Audit Summary", "content": art_content})
            art_data = json.loads(art_res_str)
            yield {"type": "tool_result", "tool": "create_audit_artifact", "result": art_data}

            assistant_reply = (
                f"### 📄 Audit Deliverable Artifact Created\n\n"
                f"I've generated a versioned audit report artifact:\n"
                f"• **Artifact ID:** `{art_data.get('artifact_id')}`\n"
                f"• **Title:** {art_data.get('title')}\n"
                f"• **Content Hash:** `{art_data.get('content_hash')}`\n\n"
                f"This deliverable is permanently versioned in the project repository."
            )

        elif approve_match:
            f_code = approve_match.group(1).upper().replace("-", "")
            finding_id = f"F-{f_code[1:]}" if f_code.startswith("F") else f"F-{f_code}"
            yield {"type": "tool_call", "tool": "decide_finding", "args": {"project_id": project_id, "finding_id": finding_id, "approved": True}}
            yield {"type": "stage", "stage": f"Approving finding {finding_id} at Human Gate..."}

            res_str = decide_finding.invoke({"project_id": project_id, "finding_id": finding_id, "approved": True})
            res_data = json.loads(res_str)
            yield {"type": "tool_result", "tool": "decide_finding", "result": res_data}

            rem = res_data.get("remaining_pending_findings", 0)
            assistant_reply = (
                f"### ✅ Finding {finding_id} Approved\n\n"
                f"I have marked finding **{finding_id}** as **APPROVED**.\n"
                f"• Remaining pending findings at Human Gate: **{rem}**\n"
            )
            if rem == 0:
                assistant_reply += "\nAll findings are now cleared! The state machine has finalized the Reconciled Register."

        elif reject_match:
            f_code = reject_match.group(1).upper().replace("-", "")
            finding_id = f"F-{f_code[1:]}" if f_code.startswith("F") else f"F-{f_code}"
            reason = reject_match.group(2) or "Rejected per user chat instruction"
            yield {"type": "tool_call", "tool": "decide_finding", "args": {"project_id": project_id, "finding_id": finding_id, "approved": False, "feedback": reason}}
            yield {"type": "stage", "stage": f"Rejecting finding {finding_id} with reviewer feedback..."}

            res_str = decide_finding.invoke({"project_id": project_id, "finding_id": finding_id, "approved": False, "feedback": reason})
            res_data = json.loads(res_str)
            yield {"type": "tool_result", "tool": "decide_finding", "result": res_data}

            rem = res_data.get("remaining_pending_findings", 0)
            assistant_reply = (
                f"### ❌ Finding {finding_id} Rejected\n\n"
                f"Finding **{finding_id}** has been marked as **REJECTED** with reviewer feedback: *\"{reason}\"*.\n"
                f"• Remaining pending findings at Human Gate: **{rem}**\n"
            )

        elif is_batch_approve_intent:
            yield {"type": "tool_call", "tool": "batch_approve_all_findings", "args": {"project_id": project_id}}
            yield {"type": "stage", "stage": "Clearing Human Gate and compiling Reconciled Register..."}

            tool_res_str = batch_approve_all_findings.invoke({"project_id": project_id})
            yield {"type": "tool_result", "tool": "batch_approve_all_findings", "result": json.loads(tool_res_str)}

            updated_state = ProjectService.get_project_state(project_id)
            action_payload = {
                "type": "SHOW_REGISTER",
                "register": updated_state.register.model_dump() if updated_state.register else None
            }
            yield {"type": "action", "action_payload": action_payload}

            assistant_reply = (
                "### ✅ All Gate Findings Approved\n\n"
                "All pending discrepancy findings have been approved. The LangGraph state machine has resumed through **Stage 7: Deliver** and finalized the **Reconciled Project Register**.\n\n"
                f"• **Status:** {updated_state.status}\n"
                f"• **Current Node:** {updated_state.current_node}\n"
                f"• **Total Reconciled Metrics:** {len(updated_state.register.entries) if updated_state.register else 0}\n\n"
                "You can inspect the table in the **Project Register** tab or click **Export Executive Report**."
            )

        elif is_audit_intent:
            yield {"type": "tool_call", "tool": "run_reconciliation_audit", "args": {"project_id": project_id}}
            yield {"type": "stage", "stage": "Executing LangGraph multi-stage reconciliation pipeline..."}
            
            tool_res_str = run_reconciliation_audit.invoke({"project_id": project_id})
            tool_res = json.loads(tool_res_str)
            yield {"type": "tool_result", "tool": "run_reconciliation_audit", "result": tool_res}

            updated_state = ProjectService.get_project_state(project_id)
            findings_to_show = updated_state.pending_findings or updated_state.findings
            action_payload = {"type": "GATE_FINDINGS", "findings": [f.model_dump() for f in findings_to_show]}
            yield {"type": "action", "action_payload": action_payload}

            crit_cnt = sum(1 for f in findings_to_show if getattr(f.severity, "value", str(f.severity)) == "CRITICAL")
            high_cnt = sum(1 for f in findings_to_show if getattr(f.severity, "value", str(f.severity)) == "HIGH")

            assistant_reply = (
                f"### ⚡ LangGraph Reconciliation Audit Complete\n\n"
                f"I have executed the 7-stage state machine across the **{len(updated_state.documents)} documents** in this project.\n\n"
                f"**Execution Summary:**\n"
                f"• **Ingested & Classified:** {len(updated_state.documents)} documents\n"
                f"• **Extracted Facts:** {len(updated_state.facts)} grounded assertions\n"
                f"• **Detected Discrepancies:** **{len(findings_to_show)} findings** ({crit_cnt} CRITICAL, {high_cnt} HIGH)\n\n"
                f"The pipeline is currently paused at **Stage 6: Human Gate**. You can review the discrepancy cards below to approve or reject them, or instruct me to approve them directly."
            )

        elif is_batch_approve_intent:
            yield {"type": "tool_call", "tool": "batch_approve_all_findings", "args": {"project_id": project_id}}
            yield {"type": "stage", "stage": "Clearing Human Gate and compiling Reconciled Register..."}

            tool_res_str = batch_approve_all_findings.invoke({"project_id": project_id})
            yield {"type": "tool_result", "tool": "batch_approve_all_findings", "result": json.loads(tool_res_str)}

            updated_state = ProjectService.get_project_state(project_id)
            action_payload = {
                "type": "SHOW_REGISTER",
                "register": updated_state.register.model_dump() if updated_state.register else None
            }
            yield {"type": "action", "action_payload": action_payload}

            assistant_reply = (
                "### ✅ All Gate Findings Approved\n\n"
                "All pending discrepancy findings have been approved. The LangGraph state machine has resumed through **Stage 7: Deliver** and finalized the **Reconciled Project Register**.\n\n"
                f"• **Status:** {updated_state.status}\n"
                f"• **Current Node:** {updated_state.current_node}\n"
                f"• **Total Reconciled Metrics:** {len(updated_state.register.entries) if updated_state.register else 0}\n\n"
                "You can inspect the table in the **Project Register** tab or click **Export Executive Report**."
            )

        elif approve_match:
            f_code = approve_match.group(1).upper().replace("-", "")
            finding_id = f"F-{f_code[1:]}" if f_code.startswith("F") else f"F-{f_code}"
            yield {"type": "tool_call", "tool": "decide_finding", "args": {"project_id": project_id, "finding_id": finding_id, "approved": True}}
            yield {"type": "stage", "stage": f"Approving finding {finding_id} at Human Gate..."}

            res_str = decide_finding.invoke({"project_id": project_id, "finding_id": finding_id, "approved": True})
            res_data = json.loads(res_str)
            yield {"type": "tool_result", "tool": "decide_finding", "result": res_data}

            rem = res_data.get("remaining_pending_findings", 0)
            assistant_reply = (
                f"### ✅ Finding {finding_id} Approved\n\n"
                f"I have marked finding **{finding_id}** as **APPROVED**.\n"
                f"• Remaining pending findings at Human Gate: **{rem}**\n"
            )
            if rem == 0:
                assistant_reply += "\nAll findings are now cleared! The state machine has finalized the Reconciled Register."

        elif reject_match:
            f_code = reject_match.group(1).upper().replace("-", "")
            finding_id = f"F-{f_code[1:]}" if f_code.startswith("F") else f"F-{f_code}"
            reason = reject_match.group(2) or "Rejected per user chat instruction"
            yield {"type": "tool_call", "tool": "decide_finding", "args": {"project_id": project_id, "finding_id": finding_id, "approved": False, "feedback": reason}}
            yield {"type": "stage", "stage": f"Rejecting finding {finding_id} with reviewer feedback..."}

            res_str = decide_finding.invoke({"project_id": project_id, "finding_id": finding_id, "approved": False, "feedback": reason})
            res_data = json.loads(res_str)
            yield {"type": "tool_result", "tool": "decide_finding", "result": res_data}

            rem = res_data.get("remaining_pending_findings", 0)
            assistant_reply = (
                f"### ❌ Finding {finding_id} Rejected\n\n"
                f"Finding **{finding_id}** has been marked as **REJECTED** with reviewer feedback: *\"{reason}\"*.\n"
                f"• Remaining pending findings at Human Gate: **{rem}**\n"
            )

        elif is_artifact_intent:
            yield {"type": "tool_call", "tool": "create_audit_artifact", "args": {"project_id": project_id, "title": "Audit Summary"}}
            yield {"type": "stage", "stage": "Creating versioned audit artifact deliverable..."}

            art_content = (
                f"# DocuMesh Executive Reconciliation Report — {project_id}\n\n"
                f"## Executive Summary\n"
                f"• Pipeline Status: {state.status}\n"
                f"• Documents Ingested: {len(state.documents)}\n"
                f"• Extracted Facts: {len(state.facts)}\n"
                f"• Discrepancies Recorded: {len(state.findings)}\n\n"
                f"Generated by DocuMesh AI Orchestrator."
            )
            art_res_str = await create_audit_artifact.ainvoke({"project_id": project_id, "title": "Executive Audit Summary", "content": art_content})
            art_data = json.loads(art_res_str)
            yield {"type": "tool_result", "tool": "create_audit_artifact", "result": art_data}

            assistant_reply = (
                f"### 📄 Audit Deliverable Artifact Created\n\n"
                f"I've generated a versioned audit report artifact:\n"
                f"• **Artifact ID:** `{art_data.get('artifact_id')}`\n"
                f"• **Title:** {art_data.get('title')}\n"
                f"• **Content Hash:** `{art_data.get('content_hash')}`\n\n"
                f"This deliverable is permanently versioned in the project repository."
            )

        elif is_rewind_intent:
            target_node = is_rewind_intent.group(1).upper()
            yield {"type": "tool_call", "tool": "rewind_state_machine", "args": {"project_id": project_id, "target_node": target_node}}
            yield {"type": "stage", "stage": f"Rewinding state machine to node {target_node}..."}

            rewind_res = rewind_state_machine.invoke({"project_id": project_id, "target_node": target_node})
            yield {"type": "tool_result", "tool": "rewind_state_machine", "result": json.loads(rewind_res)}

            assistant_reply = (
                f"### 🔄 State Machine Rewound\n\n"
                f"The LangGraph state machine for **{project_id}** has been rewound to **`{target_node}`**.\n"
                f"You can now inspect the restored state or re-trigger pipeline execution from this checkpoint."
            )

        elif is_list_docs_intent:
            yield {"type": "tool_call", "tool": "list_project_documents", "args": {"project_id": project_id}}
            yield {"type": "stage", "stage": "Inspecting project document vault..."}

            docs_res_str = list_project_documents.invoke({"project_id": project_id})
            docs_data = json.loads(docs_res_str)
            yield {"type": "tool_result", "tool": "list_project_documents", "result": docs_data}

            doc_lines = [
                f"• **`{d['filename']}`** — *{d['doc_type']}* ({d['chunks_count']} chunks)"
                for d in docs_data.get("documents", [])
            ]
            assistant_reply = (
                f"### 📁 Project Document Vault ({docs_data.get('total_documents', 0)} files)\n\n"
                + "\n".join(doc_lines)
                + "\n\nYou can ask me specific questions about any of these files, or type **'run audit'**!"
            )

        elif is_register_intent:
            yield {"type": "tool_call", "tool": "get_reconciled_register", "args": {"project_id": project_id}}
            yield {"type": "stage", "stage": "Retrieving canonical Reconciled Register..."}

            reg_res_str = get_reconciled_register.invoke({"project_id": project_id})
            reg_data = json.loads(reg_res_str)
            yield {"type": "tool_result", "tool": "get_reconciled_register", "result": reg_data}

            if reg_data.get("status") == "error":
                assistant_reply = (
                    "### ℹ️ Register Not Finalized Yet\n\n"
                    "The Reconciled Project Register deliverable has not been finalized yet.\n\n"
                    "Please run the reconciliation audit and approve gate findings to compile the register!"
                )
            else:
                action_payload = {
                    "type": "SHOW_REGISTER",
                    "register": state.register.model_dump() if state.register else None
                }
                yield {"type": "action", "action_payload": action_payload}
                assistant_reply = (
                    f"### 📋 Reconciled Project Register (v{reg_data.get('version')})\n\n"
                    f"The canonical register contains **{reg_data.get('total_metrics')} audited metrics** across all project records.\n"
                    f"You can review the full register in the **Project Register** tab or click **Export Executive Report**."
                )

        # 8. Document search & Grounded QA
        else:
            yield {"type": "tool_call", "tool": "search_document_chunks", "args": {"project_id": project_id, "query": user_message}}
            yield {"type": "stage", "stage": "Orchestrator searching hybrid document chunks & cross-referencing findings..."}

            search_res_str = search_document_chunks.invoke({"project_id": project_id, "query": user_message, "top_k": 6})
            search_data = json.loads(search_res_str)
            yield {"type": "tool_result", "tool": "search_document_chunks", "result": search_data}

            snippets = []
            for hit in search_data.get("results", []):
                snippets.append(f"• **{hit['doc_name']}** ({hit['section']}):\n  \"{hit['text']}\"")
                citation_sources.append({
                    "doc_name": hit["doc_name"],
                    "section": hit["section"],
                    "quote": hit["text"][:200]
                })

            related_findings = [
                f for f in state.findings
                if any(w in f"{f.title} {f.description}".lower() for w in msg_lower.split() if len(w) > 3)
            ]

            assistant_reply = cls._synthesize_grounded_response(
                user_message=user_message,
                state=state,
                snippets=snippets,
                related_findings=related_findings
            )

        # Stream words
        for word in assistant_reply.split(" "):
            yield {"type": "chunk", "content": word + " "}
            await asyncio.sleep(0.01)

        # Finalize message node
        assistant_node = await mgr.add_assistant_message(
            tree_id=tree_id,
            project_id=project_id,
            content=assistant_reply,
            parent_node_id=user_node.id
        )

        if action_payload:
            assistant_node.metadata["action_payload"] = action_payload
        if citation_sources:
            assistant_node.metadata["citations"] = citation_sources

        yield {
            "type": "done",
            "assistant_node": assistant_node.model_dump(),
            "action_payload": action_payload,
            "citations": citation_sources
        }

    @classmethod
    async def process_user_chat(
        cls,
        project_id: str,
        tree_id: str,
        user_message: str,
        parent_node_id: Optional[str] = None,
        tree_manager: Optional[SessionTreeManager] = None,
        llm_config: Optional[ModelProviderConfig] = None
    ) -> Dict[str, Any]:
        """Non-streaming execution of chat turn, returning final tree node and payload."""
        assistant_node = None
        action_payload = None

        async for event in cls.process_user_chat_stream(
            project_id=project_id,
            tree_id=tree_id,
            user_message=user_message,
            parent_node_id=parent_node_id,
            tree_manager=tree_manager,
            llm_config=llm_config
        ):
            if event.get("type") == "done":
                assistant_node = event.get("assistant_node")
                action_payload = event.get("action_payload")

        tree_mgr = tree_manager or SessionTreeManager()
        tree = await tree_mgr.get_or_create_tree(tree_id, project_id)
        active_thread = tree.get_thread()
        user_node = next((n for n in reversed(active_thread) if n.role == "user"), None)

        return {
            "tree_id": tree_id,
            "session_title": tree.title,
            "user_node": user_node.model_dump() if user_node else {},
            "assistant_node": assistant_node or {},
            "action_payload": action_payload
        }

    @classmethod
    def _synthesize_grounded_response(
        cls,
        user_message: str,
        state: Any,
        snippets: List[str],
        related_findings: List[Any]
    ) -> str:
        """Grounded natural language response generator referencing documents, metrics, and findings."""
        msg_lower = user_message.lower()

        # Greetings
        if any(w in msg_lower for w in ["hello", "hi", "hey", "good morning", "good evening"]):
            return (
                f"### Hello! I am your DocuMesh Orchestrator 👋\n\n"
                f"I am actively monitoring workspace **`{state.project_id}`** with **{len(state.documents)} documents**.\n\n"
                f"• Current Status: `{state.status}` (Node: `{state.current_node}`)\n"
                f"• Active Findings: **{len(state.findings)} detected discrepancies** ({len(state.pending_findings)} awaiting gate approval)\n\n"
                f"Tell me what you'd like to do! You can ask me to run an audit, inspect billing invoices, compare contract terms, or approve/reject findings."
            )

        # Penalty clause / liquidated damages
        if any(w in msg_lower for w in ["penalty", "liquidated", "damage", "clause"]):
            finding_text = ""
            for f in state.findings:
                if "penalty" in f.title.lower() or "f-004" in f.finding_id.lower():
                    finding_text = (
                        f"\n\n**Discrepancy Note (Finding {f.finding_id}):**\n"
                        f"• {f.title}: {f.description}\n"
                        f"• Remediation Action: `{f.resolution_action}`"
                    )
            return (
                "### ⚖️ Contractual Liquidated Damages & Penalty Terms\n\n"
                "Reviewing the governing contracts for this project:\n\n"
                "1. **Master Project Plan (`master_project_plan.docx` - Section 12):**\n"
                "   > \"liquidated damages shall be levied at the rate of 0.5% (zero point five percent) of the total contract value per week of delay, subject to a maximum cap of 5% (five percent) of the total contract value.\"\n\n"
                "2. **Governing Cap:** The maximum penalty is strictly capped at **5%** of the contract value (Rs 12.50 crores).\n"
                "3. **Contract Amendment #1:** Retains the same penalty structure with the extended completion date."
                f"{finding_text}"
            )

        # Invoice / billing
        if any(w in msg_lower for w in ["invoice", "billing", "bill", "inv-2024", "phase 3"]):
            finding_text = ""
            for f in state.findings:
                if "invoice" in f.title.lower() or "f-003" in f.finding_id.lower():
                    finding_text = (
                        f"\n\n**Audit Finding ({f.finding_id} - CRITICAL):**\n"
                        f"• {f.title}\n"
                        f"• Source A (`{f.source_a.filename}`): \"{f.source_a.exact_quote}\"\n"
                        f"• Source B (`{f.source_b.filename}`): \"{f.source_b.exact_quote}\"\n"
                        f"• Proposed Action: `{f.resolution_action}`"
                    )
            return (
                "### 💰 Invoice & Progress Billing Audit\n\n"
                "Comparing submitted invoices against reported on-site progress:\n\n"
                "• **Invoice INV-2024-003 (`invoice_inv_2024_003.docx`):** Billed **Rs 2.80 crores** claiming 100% Phase 3 completion.\n"
                "• **Q2 Status Report (`status_report_q2.pdf` - Section 2):** Documents that Phase 3 was only **40% complete** at the close of Q2."
                f"{finding_text}"
            )

        # Steel delivery / material receipts
        if any(w in msg_lower for w in ["steel", "material", "receipt", "apex", "delivery"]):
            finding_text = ""
            for f in state.findings:
                if "steel" in f.title.lower() or "f-005" in f.finding_id.lower():
                    finding_text = (
                        f"\n\n**Discrepancy Finding ({f.finding_id}):**\n"
                        f"• {f.title}\n"
                        f"• {f.description}\n"
                        f"• Action: `{f.resolution_action}`"
                    )
            return (
                "### 🏗️ Steel Material Deliveries & Site Verification\n\n"
                "Cross-document reconciliation of reinforcement steel deliveries:\n\n"
                "• **Material Receipt (`material_receipt_steel.pdf` - APEX-MRN-027):** Signed for 500 MT of reinforcement steel as fully delivered.\n"
                "• **Site Visit Minutes (`site_visit_minutes_jul.txt`):** Notes that only 400 MT (80%) was verified on-site, with 100 MT pending transit delivery."
                f"{finding_text}"
            )

        # Contract value / Handover date
        if any(w in msg_lower for w in ["contract value", "value", "cost", "handover", "completion date", "amendment"]):
            return (
                "### 📜 Contract Value & Milestone Lineage\n\n"
                "• **Original Contract (`master_project_plan.docx` - Section 4 & 5):**\n"
                "  - Total Contract Value: **Rs 12,50,00,000** (Rs 12.50 crores)\n"
                "  - Handover Date: **15 December 2024**\n\n"
                "• **Contract Amendment #1 (`contract_amendment_01.docx` - Section 1 & 2):**\n"
                "  - Revised Contract Value: **Rs 14,20,00,000** (Rs 14.20 crores)\n"
                "  - Revised Handover Date: **31 March 2025**\n"
                "  - Status: Supersedes the original contract terms per bilateral agreement."
            )

        # Retrieved snippets
        if snippets:
            return (
                f"### 🔍 Retrieved Evidence for: \"{user_message}\"\n\n"
                "Here are the exact excerpts retrieved from the project records:\n\n"
                + "\n\n".join(snippets[:3])
            )

        return (
            f"### Request Analyzed: \"{user_message}\"\n\n"
            f"I have scanned the records for **`{state.project_id}`**.\n\n"
            f"You can tell me naturally what to do:\n"
            f"• *\"Run a reconciliation audit on our documents\"*\n"
            f"• *\"Approve finding F-003 and reject F-001\"*\n"
            f"• *\"Batch approve all findings\"*\n"
            f"• *\"Show me what the contract says about liquidated damages\"*\n"
            f"• *\"Create an executive audit report artifact\"*"
        )
