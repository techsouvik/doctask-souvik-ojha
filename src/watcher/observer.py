"""Incremental File Watcher: Monitors folder and updates register on file arrival (Movement 3)."""

import os
import time
from typing import Optional, Set, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from src.ingestion.pipeline import ingest_file
from src.classification.classifier import classify_document
from src.extraction.extractor import extract_facts


class DocumentArrivalHandler(FileSystemEventHandler):
    """Event handler for new or modified documents in the watched directory."""

    def __init__(self, project_id: str, on_new_document_callback: Any = None):
        super().__init__()
        self.project_id = project_id
        self.callback = on_new_document_callback
        self.processed_files: Set[str] = set()

    def on_created(self, event):
        if event.is_directory:
            return
        src_path_str = str(event.src_path)
        filename = os.path.basename(src_path_str)
        if src_path_str.startswith(".") or filename.startswith("."):
            return

        ext = os.path.splitext(src_path_str)[1].lower()
        if ext in [".docx", ".pdf", ".txt", ".md"]:
            self._handle_file_arrival(src_path_str)

    def _handle_file_arrival(self, filepath: str):
        if filepath in self.processed_files:
            return
        self.processed_files.add(filepath)

        print(f"\n[FILE WATCHER] New document detected: {os.path.basename(filepath)}")
        time.sleep(1.0)  # Wait for file write completion

        doc = ingest_file(filepath, self.project_id)
        if not doc:
            return

        doc = classify_document(doc)
        facts = extract_facts(doc)

        print(f"  ✓ Processed new arrival: {doc.filename} -> Extracted {len(facts)} facts")

        if self.callback:
            self.callback(doc)


def start_watcher(folder_path: str, project_id: str, callback: Any = None):
    """Start background watchdog observer on folder."""
    event_handler = DocumentArrivalHandler(project_id, callback)
    obs = Observer()
    obs.schedule(event_handler, folder_path, recursive=True)
    obs.start()
    print(f"[FILE WATCHER] Started watching directory: {folder_path}")
    return obs
