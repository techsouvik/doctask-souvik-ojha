package app.superdocs.client

import app.superdocs.client.models.*
import kotlinx.coroutines.flow.Flow

/**
 * Public interface contract for SuperDocs Kotlin Multiplatform SDK.
 * Enables clean dependency injection (Koin, Dagger/Hilt) and test mocking.
 */
interface ISuperDocsClient {

    // Auth & Account
    suspend fun signupAgent(name: String, clientType: String = "kotlin_kmp_client"): AgentSignupResponse
    suspend fun getWhoami(): AgentWhoamiResponse
    suspend fun redeemPromo(code: String): PromoRedeemResponse

    // Uploads
    suspend fun uploadDocument(filename: String, fileBytes: ByteArray): DocumentUploadResponse
    suspend fun uploadBase64(filename: String, base64Data: String): DocumentUploadResponse
    suspend fun presignUpload(filename: String, mimeType: String, bytesSize: Long): PresignUploadResponse
    suspend fun getDocument(documentId: String): DocumentDetailResponse

    // Chat & Edit
    fun sendChatInstructionFlow(
        sessionId: String,
        instruction: String,
        documentHtml: String? = null,
        modelTier: String = "deep"
    ): Flow<ChatInstructionResponse>

    suspend fun sendChatAsync(sessionId: String, instruction: String, documentHtml: String? = null): AsyncJobResponse
    suspend fun getJobStatus(jobId: String): AsyncJobResponse
    suspend fun approveChanges(jobId: String, approvedChunkIds: List<String>): ApprovalResponse
    suspend fun revertVersion(sessionId: String, versionId: Int): ApprovalResponse

    // Export & Search
    suspend fun exportDocument(documentId: String, format: String = "pdf"): ExportResponse
    suspend fun emailExport(documentId: String, email: String, format: String = "pdf"): ExportResponse
    suspend fun searchDocuments(query: String, documentId: String? = null): DocumentSearchResponse
}
