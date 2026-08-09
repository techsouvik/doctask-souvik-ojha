# DocuMesh REST API Reference (`v1`)

Welcome to the **DocuMesh Engine** REST API documentation. The API provides complete programmatic control over document ingestion, LangGraph state machine execution, cross-document reconciliation, Human/MCP approval gates, branching conversation trees, and deliverable exports.

---

## 🌐 Base URL & Interactive Docs

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

## 📁 2. Projects API (`/projects`)

### `POST /api/v1/projects`
Create a new project workspace.

**Request Body:**
```json
{
  "project_name": "Greenfield Tech Park",
  "doc_folder": "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
}
```

**Response `200 OK`:**
```json
{
  "project_id": "proj_greenfield_tech_park",
  "status": "created",
  "doc_folder": "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"
}
```

---

### `GET /api/v1/projects`
List active project workspaces for current tenant.

**Response `200 OK`:**
```json
{
  "projects": [
    "proj_greenfield_tech_park"
  ]
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
Query current project pipeline status and checkpoint information.

**Response `200 OK`:**
```json
{
  "project_id": "proj_greenfield_tech_park",
  "status": "AWAITING_HUMAN_GATE",
  "current_node": "GATE",
  "pending_findings_count": 5,
  "register_ready": true
}
```

---

### `GET /api/v1/projects/{project_id}/register`
Retrieve final reconciled Project Register deliverable (requires completing Human Gate first).

**Response `200 OK`:**
```json
{
  "project_id": "proj_greenfield_tech_park",
  "project_name": "Greenfield Tech Park - Phase 1",
  "version": 1,
  "content_hash": "21f21520ee73",
  "entries": [
    {
      "entity_key": "project:total_contract_value",
      "title": "Project Total Contract Value",
      "reconciled_value": "Rs 14,20,00,000",
      "unit": "INR",
      "status": "SUPERSEDED",
      "primary_citation": {
        "doc_id": "contract_amendment_01.docx",
        "filename": "contract_amendment_01.docx",
        "location": "Section 1",
        "exact_quote": "revised from Rs 12,50,00,000 to Rs 14,20,00,000"
      }
    }
  ]
}
```

---

### `GET /api/v1/projects/{project_id}/graph`
Get Knowledge Graph nodes and conflict edges for visualization.

**Response `200 OK`:**
```json
{
  "project_id": "proj_greenfield_tech_park",
  "nodes": [
    {
      "id": "master_project_plan.docx",
      "label": "master_project_plan.docx",
      "type": "DOCUMENT",
      "doc_type": "CONTRACT"
    },
    {
      "id": "F-003",
      "label": "Invoice Bills 100% Phase 3 Completion Against 40% Progress",
      "type": "FINDING",
      "severity": "CRITICAL"
    }
  ],
  "edges": [
    {
      "source": "invoice_inv_2024_003.docx",
      "target": "F-003",
      "label": "SRC_A",
      "is_conflict": true
    }
  ]
}
```

---

### `GET /api/v1/projects/{project_id}/export-report`
Export executive HTML report deliverable.

**Response `200 OK` (`text/html`):** Returns styled HTML report ready for browser view or PDF print.

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
List all detected findings. Query param `status` optional (`PRESENTED`, `APPROVED`, `REJECTED`).

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

**Request Body:**
```json
{
  "approved_all": true
}
```

---

## 💬 5. Sessions & Conversation Trees API (`/projects/{project_id}/sessions`)

### `GET /api/v1/projects/{project_id}/sessions/{tree_id}`
Retrieve the active linear thread for a conversation session.

---

### `POST /api/v1/projects/{project_id}/sessions/{tree_id}/messages`
Post a user message to a conversation session (triggers auto-session-naming).

**Request Body:**
```json
{
  "content": "Please review the penalty clause terms in contract"
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

## 📦 7. Artifacts API (`/projects/{project_id}/artifacts`)

### `POST /api/v1/projects/{project_id}/artifacts`
Create a versioned, content-hashed deliverable artifact.

**Request Body:**
```json
{
  "title": "Executive Summary",
  "content": "# Executive Summary\nReconciled 16 entity metrics across 8 documents.",
  "artifact_type": "markdown"
}
```

---

## 💻 cURL Example Workflows

### Complete End-to-End Workflow via cURL

```bash
# 1. Health Check
curl http://localhost:8000/api/v1/health

# 2. Trigger Pipeline Run
curl -X POST http://localhost:8000/api/v1/projects/proj_greenfield_tech_park/run

# 3. Get Findings
curl http://localhost:8000/api/v1/projects/proj_greenfield_tech_park/findings

# 4. Batch Approve Findings at Gate
curl -X POST http://localhost:8000/api/v1/projects/proj_greenfield_tech_park/findings/batch-approve \
  -H "Content-Type: application/json" \
  -d '{"approved_all": true}'

# 5. Get Reconciled Register
curl http://localhost:8000/api/v1/projects/proj_greenfield_tech_park/register
```
