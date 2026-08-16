# SuperDocs Kotlin Multiplatform (KMP) Client — Band S3

A coroutine-first Kotlin Multiplatform (KMP) client library compiled for the **Java Virtual Machine (JVM)** and **Android** from a single Kotlin codebase.

---

## 🏛️ Architecture & Features

- **Multiplatform Targets:** `jvm()` + `androidTarget()` compiled with Kotlin 1.9.22
- **Coroutine & Flow First:** All IO network calls execute as non-blocking `suspend` functions on `Dispatchers.IO`, returning Kotlin `Flow` for real-time SSE progress event streaming.
- **Android Platform Specifics:**
  - **WorkManager Integration (`DocumentWorker`):** Background document reconciliation runs survive Android app process death.
  - **Storage Access Framework (`DocumentProviderAccess`):** Safely reads device document files via Android `ContentResolver` (`content://` URIs).

---

## 🛠️ The 4 Core API Operations

1. **Upload Document:** `client.uploadDocument(filename, fileBytes)`
2. **Send Chat Instruction (Flow):** `client.sendChatInstructionFlow(sessionId, instruction)`
3. **Approve Proposed Changes:** `client.approveChanges(jobId, approvedChunkIds)`
4. **Export Finished File:** `client.exportDocument(documentId, format)`

---

## 🚀 Building & Testing

```bash
# Build KMP artifacts for JVM and Android
./gradlew build

# Run commonTest unit test suite
./gradlew check
```
