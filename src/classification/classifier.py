"""Hybrid Document Classifier: Rule-based fast path with LLM fallback."""

import os
from typing import Tuple
from src.models.domain import DocumentMetadata, DocumentType
from src.classification.security import detect_prompt_injection


def classify_document(doc: DocumentMetadata) -> DocumentMetadata:
    """Classify a document into a DocumentType and check for prompt injection."""
    text = doc.extracted_text or ""
    
    # 1. Prompt Injection Check
    is_inj, reason, _ = detect_prompt_injection(text)
    if is_inj:
        doc.quarantined = True
        doc.quarantine_reason = reason
        print(f"  🚨 QUARANTINED: {doc.filename} -> {reason}")

    filename_lower = doc.filename.lower()
    text_lower = text[:1500].lower()

    # 2. Rule-based Fast Path
    doc_type = DocumentType.OTHER
    confidence = 0.5

    if "master_project_plan" in filename_lower or "contract" in filename_lower or "agreement" in filename_lower:
        doc_type = DocumentType.CONTRACT
        confidence = 0.98
    elif "amendment" in filename_lower or "amd" in filename_lower or "variation" in filename_lower:
        doc_type = DocumentType.AMENDMENT
        confidence = 0.98
    elif "status_report" in filename_lower or "quarterly" in filename_lower or "progress" in filename_lower:
        doc_type = DocumentType.STATUS_REPORT
        confidence = 0.98
    elif "invoice" in filename_lower or "inv-" in filename_lower or "bill" in filename_lower:
        doc_type = DocumentType.INVOICE
        confidence = 0.98
    elif "minutes" in filename_lower or "site_visit" in filename_lower or "meeting" in filename_lower:
        doc_type = DocumentType.MEETING_MINUTES
        confidence = 0.98
    elif "receipt" in filename_lower or "mrn" in filename_lower or "delivery_note" in filename_lower:
        doc_type = DocumentType.MATERIAL_RECEIPT
        confidence = 0.98
    elif "complaint" in filename_lower or "letter" in filename_lower or "email" in filename_lower or "correspondence" in filename_lower:
        doc_type = DocumentType.CORRESPONDENCE
        confidence = 0.98

    # Body text fallback heuristic if filename was obscure
    if confidence < 0.9:
        if "master project plan" in text_lower or "schedule b" in text_lower:
            doc_type = DocumentType.CONTRACT
            confidence = 0.90
        elif "contract amendment" in text_lower:
            doc_type = DocumentType.AMENDMENT
            confidence = 0.90
        elif "quarterly status report" in text_lower or "progress by phase" in text_lower:
            doc_type = DocumentType.STATUS_REPORT
            confidence = 0.90
        elif "tax invoice" in text_lower or "milestone billing" in text_lower:
            doc_type = DocumentType.INVOICE
            confidence = 0.90
        elif "meeting minutes" in text_lower or "action items" in text_lower:
            doc_type = DocumentType.MEETING_MINUTES
            confidence = 0.90
        elif "material receipt note" in text_lower or "delivery status: complete" in text_lower:
            doc_type = DocumentType.MATERIAL_RECEIPT
            confidence = 0.90

    doc.doc_type = doc_type
    doc.classification_confidence = confidence

    return doc
