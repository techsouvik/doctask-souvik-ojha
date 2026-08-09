# DocuMesh Engine — Agentic Document Reconciliation System

**DocuMesh** is an enterprise-grade, production-ready agentic document reconciliation engine. It ingests complex, multi-format document clusters (contracts, status reports, invoices, material receipts, correspondence), extracts grounded facts, cross-references metrics across files, and compiles a single reconciled source of truth with complete audit trails.

---

## Key Capabilities

1. **Multi-Provider LLM & Custom Base URL Support:** Native support for OpenAI (`gpt-4o`), Anthropic Claude (`claude-3-5-sonnet`), Google Gemini (`gemini-1.5-flash`), and any custom OpenAI-compatible endpoint (`OPENAI_BASE_URL` for Together, Ollama, OpenRouter, or local vLLM).
2. **Document Pile Understanding:** Ingests mixed formats (`.docx`, `.pdf`, `.txt`), classifies document types, extracts structured facts, and verifies 100% quote grounding against source text.
3. **3-Stage Compliance Engine:** Executes multi-pass checks (Internal Arithmetic → Cross-Document Consistency → Contract Rules) to surface financial and operational discrepancies.
4. **Incremental Directory Watcher:** Monitors target folders for new arrivals and updates affected register metrics without re-processing untouched documents.
5. **Human & MCP Approval Gate:** Pauses pipeline execution at risk thresholds. Allows humans (via REST/Web UI) or machine agents (via MCP server) to approve or reject findings before finalizing the register.
6. **LangGraph v1.2+ Time Travel & Checkpointing:** Built on LangGraph state machines with database state serialization. Enables rewinding state machine runs back to any prior node (`/api/v1/projects/{id}/rewind`).

---

## ⚡ Quickstart (Clone to Running in < 2 Minutes)

### 1. Environment Setup
```bash
git clone git@github.com:techsouvik/doctask.git
cd doctask

# Create virtualenv and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure LLM Providers (Optional `.env`)
```bash
# OpenAI Native
OPENAI_API_KEY="sk-..."

# Custom OpenAI-Compatible Endpoint (Together, OpenRouter, Ollama, vLLM)
OPENAI_BASE_URL="http://localhost:11434/v1"

# Anthropic Claude Native
ANTHROPIC_API_KEY="sk-ant-..."

# Google Gemini Native
GEMINI_API_KEY="AIza..."
```

### 3. Generate Benchmark Corpus
```bash
python test_data/generate_corpus.py
```

### 4. Run Pipeline via CLI
```bash
PYTHONPATH=. python -m src.cli run
```

### 5. Run Automated Test Suite
```bash
PYTHONPATH=. pytest tests/ -v
```

---

## 🐳 Docker Infrastructure Setup

Launch PostgreSQL (with `pgvector`) and Redis cache services using Docker Compose:

```bash
docker-compose up -d
```

---

## 🌐 Running Web Server & API

Start the FastAPI REST server:

```bash
PYTHONPATH=. python -m src.cli serve
```

- **REST API Endpoint:** [http://localhost:8000/api/v1](http://localhost:8000/api/v1)
- **Interactive OpenAPI / Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🤖 Running MCP Server (Machine-Driven Control)

To expose the system as a Model Context Protocol (MCP) server for coding agents (Claude Code, Cursor, Codex):

```bash
PYTHONPATH=. python -m src.cli mcp
```

---

## 📄 License

Apache-2.0 License.
