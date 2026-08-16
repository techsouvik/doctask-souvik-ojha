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
    private val baseUrl: String = "http://localhost:8000/api/v1",
    private val httpClient: HttpClient = createDefaultHttpClient()
) {

    /** 1. Upload Document */
    suspend fun uploadDocument(filename: String, fileBytes: ByteArray): DocumentUploadResponse = withContext(Dispatchers.IO) {
        val response = httpClient.post("$baseUrl/projects/proj_default/documents") {
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

    /** 2. Send Chat Instruction with Kotlin Flow Streaming Events */
    fun sendChatInstructionFlow(sessionId: String, instruction: String, documentHtml: String? = null): Flow<ChatInstructionResponse> = flow {
        val request = ChatInstructionRequest(sessionId, instruction, documentHtml)
        // Stream progress event
        val response: ChatInstructionResponse = withContext(Dispatchers.IO) {
            httpClient.post("$baseUrl/projects/proj_default/sessions/$sessionId/messages") {
                header("X-API-Key", apiKey)
                contentType(ContentType.Application.Json)
                setBody(request)
            }.body()
        }
        emit(response)
    }.flowOn(Dispatchers.IO)

    /** 3. Approve Proposed Changes */
    suspend fun approveChanges(jobId: String, approvedChunkIds: List<String>): ApprovalResponse = withContext(Dispatchers.IO) {
        val request = ApprovalRequest(jobId, approvedChunkIds)
        val response = httpClient.post("$baseUrl/projects/proj_default/findings/approve") {
            header("X-API-Key", apiKey)
            contentType(ContentType.Application.Json)
            setBody(request)
        }
        response.body()
    }

    /** 4. Export Finished File */
    suspend fun exportDocument(documentId: String, format: String = "pdf"): ExportResponse = withContext(Dispatchers.IO) {
        val request = ExportRequest(documentId, format)
        val response = httpClient.post("$baseUrl/projects/proj_default/artifacts") {
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
                    })
                }
            }
        }
    }
}
