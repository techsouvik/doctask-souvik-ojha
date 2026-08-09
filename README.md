# DocuMesh Engine — Agentic Document Reconciliation System

**DocuMesh** is an enterprise-grade, production-ready agentic document reconciliation engine. It ingests complex, multi-format document clusters (contracts, status reports, invoices, material receipts, correspondence), extracts grounded facts, cross-references metrics across files, and compiles a single reconciled source of truth with complete audit trails.

---

## Key Capabilities

1. **Document Pile Understanding:** Ingests mixed formats (`.docx`, `.pdf`, `.txt`), classifies document types, extracts structured facts, and verifies 100% quote grounding against source text.
2. **3-Stage Compliance Engine:** Executes multi-pass checks (Internal Arithmetic → Cross-Document Consistency → Contract Rules) to surface financial and operational discrepancies.
3. **Incremental Directory Watcher:** Monitors target folders for new arrivals and updates affected register metrics without re-processing untouched documents.
4. **Human & MCP Approval Gate:** Pauses pipeline execution at risk thresholds. Allows humans (via REST/Web UI) or machine agents (via MCP server) to approve or reject findings before finalizing the register.
5. **Fault Tolerance & Checkpointing:** Built on LangGraph state machines with database state serialization. Process crashes or kills resume seamlessly from the last completed node.

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

### 2. Generate Benchmark Corpus
```bash
python test_data/generate_corpus.py
```

### 3. Run Pipeline via CLI
```bash
PYTHONPATH=. python -m src.cli run
```

### 4. Run Automated Test Suite
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

### Available MCP Tools
- `run_documesh_analysis(project_id, doc_folder)` — Executes analysis pipeline to GATE
- `get_documesh_status(project_id)` — Queries run state and pending findings
- `list_documesh_findings(project_id)` — Retrieves structured findings with citations
- `approve_documesh_finding(project_id, finding_id, approved, feedback)` — Human/MCP Gate decision
- `get_documesh_register(project_id)` — Retrieves final reconciled project register deliverable

---

## 🏛️ System Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  1. INGEST   │ ──► │ 2. CLASSIFY  │ ──► │  3. EXTRACT  │ ──► │ 4. RECONCILE │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                       │
┌──────────────┐     ┌──────────────┐                          ┌───────▼──────┐
│  7. DELIVER  │ ◄── │   6. GATE    │ ◄─────────────────────── │  5. EXAMINE  │
└──────────────┘     └──────────────┘                          └──────────────┘
```

| Node | Function | Fault Tolerance & Resilience |
|------|----------|------------------------------|
| **1. INGEST** | Directory scanner, SHA-256 deduplication, DOCX/PDF/TXT parser, structural chunker. | Idempotent file hashing prevents duplicate ingestion. |
| **2. CLASSIFY** | Hybrid rule & heuristic classifier. Prompt injection security quarantine. | Isolates malicious instructions into quarantine. |
| **3. EXTRACT** | Dual LLM (Gemini/OpenAI) & heuristic fact extractor with quote grounding check. | Rejects ungrounded quotes; falls back cleanly. |
| **4. RECONCILE** | Canonical entity key resolution & audit trail history construction. | Content-hashed versioning. |
| **5. EXAMINE** | 3-stage rule examination engine (Internal → Cross-Doc → Contract). | Preserves existing human/MCP decisions on re-runs. |
| **6. GATE** | Pauses pipeline if pending findings exist. Waits for explicit decision. | Exposes decisions to REST API and MCP tool calls. |
| **7. DELIVER** | Produces final reconciled Project Register deliverable. | Atomic state serialization. |

---

## 📊 Benchmark Corpus & Detected Discrepancies

The engine is validated against the **Greenfield Tech Park — Phase 1** benchmark suite (`test_data/greenfield_tech_park/`) containing 8 multi-party documents and 5 cross-document discrepancies:

1. **F-001 [HIGH]: Q1 Status Report Internal Expenditure Mismatch** — Summary narrative states total expenditure as Rs 3.20 cr, but itemized table sums to Rs 3.50 cr (Rs 30 lakhs discrepancy).
2. **F-002 [MEDIUM]: Q1 Status Report Excavation Quantity Mismatch** — Narrative states 8,500 cum excavation, but table lists 7,200 cum.
3. **F-003 [CRITICAL]: Unearned Progress Billing** — Invoice INV-2024-003 bills Rs 2.80 cr for 100% Phase 3 completion, but Q2 status report (5 weeks prior) reports Phase 3 at 40% complete.
4. **F-004 [LOW]: Non-Existent Contract Term Citation** — Client complaint email asserts a 15% penalty clause, but Master Project Plan §12 defines liquidated damages as 0.5%/week capped at 5%.
5. **F-005 [MEDIUM]: Material Receipt Contradiction** — Material Receipt MRN-2024-027 claims 100% complete steel shipment on April 20, but Q2 status report notes steel delivery was delayed with 70% arrived by end of June.

---

## 🛠️ Key Architectural & Engineering Decisions

1. **Dual LLM & Zero-Key Fallback:**  
   Supports Google Gemini 1.5/3.6 Flash and OpenAI models. Includes a deterministic heuristic extractor for zero-key offline CI runs and automated testing.

2. **Database-Level Multi-Tenancy:**  
   Designed with `project_id` and `tenant_id` scoping and PostgreSQL Row-Level Security (RLS) support to prevent cross-tenant data leakage.

3. **Incremental Register Updating:**  
   Re-evaluates only affected canonical entity keys when a new document is added, keeping processing fast and token costs minimal.

4. **Distributed Locking & Caching:**  
   Uses Redis (with in-memory fallback) for fact caching, session locking, and distributed rate-limiting.

---

## 📄 License

Apache-2.0 License.
