package app.superdocs.client.work

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import app.superdocs.client.SuperDocsClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class DocumentWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        val apiKey = inputData.getString("API_KEY") ?: return@withContext Result.failure()
        val filename = inputData.getString("FILENAME") ?: "document.pdf"
        val sessionId = inputData.getString("SESSION_ID") ?: "session_bg"
        val instruction = inputData.getString("INSTRUCTION") ?: "Process document reconciliation"

        try {
            val client = SuperDocsClient(apiKey = apiKey)
            client.sendChatInstructionFlow(sessionId, instruction).collect {
                // Background job completed cleanly
            }
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }
}
