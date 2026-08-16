package app.superdocs.client

import app.superdocs.client.errors.SuperDocsErrorPayload
import app.superdocs.client.errors.SuperDocsException
import app.superdocs.client.models.*
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.plugins.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.client.request.forms.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json

/**
 * Production Coroutine-First Kotlin Multiplatform Client for SuperDocs API.
 * Implements [ISuperDocsClient] with automatic typed exception handling and Result<T> safe extensions.
 */
class SuperDocsClient(
    private var apiKey: String = "",
    private val baseUrl: String = "https://api.superdocs.app/v1",
    private val httpClient: HttpClient = createDefaultHttpClient()
) : ISuperDocsClient {

    // ========================================================================
    // 1. AUTHENTICATION & ALLOWANCE MANAGEMENT
    // ========================================================================

    override suspend fun signupAgent(name: String, clientType: String): AgentSignupResponse = safeIoCall {
        if (name.isBlank()) throw SuperDocsException.ValidationException("Agent name cannot be blank.")
        val request = AgentSignupRequest(name, clientType)
        val response = httpClient.post("$baseUrl/agents/signup") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        val res: AgentSignupResponse = response.body()
        this@SuperDocsClient.apiKey = res.apiKey
        res
    }

    override suspend fun getWhoami(): AgentWhoamiResponse = safeIoCall {
        val response = httpClient.get("$baseUrl/agents/whoami") {
            applyAuth(apiKey)
        }
        response.body()
    }

    override suspend fun redeemPromo(code: String): PromoRedeemResponse = safeIoCall {
        if (code.isBlank()) throw SuperDocsException.ValidationException("Promo code cannot be blank.")
        val request = PromoRedeemRequest(code)
        val response = httpClient.post("$baseUrl/promos/redeem") {
            applyAuth(apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    // ========================================================================
    // 2. DOCUMENT UPLOAD & PARSING PIPELINE
    // ========================================================================

    override suspend fun uploadDocument(filename: String, fileBytes: ByteArray): DocumentUploadResponse = safeIoCall {
        if (fileBytes.isEmpty()) throw SuperDocsException.ValidationException("File bytes cannot be empty.")
        val response = httpClient.post("$baseUrl/uploads/parse") {
            applyAuth(apiKey)
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

    override suspend fun uploadBase64(filename: String, base64Data: String): DocumentUploadResponse = safeIoCall {
        if (base64Data.isBlank()) throw SuperDocsException.ValidationException("Base64 string cannot be blank.")
        val request = Base64UploadRequest(filename, base64Data)
        val response = httpClient.post("$baseUrl/upload_document_base64") {
            applyAuth(apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    override suspend fun presignUpload(filename: String, mimeType: String, bytesSize: Long): PresignUploadResponse = safeIoCall {
        val request = PresignUploadRequest(filename, mimeType, bytesSize)
        val response = httpClient.post("$baseUrl/uploads/presign") {
            applyAuth(apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    override suspend fun getDocument(documentId: String): DocumentDetailResponse = safeIoCall {
        val response = httpClient.get("$baseUrl/documents/$documentId") {
            applyAuth(apiKey)
        }
        response.body()
    }

    // ========================================================================
    // 3. CHAT, EDIT, & APPROVAL GATES
    // ========================================================================

    override fun sendChatInstructionFlow(
        sessionId: String,
        instruction: String,
        documentHtml: String?,
        modelTier: String
    ): Flow<ChatInstructionResponse> = flow {
        if (instruction.isBlank()) throw SuperDocsException.ValidationException("Instruction cannot be blank.")
        val request = ChatInstructionRequest(sessionId, instruction, documentHtml, modelTier)
        val response: ChatInstructionResponse = safeIoCall {
            httpClient.post("$baseUrl/chat") {
                applyAuth(apiKey)
                contentType(ContentType.Application.Json)
                setBody(request)
            }.body()
        }
        emit(response)
    }.flowOn(Dispatchers.IO)

    override suspend fun sendChatAsync(sessionId: String, instruction: String, documentHtml: String?): AsyncJobResponse = safeIoCall {
        val request = ChatInstructionRequest(sessionId, instruction, documentHtml)
        val response = httpClient.post("$baseUrl/chat/async") {
            applyAuth(apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    override suspend fun getJobStatus(jobId: String): AsyncJobResponse = safeIoCall {
        val response = httpClient.get("$baseUrl/jobs/$jobId") {
            applyAuth(apiKey)
        }
        response.body()
    }

    override suspend fun approveChanges(jobId: String, approvedChunkIds: List<String>): ApprovalResponse = safeIoCall {
        val request = ApprovalRequest(jobId, approvedChunkIds)
        val response = httpClient.post("$baseUrl/chat/approve") {
            applyAuth(apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    override suspend fun revertVersion(sessionId: String, versionId: Int): ApprovalResponse = safeIoCall {
        val request = RevertVersionRequest(sessionId, versionId)
        val response = httpClient.post("$baseUrl/chat/revert") {
            applyAuth(apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    // ========================================================================
    // 4. MULTI-FORMAT EXPORT
    // ========================================================================

    override suspend fun exportDocument(documentId: String, format: String): ExportResponse = safeIoCall {
        val request = ExportRequest(documentId, format)
        val response = httpClient.post("$baseUrl/export") {
            applyAuth(apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    override suspend fun emailExport(documentId: String, email: String, format: String): ExportResponse = safeIoCall {
        val request = EmailExportRequest(documentId, email, format)
        val response = httpClient.post("$baseUrl/export/email") {
            applyAuth(apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    // ========================================================================
    // 5. HYBRID SEARCH
    // ========================================================================

    override suspend fun searchDocuments(query: String, documentId: String?): DocumentSearchResponse = safeIoCall {
        val request = DocumentSearchRequest(query, documentId)
        val response = httpClient.post("$baseUrl/search") {
            applyAuth(apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    // ========================================================================
    // SAFE CALL RUNNERS & KTOR FACTORY
    // ========================================================================

    private suspend inline fun <T> safeIoCall(crossinline block: suspend () -> T): T = withContext(Dispatchers.IO) {
        try {
            block()
        } catch (e: SuperDocsException) {
            throw e
        } catch (e: Exception) {
            throw SuperDocsException.NetworkException(e.message ?: "Unknown IO Exception", e)
        }
    }

    private fun HttpRequestBuilder.applyAuth(key: String) {
        if (key.isNotBlank()) {
            header("Authorization", "Bearer $key")
            header("X-API-Key", key)
        }
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

                // Automatic HTTP Response Validator mapping to typed exceptions
                HttpResponseValidator {
                    validateResponse { response ->
                        val status = response.status.value
                        if (status in 400..599) {
                            val errorBody = try {
                                response.bodyAsText()
                            } catch (_: Exception) {
                                ""
                            }

                            val parsedPayload = try {
                                Json.decodeFromString<SuperDocsErrorPayload>(errorBody)
                            } catch (_: Exception) {
                                null
                            }

                            when (status) {
                                401, 403 -> throw SuperDocsException.AuthenticationException(
                                    message = parsedPayload?.detail ?: parsedPayload?.error ?: "Invalid or unauthorized API key.",
                                    statusCode = status
                                )
                                429 -> throw SuperDocsException.RateLimitException(
                                    message = parsedPayload?.detail ?: "Rate limit or operations allowance exceeded."
                                )
                                else -> throw SuperDocsException.ApiException(
                                    statusCode = status,
                                    errorPayload = parsedPayload,
                                    message = parsedPayload?.detail ?: parsedPayload?.error ?: "HTTP $status error"
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

/**
 * Kotlin Builder DSL for ergonomic SuperDocsClient instantiation.
 */
fun superDocsClient(builder: SuperDocsClientBuilder.() -> Unit): SuperDocsClient {
    return SuperDocsClientBuilder().apply(builder).build()
}

class SuperDocsClientBuilder {
    var apiKey: String = ""
    var baseUrl: String = "https://api.superdocs.app/v1"
    var httpClient: HttpClient? = null

    fun build(): SuperDocsClient {
        return SuperDocsClient(
            apiKey = apiKey,
            baseUrl = baseUrl,
            httpClient = httpClient ?: SuperDocsClient.createDefaultHttpClient()
        )
    }
}
