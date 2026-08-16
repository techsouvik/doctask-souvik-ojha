package app.superdocs.client

import app.superdocs.client.models.*
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.client.request.forms.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json

class SuperDocsClient(
    private var apiKey: String = "",
    private val baseUrl: String = "https://api.superdocs.app/v1",
    private val httpClient: HttpClient = createDefaultHttpClient()
) {

    // ========================================================================
    // 1. AGENT AUTHENTICATION & ALLOWANCE MANAGEMENT
    // ========================================================================

    /**
     * Headless autonomous agent signup.
     */
    suspend fun signupAgent(name: String, clientType: String = "kotlin_kmp_client"): AgentSignupResponse = withContext(Dispatchers.IO) {
        val request = AgentSignupRequest(name, clientType)
        val response = httpClient.post("$baseUrl/agents/signup") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        val res: AgentSignupResponse = response.body()
        this@SuperDocsClient.apiKey = res.apiKey
        res
    }

    /**
     * Query account details, tier, and remaining operations allowance.
     */
    suspend fun getWhoami(): AgentWhoamiResponse = withContext(Dispatchers.IO) {
        val response = httpClient.get("$baseUrl/agents/whoami") {
            header("Authorization", "Bearer $apiKey")
            header("X-API-Key", apiKey)
        }
        response.body()
    }

    /**
     * Redeem builder promo code (e.g. BUILDER26 for 10,000 free operations).
     */
    suspend fun redeemPromo(code: String): PromoRedeemResponse = withContext(Dispatchers.IO) {
        val request = PromoRedeemRequest(code)
        val response = httpClient.post("$baseUrl/promos/redeem") {
            header("Authorization", "Bearer $apiKey")
            header("X-API-Key", apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    // ========================================================================
    // 2. DOCUMENT UPLOAD & PARSING PIPELINE
    // ========================================================================

    /**
     * Direct multi-part document upload & parse into structured HTML with stable chunk IDs.
     */
    suspend fun uploadDocument(filename: String, fileBytes: ByteArray): DocumentUploadResponse = withContext(Dispatchers.IO) {
        val response = httpClient.post("$baseUrl/uploads/parse") {
            header("Authorization", "Bearer $apiKey")
            header("X-API-Key", apiKey)
            setBody(MultiPartFormDataContent(
                formData {
                    append("file", fileBytes, Headers.build {
                        append(HttpHeaders.ContentDisposition, "filename=\"$filename\"")
                    })
                }
            ))
        }
        response.body()
    }

    /**
     * Base64 document upload.
     */
    suspend fun uploadBase64(filename: String, base64Data: String): DocumentUploadResponse = withContext(Dispatchers.IO) {
        val request = Base64UploadRequest(filename, base64Data)
        val response = httpClient.post("$baseUrl/upload_document_base64") {
            header("Authorization", "Bearer $apiKey")
            header("X-API-Key", apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    /**
     * Pre-sign S3 URL for large multi-gigabyte files.
     */
    suspend fun presignUpload(filename: String, mimeType: String, bytesSize: Long): PresignUploadResponse = withContext(Dispatchers.IO) {
        val request = PresignUploadRequest(filename, mimeType, bytesSize)
        val response = httpClient.post("$baseUrl/uploads/presign") {
            header("Authorization", "Bearer $apiKey")
            header("X-API-Key", apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    /**
     * Retrieve document details & current HTML chunk tree.
     */
    suspend fun getDocument(documentId: String): DocumentDetailResponse = withContext(Dispatchers.IO) {
        val response = httpClient.get("$baseUrl/documents/$documentId") {
            header("Authorization", "Bearer $apiKey")
            header("X-API-Key", apiKey)
        }
        response.body()
    }

    // ========================================================================
    // 3. CHAT, REWRITING, & APPROVAL GATES
    // ========================================================================

    /**
     * Synchronous Chat Edit with real-time Kotlin Flow streaming.
     */
    fun sendChatInstructionFlow(
        sessionId: String,
        instruction: String,
        documentHtml: String? = null,
        modelTier: String = "deep"
    ): Flow<ChatInstructionResponse> = flow {
        val request = ChatInstructionRequest(sessionId, instruction, documentHtml, modelTier)
        val response: ChatInstructionResponse = withContext(Dispatchers.IO) {
            httpClient.post("$baseUrl/chat") {
                header("Authorization", "Bearer $apiKey")
                header("X-API-Key", apiKey)
                contentType(ContentType.Application.Json)
                setBody(request)
            }.body()
        }
        emit(response)
    }.flowOn(Dispatchers.IO)

    /**
     * Async Job execution for heavy long-running document runs.
     */
    suspend fun sendChatAsync(sessionId: String, instruction: String, documentHtml: String? = null): AsyncJobResponse = withContext(Dispatchers.IO) {
        val request = ChatInstructionRequest(sessionId, instruction, documentHtml)
        val response = httpClient.post("$baseUrl/chat/async") {
            header("Authorization", "Bearer $apiKey")
            header("X-API-Key", apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    /**
     * Poll async job status.
     */
    suspend fun getJobStatus(jobId: String): AsyncJobResponse = withContext(Dispatchers.IO) {
        val response = httpClient.get("$baseUrl/jobs/$jobId") {
            header("Authorization", "Bearer $apiKey")
            header("X-API-Key", apiKey)
        }
        response.body()
    }

    /**
     * Approve proposed chunk diffs.
     */
    suspend fun approveChanges(jobId: String, approvedChunkIds: List<String>): ApprovalResponse = withContext(Dispatchers.IO) {
        val request = ApprovalRequest(jobId, approvedChunkIds)
        val response = httpClient.post("$baseUrl/chat/approve") {
            header("Authorization", "Bearer $apiKey")
            header("X-API-Key", apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    /**
     * Revert document state to a prior version ID.
     */
    suspend fun revertVersion(sessionId: String, versionId: Int): ApprovalResponse = withContext(Dispatchers.IO) {
        val request = RevertVersionRequest(sessionId, versionId)
        val response = httpClient.post("$baseUrl/chat/revert") {
            header("Authorization", "Bearer $apiKey")
            header("X-API-Key", apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    // ========================================================================
    // 4. MULTI-FORMAT EXPORT ENGINE
    // ========================================================================

    /**
     * Export document into PDF, DOCX, HTML, MD, or TXT. (Exports never cost operations)
     */
    suspend fun exportDocument(documentId: String, format: String = "pdf"): ExportResponse = withContext(Dispatchers.IO) {
        val request = ExportRequest(documentId, format)
        val response = httpClient.post("$baseUrl/export") {
            header("Authorization", "Bearer $apiKey")
            header("X-API-Key", apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    /**
     * Export document and deliver asynchronously via email.
     */
    suspend fun emailExport(documentId: String, email: String, format: String = "pdf"): ExportResponse = withContext(Dispatchers.IO) {
        val request = EmailExportRequest(documentId, email, format)
        val response = httpClient.post("$baseUrl/export/email") {
            header("Authorization", "Bearer $apiKey")
            header("X-API-Key", apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    // ========================================================================
    // 5. HYBRID SEARCH & RETRIEVAL
    // ========================================================================

    /**
     * Search across document chunks or session history.
     */
    suspend fun searchDocuments(query: String, documentId: String? = null): DocumentSearchResponse = withContext(Dispatchers.IO) {
        val request = DocumentSearchRequest(query, documentId)
        val response = httpClient.post("$baseUrl/search") {
            header("Authorization", "Bearer $apiKey")
            header("X-API-Key", apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    companion object {
        fun createDefaultHttpClient(): HttpClient {
            return HttpClient {
                install(ContentNegotiation) {
                    json(Json {
                        ignoreUnknownKeys = true
                        prettyPrint = true
                        encodeDefaults = true
                    })
                }
            }
        }
    }
}
