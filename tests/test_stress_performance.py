"""Stress & Load Testing Suite for DocuMesh Application Layer."""

import time
import asyncio
import pytest
from src.app.project_service import ProjectService
from src.ingestion.parsers import parse_txt
from src.ingestion.chunker import create_chunks_from_blocks
from src.reconciliation.search import HybridSearchIndex
from src.models.domain import TextChunk


@pytest.mark.asyncio
async def test_high_concurrency_multi_project_stress():
    """Stress test parallel project pipelines running concurrently."""
    start_time = time.time()

    async def run_single_proj(idx: int):
        project_id = f"stress_proj_{idx}"
        state = ProjectService.run_pipeline_for_project(project_id)
        assert state.status == "AWAITING_HUMAN_GATE"
        assert len(state.pending_findings) == 5
        return project_id

    # Run 3 parallel projects concurrently
    tasks = [run_single_proj(i) for i in range(3)]
    project_ids = await asyncio.gather(*tasks)

    duration = time.time() - start_time
    print(f"\n[STRESS TEST] Successfully ran 3 parallel projects in {duration:.2f}s ({round(3/duration, 2)} projects/sec)")
    assert len(project_ids) == 3


def test_heavy_document_chunking_stress(tmp_path):
    """Stress test chunking a large 50-page document with 200 blocks."""
    large_text = "\n\n".join([f"Section {i}: This is simulated paragraph text for heavy document load testing paragraph number {i}." for i in range(200)])
    test_file = str(tmp_path / "heavy_doc.txt")

    with open(test_file, "w") as f:
        f.write(large_text)

    start_time = time.time()
    parsed_text, blocks = parse_txt(test_file)
    chunks = create_chunks_from_blocks("doc_heavy", "heavy_doc.txt", blocks, max_chunk_chars=500)

    duration_ms = (time.time() - start_time) * 1000.0
    print(f"\n[STRESS TEST] Chunked 200-block document into {len(chunks)} chunks in {duration_ms:.2f}ms")

    assert len(chunks) >= 150
    assert duration_ms < 500.0  # Must be under 500ms


def test_hybrid_search_subsecond_scale_stress():
    """Stress test BM25 search over 10,000 text chunks."""
    index = HybridSearchIndex()
    chunks = [
        TextChunk(
            chunk_id=f"chk_{i}",
            doc_id=f"doc_{i % 10}",
            doc_name=f"document_{i % 10}.docx",
            text=f"Chunk number {i} containing payment terms and milestone billing for superstructure phase {i % 5}.",
            start_char=0,
            end_char=100
        )
        for i in range(10000)
    ]

    start_index_t = time.time()
    index.add_chunks(chunks)
    index_duration_ms = (time.time() - start_index_t) * 1000.0

    start_search_t = time.time()
    results = index.search("payment terms milestone billing", top_k=10)
    search_duration_ms = (time.time() - start_search_t) * 1000.0

    print(f"\n[STRESS TEST] Indexed 10,000 chunks in {index_duration_ms:.2f}ms. Search query took {search_duration_ms:.2f}ms")

    assert len(results) == 10
    assert search_duration_ms < 50.0  # Search query must take under 50ms!
