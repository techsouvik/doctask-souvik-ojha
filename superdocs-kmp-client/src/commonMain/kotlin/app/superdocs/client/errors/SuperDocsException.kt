package app.superdocs.client.errors

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class SuperDocsErrorPayload(
    @SerialName("error") val error: String = "",
    @SerialName("code") val code: String = "",
    @SerialName("detail") val detail: String = ""
)

/**
 * Base sealed exception hierarchy for SuperDocs Kotlin SDK.
 */
sealed class SuperDocsException(
    message: String,
    cause: Throwable? = null
) : Exception(message, cause) {

    /** 401/403 Authentication or Invalid API Key */
    class AuthenticationException(
        message: String,
        val statusCode: Int = 401
    ) : SuperDocsException("SuperDocs Authentication Error ($statusCode): $message")

    /** 429 Rate Limit Exceeded */
    class RateLimitException(
        message: String,
        val retryAfterSeconds: Int? = null
    ) : SuperDocsException("SuperDocs Rate Limit Exceeded: $message")

    /** 4xx/5xx API Response Error */
    class ApiException(
        val statusCode: Int,
        val errorPayload: SuperDocsErrorPayload? = null,
        message: String
    ) : SuperDocsException("SuperDocs API Error ($statusCode): $message")

    /** Network connection or IO failure */
    class NetworkException(
        message: String,
        cause: Throwable? = null
    ) : SuperDocsException("SuperDocs Network Failure: $message", cause)

    /** Client-side validation failure */
    class ValidationException(
        message: String
    ) : SuperDocsException("SuperDocs Validation Error: $message")
}
