package app.superdocs.client

import app.superdocs.client.errors.SuperDocsErrorPayload
import app.superdocs.client.errors.SuperDocsException
import kotlinx.serialization.json.Json
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class SuperDocsExceptionTest {

    @Test
    fun testAuthenticationException() {
        val ex = SuperDocsException.AuthenticationException("Invalid key", 401)
        assertEquals(401, ex.statusCode)
        assertTrue(ex.message!!.contains("Authentication Error"))
    }

    @Test
    fun testRateLimitException() {
        val ex = SuperDocsException.RateLimitException("Too many operations", 60)
        assertEquals(60, ex.retryAfterSeconds)
        assertTrue(ex.message!!.contains("Rate Limit Exceeded"))
    }

    @Test
    fun testErrorPayloadSerialization() {
        val payload = SuperDocsErrorPayload(
            error = "invalid_document",
            code = "DOC_PARSE_ERR",
            detail = "Could not parse corrupted PDF stream"
        )

        val json = Json.encodeToString(SuperDocsErrorPayload.serializer(), payload)
        val decoded = Json.decodeFromString(SuperDocsErrorPayload.serializer(), json)

        assertEquals("DOC_PARSE_ERR", decoded.code)
        assertEquals("Could not parse corrupted PDF stream", decoded.detail)
    }

    @Test
    fun testBuilderDsl() {
        val client = superDocsClient {
            apiKey = "sk_test_builder_123"
            baseUrl = "https://custom.superdocs.app/v1"
        }
        assertTrue(client is ISuperDocsClient)
    }
}
