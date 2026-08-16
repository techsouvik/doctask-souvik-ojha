package app.superdocs.client

import app.superdocs.client.models.*
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull

class SuperDocsClientTest {

    @Test
    fun testSerializationModels() {
        val diff = ChunkDiff(
            chunkId = "chk_001",
            oldHtml = "<p>Old</p>",
            newHtml = "<p>New</p>",
            explanation = "Updated section text"
        )

        val json = Json.encodeToString(ChunkDiff.serializer(), diff)
        assertNotNull(json)

        val decoded = Json.decodeFromString(ChunkDiff.serializer(), json)
        assertEquals("chk_001", decoded.chunkId)
        assertEquals("<p>Old</p>", decoded.oldHtml)
    }

    @Test
    fun testClientInstantiation() = runTest {
        val client = SuperDocsClient(apiKey = "test_kmp_api_key")
        assertNotNull(client)
    }
}
