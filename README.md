# DocuMesh Engine — Agentic Document Reconciliation System

**Candidate:** Souvik Ojha (`doctask-souvik-ojha`)  
**Task:** Task 1 — Build an Agentic System (SuperDocs Round 2 Selection Process)  
**Domain:** Construction Project Management (*Greenfield Tech Park — Phase 1*)  
**Architecture:** LangGraph State Machine + FastAPI + PostgreSQL/SQLite + React Review UI + MCP Server  

---

## Executive Overview

Organizations run on piles of related documents (contracts, progress reports, invoices, meeting minutes, material receipts) that describe the same reality but frequently contradict each other. **DocuMesh** is a production-grade agentic document reconciliation engine that owns a construction project document pile end-to-end:

1. **Understands the Pile (Movement 1):** Ingests mixed formats (`.docx`, `.pdf`, `.txt`), classifies each document, extracts facts with exact verbatim citations, and grounds every claim back to source chunks.
2. **Examines (Movement 2):** Runs a 3-stage compliance engine (Internal Arithmetic → Cross-Document Consistency → Contract Rules) to surface discrepancies as structured findings.
3. **Stays Alive (Movement 3):** Monitors watched directories via a file observer. New document arrivals produce targeted incremental register updates without re-processing untouched documents.
4. **Human/MCP Gate:** Findings pause at an approval gate. Humans (via React Review UI) or machine agents (via MCP server) explicitly approve/reject each finding before committing the final register.
5. **Never Bluffs & Never Loses Work:** 100% quote grounding verification against source documents; full LangGraph checkpointing so process crashes resume without losing completed work.

---

## Quickstart (Clone to Running in < 2 Minutes)

### 1. Prerequisites & Environment Setup
```bash
git clone git@github.com:Assessli-tech/doctask-souvik-ojha.git
cd doctask-souvik-ojha

# Create virtualenv and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Generate Test Corpus (8 Real Documents with 5 Planted Errors)
```bash
python test_data/generate_corpus.py
```

### 3. Run Pipeline via CLI
```bash
PYTHONPATH=. python -m src.cli run
```

### 4. Run Automated Offline Test Suite (No API Key Required)
```bash
PYTHONPATH=. pytest tests/ -v
```

---

## 🌐 Running Web Server & React Review UI

Start the FastAPI REST server and open the Human/MCP Review UI in your browser:

```bash
PYTHONPATH=. python -m src.cli serve
```

- **Web UI & Gate Reviewer:** Open [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI / Swagger Docs:** Open [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🤖 Running MCP Server (Machine-Driven Control)

To expose the system as an MCP server for coding agents (Claude Code, Cursor, Codex):

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

## 🏛️ Architecture & LangGraph State Machine

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  1. INGEST   │ ──► │ 2. CLASSIFY  │ ──► │  3. EXTRACT  │ ──► │ 4. RECONCILE │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                       │
┌──────────────┐     ┌──────────────┐                          ┌───────▼──────┐
│  7. DELIVER  │ ◄── │   6. GATE    │ ◄─────────────────────── │  5. EXAMINE  │
└──────────────┘     └──────────────┘                          └──────────────┘
```

| Node | Purpose | Idempotency & Fault Tolerance |
|------|---------|--------------------------------|
| **1. INGEST** | Scans directory, computes SHA-256 hashes, parses DOCX/PDF/TXT, extracts structural chunks. | Deduplicates files by SHA-256 hash. |
| **2. CLASSIFY** | Hybrid rule-based & heuristic classifier. Runs security scanner for prompt injection attacks. | Quarantines malicious documents into `QUARANTINE` state. |
| **3. EXTRACT** | Schema-driven fact extraction. Runs `verify_grounding()` fuzzy string matching against source text. | Rejects ungrounded quotes (Never Bluffs). |
| **4. RECONCILE** | Groups facts by canonical `entity_key`, constructs audit trail history, drafts register. | Content-hashed versioning. |
| **5. EXAMINE** | Runs 3-stage rule examination engine (Internal → Cross-Doc → Contract). | Preserves existing human/MCP decisions on re-runs. |
| **6. GATE** | Pauses pipeline if pending findings exist. Waits for explicit approve/reject decision. | Exposes decisions to UI and MCP tool calls. |
| **7. DELIVER** | Produces final reconciled Project Register deliverable with active approved findings. | Atomic state serialization. |

---

## 🎯 Ground Truth: The 5 Planted Errors in Seed Corpus

The system is evaluated against the 8 documents in `test_data/greenfield_tech_park/` containing 5 planted cross-document contradictions (documented in `test_data/SEED_CORPUS_KEY.md`):

1. **F-001 [HIGH]: Q1 Status Report Internal Arithmetic Mismatch** — Narrative states total expenditure is Rs 3.20 cr, but itemized table sums to Rs 3.50 cr (Rs 30 lakhs discrepancy).
2. **F-002 [MEDIUM]: Q1 Status Report Excavation Quantity Mismatch** — Narrative states 8,500 cum excavation, but data table lists 7,200 cum.
3. **F-003 [CRITICAL]: Invoice Bills 100% Phase 3 vs 40% Reported Progress** — Invoice INV-2024-003 bills Rs 2.80 cr for 100% Phase 3 completion, but Q2 report (5 weeks prior) reports Phase 3 at 40% complete.
4. **F-004 [LOW]: Client Complaint Cites Non-Existent 15% Penalty Clause** — Client complaint email asserts a 15% penalty clause, but Master Project Plan §12 defines liquidated damages as 0.5%/week capped at 5%.
5. **F-005 [MEDIUM]: Material Receipt Claims Complete Delivery Contradicted by Q2 Report** — Receipt MRN-2024-027 claims 100% complete steel shipment on April 20, but Q2 status report (July 8) notes steel delivery was delayed with only 70% arrived by end of June.

---

## 🛠️ Defended Trade-offs & Engineering Decisions

1. **Zero-Key Offline Fallback Extractor:**  
   *Trade-off:* Implemented deterministic heuristic extractors alongside LLM extractors.  
   *Why:* Enables reviewers and automated CI pipelines to execute full test suites without requiring live API keys or spending real money.

2. **Database-Level Multi-Tenancy Architecture:**  
   *Trade-off:* Designed models with `project_id` and `tenant_id` foreign keys and PostgreSQL Row-Level Security (RLS) policies.  
   *Why:* Prevents cross-tenant data leakage at the database engine level rather than relying on application `WHERE` clauses.

3. **Incremental Register Updating:**  
   *Trade-off:* Incremental updates re-evaluate only the affected `entity_key` subset when a new document arrives.  
   *Why:* Keeps update costs proportional to the new document rather than re-running the full 1,000-document corpus.

---

## 📄 License & Attribution

Built for the **SuperDocs Round 2 Selection Process** by Souvik Ojha. All rights reserved.
