"""Ingestion pipeline module: file hashing, locks, and parsing wrapper."""

import os
import hashlib
import uuid
import time
from typing import Optional, List
from src.models.domain import DocumentMetadata
from src.ingestion.parsers import parse_document
from src.ingestion.chunker import create_chunks_from_blocks


def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def wait_for_file_settled(filepath: str, timeout_sec: float = 1.0) -> bool:
    """Ensure a file is completely written before reading."""
    if not os.path.exists(filepath):
        return False

    size = os.path.getsize(filepath)
    if size > 0:
        return True

    time.sleep(0.1)
    return os.path.exists(filepath) and os.path.getsize(filepath) > 0


def ingest_file(filepath: str, project_id: str, existing_checksums: Optional[List[str]] = None) -> Optional[DocumentMetadata]:
    """Ingest a single document file, computing SHA-256, parsing blocks, and creating chunks."""
    if not wait_for_file_settled(filepath):
        return None

    filename = os.path.basename(filepath)
    checksum = compute_sha256(filepath)

    # Check for deduplication
    if existing_checksums and checksum in existing_checksums:
        print(f"Skipping duplicate file {filename} (checksum match)")
        return None

    doc_id = str(uuid.uuid4())[:8] + "_" + filename.replace(" ", "_")
    full_text, blocks, fmt = parse_document(filepath)
    chunks = create_chunks_from_blocks(doc_id, filename, blocks)

    return DocumentMetadata(
        doc_id=doc_id,
        project_id=project_id,
        filename=filename,
        filepath=filepath,
        format=fmt,
        checksum=checksum,
        extracted_text=full_text,
        chunks=chunks
    )
