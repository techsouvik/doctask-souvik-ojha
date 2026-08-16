package app.superdocs.client.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// --- AUTH & AGENT MANAGEMENT ---
@Serializable
data class AgentSignupRequest(
    @SerialName("name") val name: String,
    @SerialName("client_type") val clientType: String = "kotlin_kmp_client"
)

@Serializable
data class AgentSignupResponse(
    @SerialName("api_key") val apiKey: String,
    @SerialName("account_id") val accountId: String,
    @SerialName("operations_remaining") val operationsRemaining: Int = 1000
)

@Serializable
data class AgentWhoamiResponse(
    @SerialName("account_id") val accountId: String,
    @SerialName("tier") val tier: String = "developer",
    @SerialName("operations_remaining") val operationsRemaining: Int = 0
)

@Serializable
data class PromoRedeemRequest(
    @SerialName("code") val code: String
)

@Serializable
data class PromoRedeemResponse(
    @SerialName("status") val status: String = "SUCCESS",
    @SerialName("operations_added") val operationsAdded: Int = 10000
)

// --- UPLOAD & PARSING ---
@Serializable
data class Base64UploadRequest(
    @SerialName("filename") val filename: String,
    @SerialName("base64_data") val base64Data: String
)

@Serializable
data class PresignUploadRequest(
    @SerialName("filename") val filename: String,
    @SerialName("mime_type") val mimeType: String,
    @SerialName("bytes_size") val bytesSize: Long
)

@Serializable
data class PresignUploadResponse(
    @SerialName("upload_url") val uploadUrl: String,
    @SerialName("document_id") val documentId: String
)

@Serializable
data class DocumentUploadResponse(
    @SerialName("document_id") val documentId: String = "",
    @SerialName("filename") val filename: String = "",
    @SerialName("chunk_count") val chunkCount: Int = 0,
    @SerialName("status") val status: String = "SUCCESS",
    @SerialName("headings") val headings: List<String> = emptyList()
)

@Serializable
data class DocumentDetailResponse(
    @SerialName("document_id") val documentId: String,
    @SerialName("filename") val filename: String,
    @SerialName("html_content") val htmlContent: String = "",
    @SerialName("version") val version: Int = 1
)

// --- CHAT & EDIT ---
@Serializable
data class ChatInstructionRequest(
    @SerialName("session_id") val sessionId: String,
    @SerialName("instruction") val instruction: String,
    @SerialName("document_html") val documentHtml: String? = null,
    @SerialName("model_tier") val modelTier: String = "deep"
)

@Serializable
data class ChunkDiff(
    @SerialName("chunk_id") val chunkId: String,
    @SerialName("old_html") val oldHtml: String = "",
    @SerialName("new_html") val newHtml: String = "",
    @SerialName("explanation") val explanation: String = ""
)

@Serializable
data class ChatInstructionResponse(
    @SerialName("job_id") val jobId: String = "",
    @SerialName("diffs") val diffs: List<ChunkDiff> = emptyList(),
    @SerialName("status") val status: String = "COMPLETED"
)

@Serializable
data class AsyncJobResponse(
    @SerialName("job_id") val jobId: String,
    @SerialName("status") val status: String, // PROCESSING, COMPLETED, FAILED
    @SerialName("progress_pct") val progressPct: Int = 0,
    @SerialName("result") val result: ChatInstructionResponse? = null
)

@Serializable
data class ApprovalRequest(
    @SerialName("job_id") val jobId: String,
    @SerialName("approved_chunk_ids") val approvedChunkIds: List<String>
)

@Serializable
data class ApprovalResponse(
    @SerialName("document_id") val documentId: String,
    @SerialName("status") val status: String = "APPROVED"
)

@Serializable
data class RevertVersionRequest(
    @SerialName("session_id") val sessionId: String,
    @SerialName("version_id") val versionId: Int
)

// --- EXPORT ---
@Serializable
data class ExportRequest(
    @SerialName("document_id") val documentId: String,
    @SerialName("format") val format: String = "pdf" // pdf, docx, html, md, txt
)

@Serializable
data class ExportResponse(
    @SerialName("download_url") val downloadUrl: String = "",
    @SerialName("format") val format: String = "pdf",
    @SerialName("bytes_size") val bytesSize: Long = 0L
)

@Serializable
data class EmailExportRequest(
    @SerialName("document_id") val documentId: String,
    @SerialName("email") val email: String,
    @SerialName("format") val format: String = "pdf"
)

// --- SEARCH & MEMORY ---
@Serializable
data class DocumentSearchRequest(
    @SerialName("query") val query: String,
    @SerialName("document_id") val documentId: String? = null
)

@Serializable
data class SearchHit(
    @SerialName("chunk_id") val chunkId: String,
    @SerialName("text") val text: String,
    @SerialName("score") val score: Float
)

@Serializable
data class DocumentSearchResponse(
    @SerialName("hits") val hits: List<SearchHit> = emptyList()
)
