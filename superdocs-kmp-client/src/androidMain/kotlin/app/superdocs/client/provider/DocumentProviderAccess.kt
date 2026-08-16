package app.superdocs.client.provider

import android.content.ContentResolver
import android.net.Uri
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class DocumentProviderAccess(private val contentResolver: ContentResolver) {

    suspend fun readBytesFromUri(uri: Uri): ByteArray = withContext(Dispatchers.IO) {
        contentResolver.openInputStream(uri)?.use { stream ->
            stream.readBytes()
        } ?: throw IllegalArgumentException("Unable to open stream for URI: $uri")
    }
}
