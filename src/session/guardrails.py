"""Input Guardrails, Gibberish Detection, and Product Onboarding Helpers for DocuMesh."""

import re
import math
from typing import Optional, Any
from src.config import settings
from src.llm.models import ModelProviderConfig


def is_gibberish(text: str) -> bool:
    """Detect random keyboard mashing, repeated characters, and non-lexical inputs."""
    s = text.strip()
    if not s:
        return True

    # 1. Repeated single character (e.g. "aaaaa", "11111", ".......", "??????")
    if re.fullmatch(r"(.)\1{4,}", s):
        return True

    # 2. Pure non-alphanumeric punctuation/symbols (e.g. "!@#$%^&*")
    if not re.search(r"[a-zA-Z0-9]", s):
        return True

    # 3. Known single-letter or two-letter random mashes (unless common word like "hi", "ok", "no", "is", "at")
    common_short = {"hi", "ok", "no", "is", "at", "to", "in", "it", "on", "he", "we", "go", "up", "me", "my", "do", "so"}
    alpha_only = re.sub(r"[^a-zA-Z]", "", s).lower()
    if len(alpha_only) <= 2 and alpha_only not in common_short:
        return True

    # 4. Token-level consonant-vowel ratio & keyboard mashing check
    words = re.findall(r"[a-zA-Z]+", s)
    if words:
        vowels = set("aeiouyAEIOUY")
        mashing_count = 0
        for w in words:
            if len(w) >= 5:
                v_count = sum(1 for ch in w if ch in vowels)
                # Words of 5+ chars with zero vowels (e.g. "asdfgh", "zxcvbn", "qwrtyp")
                if v_count == 0:
                    mashing_count += 1
                # Repeating consonant sequences of 5+ (e.g. "bcdfgh")
                elif re.search(r"[bcdfghjklmnpqrstvwxyz]{5,}", w.lower()):
                    mashing_count += 1

        if mashing_count > 0 and (mashing_count / len(words)) >= 0.5:
            return True

    # 5. Shannon entropy check for randomized noise
    if len(s) > 12 and not any(w in s.lower() for w in ["contract", "invoice", "report", "penalty", "steel", "project"]):
        prob = [float(s.count(c)) / len(s) for c in set(s)]
        entropy = -sum(p * math.log2(p) for p in prob)
        # Random keyboard walks tend to have abnormally high entropy without spaces
        if " " not in s and entropy > 3.8 and len(s) > 14:
            return True

    return False


def is_help_or_onboarding(text: str) -> bool:
    """Check if the user is asking for assistance, how the product works, or getting started."""
    s = text.strip().lower()
    patterns = [
        r"^help\b",
        r"^how\s+to\s+use\b",
        r"^how\s+does\s+this\s+work\b",
        r"^what\s+is\s+this\b",
        r"^what\s+is\s+documesh\b",
        r"^what\s+can\s+you\s+do\b",
        r"^what\s+do\s+you\s+do\b",
        r"^explain\s+(?:the\s+)?product\b",
        r"^getting\s+started\b",
        r"^guide\s+me\b",
        r"^who\s+are\s+you\b",
        r"^i\s+don'?t\s+understand\b",
        r"^how\s+do\s+i\b"
    ]
    return any(re.search(p, s) for p in patterns) or s in ["help", "info", "start", "tutorial"]


def is_model_info_query(text: str) -> bool:
    """Check if the user is asking which LLM or AI model is currently active."""
    s = text.strip().lower()
    patterns = [
        r"which\s+model",
        r"what\s+model",
        r"what\s+llm",
        r"which\s+llm",
        r"what\s+ai\s+model",
        r"what\s+are\s+you\s+using",
        r"model\s+you\s+are\s+using",
        r"which\s+model\s+are\s+you\s+using",
        r"what\s+model\s+is\s+this",
        r"active\s+model"
    ]
    return any(re.search(p, s) for p in patterns)


def is_off_topic_query(text: str) -> bool:
    """Check if user query is completely off-topic trivia, jokes, or non-work queries."""
    s = text.strip().lower()
    patterns = [
        r"^tell\s+me\s+a\s+joke\b",
        r"^write\s+a\s+(?:poem|song|story)\s+about\b",
        r"^what\s+is\s+the\s+capital\s+of\b",
        r"^what\s+is\s+the\s+weather\b",
        r"^who\s+won\s+the\b",
        r"^translate\s+.*to\s+(?:french|spanish|german|hindi|chinese)\b"
    ]
    return any(re.search(p, s) for p in patterns)


def get_gibberish_response(project_id: str) -> str:
    """Friendly guardrail reply for nonsense or typo input."""
    clean_name = project_id.replace("proj_", "").replace("_", " ").title()
    return (
        f"### 🤔 I didn't quite catch that!\n\n"
        f"It looks like your message might have contained accidental characters or typos.\n\n"
        f"I am your **DocuMesh Reconciliation Orchestrator** for **{clean_name}**. Here are some things you can ask me to do:\n\n"
        f"• **Audit Document Pile:** Type *\"run reconciliation audit\"* to check contracts, invoices, and reports.\n"
        f"• **Review Discrepancies:** Ask *\"show findings\"* to see detected conflicts and conflicting quotes.\n"
        f"• **Inspect Contracts & Billing:** Ask *\"What is the penalty clause rate?\"* or *\"Verify Invoice INV-2024-003\"*.\n"
        f"• **Approve Decisions:** Type *\"approve finding F-003\"* or *\"batch approve all findings\"*.\n\n"
        f"What would you like to inspect or execute?"
    )


def get_onboarding_help_response(project_id: str, state: Any) -> str:
    """Comprehensive, easy-to-understand product onboarding explainer."""
    clean_name = project_id.replace("proj_", "").replace("_", " ").title()
    doc_count = len(state.documents)
    finding_count = len(state.findings)

    return (
        f"### 🏛️ Welcome to DocuMesh — Product Guide & Overview\n\n"
        f"**DocuMesh** is an **Enterprise Agentic Document Reconciliation System** designed to audit complex clusters of construction and commercial documents.\n\n"
        f"In real-world projects, project managers, contractors, and owners deal with thousands of pages across contracts, amendments, invoices, site minutes, and delivery passes. Figures frequently contradict each other.\n\n"
        f"#### How DocuMesh Works in 4 Steps:\n\n"
        f"1. **📁 Multi-Format Document Ingestion:**\n"
        f"   Upload contracts (`.docx`), status reports (`.pdf`), or site visit logs (`.txt`). DocuMesh classifies each file and verifies 100% quote grounding against source text.\n\n"
        f"2. **⚡ 7-Stage LangGraph State Machine:**\n"
        f"   Runs cyclical passes (`INGEST` → `CLASSIFY` → `EXTRACT` → `RECONCILE` → `EXAMINE` → `GATE` → `DELIVER`) with persistent SQLite checkpoints and time-travel rewind capabilities.\n\n"
        f"3. **⚠️ Automated Discrepancy Detection:**\n"
        f"   Identifies arithmetic mismatches (e.g. Q1 expenditure table vs text), progress over-billing (e.g. Invoice billing 100% when reports state 40%), and contract term contradictions.\n\n"
        f"4. **🛡️ Human-in-the-Loop Gate & Deliverables:**\n"
        f"   Pauses at Stage 6 so you (or machine MCP agents) can approve/reject each finding before compiling the final **Reconciled Project Register** and printable executive audit reports.\n\n"
        f"#### Current Workspace Status for **{clean_name}**:\n"
        f"• **Documents Loaded:** {doc_count} files in vault\n"
        f"• **Pipeline Node:** `{state.current_node}` (Status: `{state.status}`)\n"
        f"• **Active Findings:** {finding_count} detected issues\n\n"
        f"#### Try Asking Me Natural Language Commands:\n"
        f"• *\"Run a reconciliation audit across our documents\"*\n"
        f"• *\"What is the penalty clause rate in the master project plan?\"*\n"
        f"• *\"Why does Invoice INV-2024-003 conflict with the Q2 status report?\"*\n"
        f"• *\"Approve finding F-003 and batch approve the rest\"*\n"
        f"• *\"Show me the reconciled register\"*"
    )


def get_model_info_response(project_id: str, llm_config: Optional[ModelProviderConfig] = None) -> str:
    """Clear explanation of active LLM model, multi-provider support, and offline capabilities."""
    has_key = bool(
        settings.openai_api_key or
        settings.anthropic_api_key or
        settings.gemini_api_key or
        settings.google_api_key or
        (llm_config and llm_config.api_key)
    )
    is_compatible = (
        settings.default_provider == "openai_compatible" or
        bool(settings.openai_base_url) or
        (llm_config and llm_config.base_url)
    )

    current_provider = llm_config.provider_type.value if llm_config else settings.default_provider
    current_model = (llm_config.model_name if llm_config else settings.default_model) or "gemini-3.8-flash"
    base_url = (llm_config.base_url if llm_config else settings.openai_base_url) or "N/A"

    if current_provider == "gemini":
        sdk_note = "Official Google GenAI SDK (`google-genai`)"
    elif current_provider == "anthropic":
        sdk_note = "Anthropic SDK (`langchain-anthropic`)"
    else:
        sdk_note = "OpenAI SDK (`langchain-openai`)"

    if has_key or is_compatible:
        status_msg = (
            f"• **Active Mode:** Live LLM Agent (Real-Time SSE Streaming)\n"
            f"• **Provider:** `{current_provider}`\n"
            f"• **Model ID:** `{current_model}`\n"
            f"• **SDK:** {sdk_note}\n"
            f"• **Base URL / Endpoint:** `{base_url}`"
        )
    else:
        status_msg = (
            f"• **Active Mode:** **Grounded Offline Autonomous Orchestrator** (Deterministic Zero-Key Mode)\n"
            f"• **Default Configured Model:** `{current_model}` (`{current_provider}`)\n"
            f"• **Local Retrieval Engine:** Sub-30ms Hybrid BM25 & Semantic Vector Index over document chunks\n"
            f"• **Status:** Operating 100% offline with zero external API dependencies."
        )

    return (
        f"### 🤖 Active Model & LLM Provider Diagnostics\n\n"
        f"{status_msg}\n\n"
        f"#### Supported Model Providers:\n"
        f"1. **Google Gemini (Active):** `gemini-3.8-flash`, `gemini-2.5-pro`, `gemini-1.5-flash` via `google-genai` SDK\n"
        f"2. **OpenAI Native:** `gpt-4o`, `gpt-4o-mini`, `o1-mini`\n"
        f"3. **Anthropic Claude:** `claude-3-5-sonnet-20241022`, `claude-3-haiku`\n"
        f"4. **Local / OpenAI-Compatible:** Ollama (`http://localhost:11434/v1` with `llama3.2`, `deepseek-r1`, `mistral`), Together AI, OpenRouter, or vLLM.\n\n"
        f"💡 **How to switch models:**\n"
        f"Click the **LLM & Providers** button at the bottom of the sidebar (or call `POST /api/v1/settings/llm`) to configure your API key or local endpoint with live connection testing!"
    )


def get_off_topic_response(user_message: str, project_id: str) -> str:
    """Polite redirection for non-work / off-topic queries."""
    clean_name = project_id.replace("proj_", "").replace("_", " ").title()
    return (
        f"### 📑 Dedicated Project Assistant\n\n"
        f"I am specifically optimized as an **Enterprise Document Reconciliation & Contract Audit Agent** for **{clean_name}**.\n\n"
        f"While I cannot help with general web trivia or casual creative writing, I can:\n"
        f"• Cross-reference contracts and amendments for delay penalty clauses\n"
        f"• Audit progress invoices against site inspection minutes\n"
        f"• Check steel delivery receipts against warehouse store inventories\n"
        f"• Execute the LangGraph reconciliation pipeline and approve Human Gate findings\n\n"
        f"Would you like me to run an audit on **{clean_name}** or explain any active discrepancies?"
    )
