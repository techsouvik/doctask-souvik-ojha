# DocuMesh REST API Reference (`v1`)

Welcome to the **DocuMesh Engine** REST API documentation. The API provides complete programmatic control over document ingestion, LangGraph state machine execution, cross-document reconciliation, Human/MCP approval gates, branching conversation trees, dynamic skills/playbooks, prompt evaluations, and time-travel state rewind.

---

## 🌐 Base Endpoint & Swagger UI

- **Base Endpoint:** `http://localhost:8000/api/v1`
- **Interactive OpenAPI / Swagger UI:** `http://localhost:8000/docs`
- **ReDoc Interactive UI:** `http://localhost:8000/redoc`

---

## 🔒 Headers & Multi-Tenancy Scoping

Every request supports standard tracing and tenant isolation headers:

| Header | Type | Default | Description |
|--------|------|---------|-------------|
| `X-Tenant-ID` | String | `tenant_default` | Tenant organization ID for database RLS scoping. |
| `X-Project-ID` | String | `proj_greenfield_tech_park` | Target project workspace ID. |
| `X-Correlation-ID` | String | *Auto-generated UUID* | Request tracing ID across services and logs. |

---

## 🏥 1. Health API (`/health`)

### `GET /api/v1/health`
Check system health, database readiness, and Redis cache connection status.

**Response `200 OK`:**
```json
{
  "status": "healthy",
  "app_name": "DocuMesh Engine",
  "version": "1.0.0",
  "redis_cache": "connected",
  "database": "sqlite_active"
}
```

---

## 📁 2. Projects & Time Travel API (`/projects`)

### `POST /api/v1/projects`
Create a new project workspace.

**Request Body:**
```json
{
  "project_name": "Greenfield Tech Park",
  "doc_folder": "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
}
```

---

### `POST /api/v1/projects/{project_id}/run`
Trigger or resume 7-stage LangGraph state machine execution up to the Human/MCP Approval Gate.

**Response `200 OK`:**
```json
{
  "project_id": "proj_greenfield_tech_park",
  "status": "AWAITING_HUMAN_GATE",
  "current_node": "GATE",
  "documents_count": 8,
  "facts_count": 20,
  "findings_count": 5,
  "pending_findings_count": 5
}
```

---

### `GET /api/v1/projects/{project_id}/status`
Query current project pipeline status and checkpointer information.

---

### `GET /api/v1/projects/{project_id}/register`
Retrieve final reconciled Project Register deliverable (requires completing Human Gate first).

---

### `GET /api/v1/projects/{project_id}/history`
Retrieve time-travel checkpoint history across node runs.

**Response `200 OK`:**
```json
{
  "project_id": "proj_greenfield_tech_park",
  "checkpoint_history": [
    { "checkpoint_id": "chk_001", "seq_id": 1, "node_name": "INGEST", "created_at": "2026-08-10T01:00:00Z" },
    { "checkpoint_id": "chk_002", "seq_id": 2, "node_name": "CLASSIFY", "created_at": "2026-08-10T01:00:01Z" },
    { "checkpoint_id": "chk_003", "seq_id": 3, "node_name": "EXTRACT", "created_at": "2026-08-10T01:00:02Z" }
  ]
}
```

---

### `POST /api/v1/projects/{project_id}/rewind`
Rewind state machine back to a prior node checkpoint (Time Travel).

**Request Body:**
```json
{
  "target_node_name": "CLASSIFY"
}
```

---

### `GET /api/v1/projects/{project_id}/timeline`
Get chronological project lineage timeline events.

---

### `GET /api/v1/projects/{project_id}/analytics`
Get stage-by-stage token usage, USD cost, and latency analytics.

---

### `GET /api/v1/projects/{project_id}/graph`
Get Knowledge Graph nodes and conflict edges for visualization.

---

## 📄 3. Documents API (`/projects/{project_id}/documents`)

### `GET /api/v1/projects/{project_id}/documents`
List all documents in the project pile.

---

### `GET /api/v1/projects/{project_id}/documents/{doc_id}`
Get document detail, extracted text, and chunks.

---

### `POST /api/v1/projects/{project_id}/documents`
Upload new document file (`multipart/form-data`) for incremental update.

---

## 🚨 4. Findings & Gate API (`/projects/{project_id}/findings`)

### `GET /api/v1/projects/{project_id}/findings`
List all detected findings. Optional query param `status` (`PRESENTED`, `APPROVED`, `REJECTED`).

---

### `POST /api/v1/projects/{project_id}/findings/approve`
Approve or reject a finding at the Human/MCP Gate.

**Request Body:**
```json
{
  "finding_id": "F-001",
  "approved": true,
  "feedback": "Verified by Site Engineer"
}
```

---

### `POST /api/v1/projects/{project_id}/findings/batch-approve`
Batch approve or reject all pending findings.

---

## 💬 5. Sessions & Chat Engine API (`/projects/{project_id}/sessions`)

### `GET /api/v1/projects/{project_id}/sessions`
List all active chat sessions for a project.

---

### `GET /api/v1/projects/{project_id}/sessions/{tree_id}`
Retrieve the active linear thread for a conversation session.

---

### `POST /api/v1/projects/{project_id}/sessions/{tree_id}/messages`
Send user message and receive document-grounded AI answer with citations.

**Request Body:**
```json
{
  "content": "What is the penalty clause rate in the master project plan?"
}
```

---

### `POST /api/v1/projects/{project_id}/sessions/{tree_id}/branch`
Branch the conversation tree starting from any parent `node_id`.

**Request Body:**
```json
{
  "parent_node_id": "msg_001",
  "content": "Branching into milestone billing analysis"
}
```

---

### `PATCH /api/v1/projects/{project_id}/sessions/{tree_id}`
Rename conversation session title.

---

### `DELETE /api/v1/projects/{project_id}/sessions/{tree_id}`
Delete a chat session.

---

## 🔍 6. Search API (`/projects/{project_id}/search`)

### `POST /api/v1/projects/{project_id}/search`
Sub-30ms Hybrid BM25 & Vector search across all document chunks.

**Request Body:**
```json
{
  "query": "liquidated damages penalty clause",
  "top_k": 3
}
```

---

## 🧠 7. Skills & Playbooks API (`/projects/{project_id}/skills`)

### `GET /api/v1/projects/{project_id}/skills`
List all registered dynamic skills/playbooks.

---

### `POST /api/v1/projects/{project_id}/skills`
Register a new custom skill/playbook dynamically.

**Request Body:**
```json
{
  "name": "Safety Certificate Auditor",
  "description": "Requires certified safety test report for steel deliveries",
  "category": "SAFETY",
  "rule_name": "Missing Safety Certificate Check",
  "finding_title": "Safety Test Certificate Missing",
  "finding_description": "Steel delivery missing certified tensile test report",
  "severity": "HIGH",
  "recommendation": "Obtain ISO certificate before clearance.",
  "resolution_action": "REQUEST_CERTIFICATE: Issue request for safety certificate."
}
```

---

### `DELETE /api/v1/projects/{project_id}/skills/{skill_id}`
Unregister a skill.

---

## 📊 8. Evals & Prompt Optimization API (`/evals`)

### `GET /api/v1/evals`
List benchmark dataset test cases.

---

### `POST /api/v1/evals/run`
Trigger prompt evaluation benchmark across all prompt variants and return winning prompt with scores.

---

## 📦 9. Artifacts API (`/projects/{project_id}/artifacts`)

### `POST /api/v1/projects/{project_id}/artifacts`
Create a versioned deliverable artifact.

---

### `GET /api/v1/projects/{project_id}/artifacts/{artifact_id}`
Retrieve artifact content.
