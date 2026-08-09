"""Unit test for Hybrid Search Index."""

from src.models.domain import TextChunk
from src.reconciliation.search import HybridSearchIndex


def test_hybrid_search_index():
    index = HybridSearchIndex()

    c1 = TextChunk(
        chunk_id="chk1", doc_id="d1", doc_name="plan.docx",
        text="The project handover date is 15 December 2024 with a penalty clause of 0.5% per week.",
        start_char=0, end_char=80
    )
    c2 = TextChunk(
        chunk_id="chk2", doc_id="d2", doc_name="invoice.docx",
        text="Invoice INV-2024-003 for Milestone M3 superstructure billing Rs 3.30 crores.",
        start_char=0, end_char=75
    )

    index.add_chunks([c1, c2])

    results = index.search("penalty clause handover", top_k=1)
    assert len(results) == 1
    assert results[0][0].chunk_id == "chk1"

    results_inv = index.search("invoice billing milestone", top_k=1)
    assert len(results_inv) == 1
    assert results_inv[0][0].chunk_id == "chk2"
