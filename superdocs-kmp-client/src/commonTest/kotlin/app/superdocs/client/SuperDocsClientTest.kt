package app.superdocs.client

import app.superdocs.client.models.*
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull

class SuperDocsClientTest {

    @Test
    fun testAllSuperDocsApiModelsSerialization() {
        // 1. Auth & Agent Signup
        val signup = AgentSignupResponse(apiKey = "sk_agent_123", accountId = "acc_001", operationsRemaining = 1000)
        val signupJson = Json.encodeToString(AgentSignupResponse.serializer(), signup)
        assertEquals("sk_agent_123", Json.decodeFromString(AgentSignupResponse.serializer(), signupJson).apiKey)

        // 2. Whoami
        val whoami = AgentWhoamiResponse(accountId = "acc_001", tier = "developer", operationsRemaining = 950)
        val whoamiJson = Json.encodeToString(AgentWhoamiResponse.serializer(), whoami)
        assertEquals(950, Json.decodeFromString(AgentWhoamiResponse.serializer(), whoamiJson).operationsRemaining)

        // 3. Document Chunk Diff
        val diff = ChunkDiff(
            chunkId = "chk_001",
            oldHtml = "<p>Old clause</p>",
            newHtml = "<p>New clause</p>",
            explanation = "Updated section text"
        )
        val diffJson = Json.encodeToString(ChunkDiff.serializer(), diff)
        assertEquals("chk_001", Json.decodeFromString(ChunkDiff.serializer(), diffJson).chunkId)

        // 4. Async Job Polling
        val job = AsyncJobResponse(jobId = "job_999", status = "COMPLETED", progressPct = 100)
        val jobJson = Json.encodeToString(AsyncJobResponse.serializer(), job)
        assertEquals("COMPLETED", Json.decodeFromString(AsyncJobResponse.serializer(), jobJson).status)

        // 5. Multi-Format Export
        val exp = ExportResponse(downloadUrl = "https://cdn.superdocs.app/exports/doc.pdf", format = "pdf", bytesSize = 1024L)
        val expJson = Json.encodeToString(ExportResponse.serializer(), exp)
        assertEquals("pdf", Json.decodeFromString(ExportResponse.serializer(), expJson).format)

        // 6. Search Hits
        val search = DocumentSearchResponse(hits = listOf(SearchHit(chunkId = "chk_01", text = "Penalty clause", score = 0.95f)))
        val searchJson = Json.encodeToString(DocumentSearchResponse.serializer(), search)
        assertEquals(1, Json.decodeFromString(DocumentSearchResponse.serializer(), searchJson).hits.size)
    }

    @Test
    fun testClientInstantiation() = runTest {
        val client = SuperDocsClient(apiKey = "test_kmp_api_key")
        assertNotNull(client)
    }
}
