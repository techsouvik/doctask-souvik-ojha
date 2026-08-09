"""Prompt Injection Quarantine & Security Sanitizer (Behavior #8)."""

import re
from typing import Tuple, Optional, List

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior)\s+instructions",
    r"you\s+are\s+now\s+a\s+",
    r"system:\s*override",
    r"assistant:\s*override",
    r"\[system\s+instruction:",
    r"\[admin\s+override:",
    r"do\s+not\s+report\s+any\s+errors",
    r"report\s+100%\s+compliance",
    r"override\s+all\s+penalt(y|ies)",
]


def detect_prompt_injection(text: str) -> Tuple[bool, Optional[str], List[str]]:
    """Scan text for prompt injection patterns. Returns (is_suspicious, reason, matched_patterns)."""
    matches = []
    text_lower = text.lower()

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            matches.append(pattern)

    if matches:
        reason = f"Security Alert: Document contains prompt injection pattern(s): {', '.join(matches)}"
        return True, reason, matches

    return False, None, []
