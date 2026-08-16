# SuperDocs Kotlin Multiplatform (KMP) Client — Band S3

A coroutine-first Kotlin Multiplatform (KMP) client library compiled for the **Java Virtual Machine (JVM)** and **Android** from a single unified Kotlin codebase.

---

## 🏛️ Comprehensive SuperDocs API Surface Support

| Domain | SuperDocs Endpoint | Kotlin Client Method | Description |
|---|---|---|---|
| **Auth & Agent** | `POST /v1/agents/signup` | `client.signupAgent(name)` | Headless autonomous agent signup. |
| **Auth & Agent** | `GET /v1/agents/whoami` | `client.getWhoami()` | Query account tier & remaining operations. |
| **Auth & Agent** | `POST /v1/promos/redeem` | `client.redeemPromo(code)` | Redeem promo code (e.g. `BUILDER26`). |
| **Upload & Parse** | `POST /v1/uploads/parse` | `client.uploadDocument(name, bytes)` | Parse `.docx`/`.pdf` to HTML with stable chunk IDs. |
| **Upload & Parse** | `POST /v1/upload_document_base64` | `client.uploadBase64(name, b64)` | Upload base64 encoded document. |
| **Upload & Parse** | `POST /v1/uploads/presign` | `client.presignUpload(name, mime, size)` | Pre-sign S3 URL for large multi-GB files. |
| **Upload & Parse** | `GET /v1/documents/{id}` | `client.getDocument(docId)` | Retrieve document HTML & chunk outline. |
| **Chat & Edit** | `POST /v1/chat` | `client.sendChatInstructionFlow(...)` | Streamed section diffs as Kotlin `Flow`. |
| **Chat & Edit** | `POST /v1/chat/async` | `client.sendChatAsync(...)` | Async job for heavy/long document runs. |
| **Chat & Edit** | `GET /v1/jobs/{job_id}` | `client.getJobStatus(jobId)` | Poll async job status & progress. |
| **Chat & Edit** | `POST /v1/chat/approve` | `client.approveChanges(jobId, chunks)` | Apply approved chunk diffs. |
| **Chat & Edit** | `POST /v1/chat/revert` | `client.revertVersion(sessionId, vId)` | Revert document to prior version ID. |
| **Export** | `POST /v1/export` | `client.exportDocument(docId, format)` | Free export to PDF, DOCX, HTML, MD, TXT. |
| **Export** | `POST /v1/export/email` | `client.emailExport(docId, email)` | Async email export delivery. |
| **Search** | `POST /v1/search` | `client.searchDocuments(query, docId)` | Sub-second hybrid search across document chunks. |

---

## 📱 Android-Specific Integrations

- **WorkManager (`DocumentWorker.kt`):** Background document jobs survive Android app process death and activity recreation.
- **Storage Access Framework (`DocumentProviderAccess.kt`):** Reads files securely via Android `ContentResolver` (`content://` URIs) without legacy storage permissions.
- **Main-Thread Safe:** All network IO pinned strictly to `Dispatchers.IO`.

---

## 🚀 Building & Testing

```bash
# Build JVM and Android AAR artifacts
./gradlew build

# Run unit tests
./gradlew check
```
