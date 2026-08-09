"""Unit tests for SuperDocs API Client Integration."""

import pytest
from src.integrations.superdocs_client import SuperDocsClient


@pytest.mark.asyncio
async def test_superdocs_client_offline_fallback(tmp_path):
    client = SuperDocsClient(api_key="")
    assert not client.is_configured

    # Test upload fallback
    test_file = str(tmp_path / "sample_contract.txt")
    with open(test_file, "w") as f:
        f.write("Sample contract text")

    upload_res = await client.upload_document_base64_async(test_file)
    assert upload_res is None  # Graceful fallback

    # Test chat remedy fallback
    remedy_res = await client.propose_document_remedy_async(
        session_id="sess_001",
        instruction="Adjust Phase 3 billing to 40%",
        document_html="<p>Invoice INV-003</p>"
    )
    assert remedy_res is None  # Graceful fallback

    # Test export fallback
    export_res = await client.export_document_async("<p>Reconciled Register</p>", export_format="pdf")
    assert export_res is None  # Graceful fallback
