package app.superdocs.client.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class DocumentUploadResponse(
    @SerialName("document_id") val documentId: String = "",
    @SerialName("filename") val filename: String = "",
    @SerialName("chunk_count") val chunkCount: Int = 0,
    @SerialName("status") val status: String = "SUCCESS"
)

@Serializable
data class ChatInstructionRequest(
    @SerialName("session_id") val sessionId: String,
    @SerialName("instruction") val instruction: String,
    @SerialName("document_html") val documentHtml: String? = null
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
    @SerialName("job_id") val jobId: String,
    @SerialName("diffs") val diffs: List<ChunkDiff> = emptyList(),
    @SerialName("status") val status: String = "COMPLETED"
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
data class ExportRequest(
    @SerialName("document_id") val documentId: String,
    @SerialName("format") val format: String = "pdf"
)

@Serializable
data class ExportResponse(
    @SerialName("download_url") val downloadUrl: String = "",
    @SerialName("format") val format: String = "pdf",
    @SerialName("bytes_size") val bytesSize: Long = 0L
)
