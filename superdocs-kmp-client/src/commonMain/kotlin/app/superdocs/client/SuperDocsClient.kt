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
    private val apiKey: String,
    private val baseUrl: String = "https://api.superdocs.app/v1",
    private val httpClient: HttpClient = createDefaultHttpClient()
) {

    /**
     * 1. Upload and parse document to SuperDocs HTML with stable chunk IDs.
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
     * 2. Send targeted edit instruction to SuperDocs with Kotlin Flow streaming diffs.
     */
    fun sendChatInstructionFlow(
        sessionId: String,
        instruction: String,
        documentHtml: String? = null
    ): Flow<ChatInstructionResponse> = flow {
        val request = ChatInstructionRequest(sessionId, instruction, documentHtml)
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
     * 3. Approve proposed chunk diffs on SuperDocs.
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
     * 4. Export finished file from SuperDocs (PDF, DOCX, HTML, MD).
     * Note: Exports do not cost operations.
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
