"""Grounding Verification: Ensures every extracted fact quote exists in source text (Behavior #5)."""

from difflib import SequenceMatcher


def verify_grounding(quote: str, full_doc_text: str, threshold: float = 0.80) -> bool:
    """Check if the extracted quote actually exists in the source document.
    
    Uses exact substring match first, then fallback to normalized fuzzy match.
    """
    if not quote or not full_doc_text:
        return False

    q_clean = " ".join(quote.lower().split())
    doc_clean = " ".join(full_doc_text.lower().split())

    # Direct substring match
    if q_clean in doc_clean:
        return True

    # If quote is very short, exact match is required
    if len(q_clean) < 15:
        return False

    # Sliding window fuzzy match for long quotes
    q_len = len(q_clean)
    step = max(1, q_len // 2)

    for i in range(0, len(doc_clean) - q_len + 1, step):
        window = doc_clean[i : i + q_len]
        ratio = SequenceMatcher(None, q_clean, window).ratio()
        if ratio >= threshold:
            return True

    return False
