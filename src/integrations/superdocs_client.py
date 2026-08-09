"""SuperDocs API Client Integration for DocuMesh Engine."""

import os
import base64
import httpx
from typing import Optional, Dict, Any
from src.config import settings
from src.logging_config import get_logger

logger = get_logger("documesh.integrations.superdocs")


class SuperDocsClient:
    """Client for SuperDocs AI Document API (api.superdocs.app/v1)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SUPERDOCS_API_KEY", "")
        self.base_url = "https://api.superdocs.app/v1"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def upload_document_base64_async(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Upload and parse a document via SuperDocs base64 upload endpoint."""
        if not self.is_configured:
            logger.info("superdocs_key_not_set_using_local_parser", filepath=filepath)
            return None

        try:
            with open(filepath, "rb") as f:
                content_bytes = f.read()
            b64_str = base64.b64encode(content_bytes).decode("utf-8")
            filename = os.path.basename(filepath)

            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    f"{self.base_url}/upload_document_base64",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"file_name": filename, "file_base64": b64_str}
                )

                if res.status_code == 200:
                    data = res.json()
                    logger.info("superdocs_upload_success", filename=filename, doc_id=data.get("document_id"))
                    return data
                else:
                    logger.warning("superdocs_upload_failed", status_code=res.status_code, body=res.text)
                    return None
        except Exception as e:
            logger.error("superdocs_upload_exception", error=str(e))
            return None

    async def propose_document_remedy_async(
        self,
        session_id: str,
        instruction: str,
        document_html: str
    ) -> Optional[Dict[str, Any]]:
        """Call SuperDocs /v1/chat API to generate section-level document edit proposals."""
        if not self.is_configured:
            logger.info("superdocs_key_not_set_skipping_chat_remedy")
            return None

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(
                    f"{self.base_url}/chat",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "message": instruction,
                        "session_id": session_id,
                        "document_html": document_html,
                        "approval_mode": "ask_every_time",
                        "response_mode": "compact"
                    }
                )

                if res.status_code == 200:
                    data = res.json()
                    logger.info("superdocs_remedy_proposed", session_id=session_id)
                    return data
                else:
                    logger.warning("superdocs_chat_failed", status_code=res.status_code, body=res.text)
                    return None
        except Exception as e:
            logger.error("superdocs_chat_exception", error=str(e))
            return None

    async def export_document_async(self, document_html: str, export_format: str = "pdf") -> Optional[bytes]:
        """Export HTML document to PDF or DOCX using SuperDocs free export API."""
        if not self.is_configured:
            logger.info("superdocs_key_not_set_skipping_export")
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    f"{self.base_url}/export",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"document_html": document_html, "export_format": export_format}
                )

                if res.status_code == 200:
                    logger.info("superdocs_export_success", export_format=export_format)
                    return res.content
                else:
                    logger.warning("superdocs_export_failed", status_code=res.status_code)
                    return None
        except Exception as e:
            logger.error("superdocs_export_exception", error=str(e))
            return None
