# Frontend Engineering & UX Integration Guide

Welcome to the **DocuMesh Engine** Frontend Integration Guide. This document specifies how the frontend application (React, Next.js, Vue, Svelte) should interface with the DocuMesh backend API surface and implement enterprise-grade UX components.

---

## 🏛️ Architecture & API Configuration

- **Backend Base URL:** `http://localhost:8000/api/v1`
- **Swagger Interactive Docs:** `http://localhost:8000/docs`
- **Multi-Tenancy Headers:**
  - `X-Tenant-ID`: Current tenant/organization ID (default: `tenant_default`)
  - `X-Project-ID`: Current project workspace ID (default: `proj_greenfield_tech_park`)

---

## 🎨 Recommended UI Component Layout

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  DocuMesh Engine Header — Project: Greenfield Tech Park | Status: AWAITING_GATE │
├─────────────────────────┬───────────────────────────────────┬───────────────────┤
│  Pipeline Stepper       │  Human/MCP Gate Findings          │  Knowledge Graph  │
│  [1. Ingest] -> [2...]  │  • Card 1: F-003 [CRITICAL]       │  Nodes & Edges    │
│  • Time Travel Slider   │    Source A vs Source B Diffs     │  Visual Network   │
│  • Rewind to Node       │    [Approve]  [Reject]          │  (Cytoscape.js)   │
├─────────────────────────┼───────────────────────────────────┴───────────────────┤
│  Document Pile List     │  Reconciled Project Register      [Export PDF/HTML]  │
│  • 8 Files (DOCX, PDF)  │  Metric | Value | Status | Citation               │
├─────────────────────────┴───────────────────────────────────────────────────────┤
│  Document-Aware Chat Thread (Tree Branching Supported)                          │
│  User: What is the penalty clause? -> AI: 0.5%/week (Master Plan §12) [Branch] │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Key UI Components & Integration Specifications

### 1. LangGraph State Machine Stepper Component
Render the 7 pipeline nodes: `INGEST` → `CLASSIFY` → `EXTRACT` → `RECONCILE` → `EXAMINE` → `GATE` → `DELIVER`.

* **API Call:** `GET /api/v1/projects/{project_id}/status`
* **UX Specification:**
  - Highlight current node in blue (`IN_PROGRESS`).
  - Highlight completed nodes in green.
  - Highlight `GATE` node in orange when status is `AWAITING_HUMAN_GATE`.

---

### 2. Time Travel & State Rewind Component
Allows users to rewind graph execution back to any prior completed node (e.g. back to `CLASSIFY` or `EXTRACT`) to re-evaluate state.

* **API Calls:**
  - Get Checkpoints History: `GET /api/v1/projects/{project_id}/history`
  - Execute Rewind: `POST /api/v1/projects/{project_id}/rewind`
* **TypeScript Call Example:**
```typescript
async function rewindToNode(projectId: string, nodeName: string) {
  const res = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/rewind`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_node_name: nodeName })
  });
  return await res.json();
}
```

---

### 3. Human Gate Findings Cards & Side-by-Side Visual Diffs
When status is `AWAITING_HUMAN_GATE`, render a card for each pending finding.

* **API Calls:**
  - Get Findings: `GET /api/v1/projects/{project_id}/findings?status=PRESENTED`
  - Single Approve/Reject: `POST /api/v1/projects/{project_id}/findings/approve`
  - Batch Approve: `POST /api/v1/projects/{project_id}/findings/batch-approve`
* **UX Specification:**
  - **Severity Badges:** Red (`CRITICAL`), Amber (`HIGH`), Blue (`MEDIUM`), Gray (`LOW`).
  - **Side-by-Side Quote Diff:**
    - Left Column: `source_a.filename` + `source_a.location` + verbatim quote.
    - Right Column: `source_b.filename` + `source_b.location` + verbatim quote.
  - **AI Resolution Action Box:** Highlight the proposed remediation (e.g., `"ISSUE_CREDIT_NOTE: Rs 1.68 crores"`).
  - **Actions:** Green **Approve** button, Red **Reject** button, and text input for reviewer feedback.

---

### 4. Interactive Knowledge Graph Visualizer
Render the document pile and conflict network using Cytoscape.js or Vis.js.

* **API Call:** `GET /api/v1/projects/{project_id}/graph`
* **Response Data:** Nodes (documents, findings) and edges (`is_conflict: true`).
* **UX Specification:** Render document nodes in dark blue and findings in colored circles. Highlight conflict edges in flashing red. Clicking a red edge opens the corresponding finding card modal!

---

### 5. Document-Aware Chat & Branching Conversation Trees
Render the document Q&A chat interface supporting thread branching.

* **API Calls:**
  - Send Message: `POST /api/v1/projects/{project_id}/sessions/{tree_id}/messages`
  - Branch Conversation: `POST /api/v1/projects/{project_id}/sessions/{tree_id}/branch`
  - Get Active Thread: `GET /api/v1/projects/{project_id}/sessions/{tree_id}`
* **UX Specification:**
  - Display citations in expandable pills under assistant messages (`• [master_project_plan.docx - Section 12]`).
  - Add a **"Branch Thread"** button on every message node allowing the user to spawn an alternative conversation branch without losing the main thread history.

---

### 6. Reconciled Project Register & Deliverable Export
Render the audited Project Register table.

* **API Calls:**
  - Get Register JSON: `GET /api/v1/projects/{project_id}/register`
  - Export Executive HTML: `GET /api/v1/projects/{project_id}/export-report`
* **UX Specification:**
  - Status Pills: Green (`CORROBORATED`), Amber (`CONTRADICTED`), Purple (`SUPERSEDED`).
  - Include a **"Download Executive Report"** button that opens `GET /export-report` in a new tab for printing or PDF save.
