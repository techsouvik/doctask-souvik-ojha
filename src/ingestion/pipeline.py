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


def wait_for_file_settled(filepath: str, timeout_sec: float = 3.0, check_interval: float = 0.5) -> bool:
    """Ensure a file is completely written before reading."""
    start_time = time.time()
    last_size = -1

    while time.time() - start_time < timeout_sec:
        if not os.path.exists(filepath):
            return False
        current_size = os.path.getsize(filepath)
        if current_size > 0 and current_size == last_size:
            return True
        last_size = current_size
        time.sleep(check_interval)

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
