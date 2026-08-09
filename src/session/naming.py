"""Automated Conversation Session Naming Module."""

import re
from typing import Optional


def generate_session_title(first_message: str, document_title: Optional[str] = None) -> str:
    """Generate a clean 3-to-5 word title automatically from initial prompt or document."""
    if document_title:
        doc_clean = document_title.replace("_", " ").replace("-", " ").replace(".docx", "").replace(".pdf", "").replace(".txt", "")
        doc_clean = re.sub(r"\s+", " ", doc_clean).strip().title()
        if len(doc_clean.split()) <= 6:
            return doc_clean

    text = re.sub(r"[^\w\s]", "", first_message).strip()
    words = text.split()

    if not words:
        return "Document Analysis Session"

    # Filter out common filler words
    stopwords = {"a", "an", "the", "please", "can", "you", "check", "run", "show", "me", "find", "all", "in", "on", "for", "with", "and", "or"}
    meaningful = [w for w in words if w.lower() not in stopwords]

    if not meaningful:
        meaningful = words

    selected = meaningful[:4]
    title = " ".join(selected).title()

    if len(title) > 40:
        title = title[:37] + "..."

    return title
