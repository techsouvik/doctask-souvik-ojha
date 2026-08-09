"""Documents API Router for file ingestion & document details."""

import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File

from src.app.project_service import ProjectService
from src.ingestion.pipeline import ingest_file
from src.classification.classifier import classify_document
from src.extraction.extractor import extract_facts

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["Documents"])


@router.get("")
def list_documents(project_id: str):
    """List all documents in project pile."""
    state = ProjectService.get_project_state(project_id)
    return {"project_id": project_id, "documents": [d.model_dump() for d in state.documents]}


@router.get("/{doc_id}")
def get_document_detail(project_id: str, doc_id: str):
    """Get document detail, extracted text, and chunks."""
    state = ProjectService.get_project_state(project_id)
    target = next((d for d in state.documents if d.doc_id == doc_id or d.filename == doc_id), None)

    if not target:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found in project {project_id}")

    return target.model_dump()


@router.post("")
async def upload_document(project_id: str, file: UploadFile = File(...)):
    """Upload a new document to the project folder for incremental update."""
    state = ProjectService.get_project_state(project_id)
    filename = file.filename or "uploaded_document.docx"
    target_path = os.path.join(state.doc_folder, filename)

    content = await file.read()
    with open(target_path, "wb") as f:
        f.write(content)

    doc = ingest_file(target_path, project_id)
    if not doc:
        return {"status": "duplicate_skipped", "filename": filename}

    doc = classify_document(doc)
    facts = extract_facts(doc)

    state.documents.append(doc)
    state.facts.extend(facts)

    return {
        "status": "ingested",
        "doc_id": doc.doc_id,
        "filename": doc.filename,
        "doc_type": doc.doc_type.value,
        "chunks_count": len(doc.chunks),
        "facts_extracted": len(facts)
    }
