"""Search API Router for sub-30ms hybrid BM25 search."""

from typing import Optional, List
from fastapi import APIRouter
from pydantic import BaseModel

from src.app.project_service import ProjectService
from src.reconciliation.search import HybridSearchIndex

router = APIRouter(prefix="/projects/{project_id}/search", tags=["Search Engine"])


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


@router.post("")
def search_chunks(project_id: str, req: SearchRequest):
    """Search document chunks using sub-30ms Hybrid BM25 search index."""
    state = ProjectService.get_project_state(project_id)

    index = HybridSearchIndex()
    all_chunks = []
    for doc in state.documents:
        all_chunks.extend(doc.chunks)

    index.add_chunks(all_chunks)
    results = index.search(req.query, top_k=req.top_k or 5)

    return {
        "project_id": project_id,
        "query": req.query,
        "total_chunks_searched": len(all_chunks),
        "results": [
            {
                "score": round(score, 4),
                "chunk_id": chunk.chunk_id,
                "doc_name": chunk.doc_name,
                "section_title": chunk.section_title,
                "page_num": chunk.page_num,
                "text": chunk.text
            }
            for chunk, score in results
        ]
    }
