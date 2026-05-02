# validators.py
# Post-LLM message validation. Checks for all anti-patterns from the scoring rubric.
# Used by composer.py to decide whether to re-prompt.

import re
from typing import Optional, Tuple

MAX_CHARS = 1000         # Hard limit — judge will reject above this
IDEAL_CHARS = 280        # WhatsApp-friendly target
MAX_RETRY_ATTEMPTS = 2   # Re-prompt at most this many times

# ============================================================================
# Clinical category config
# ============================================================================

CLINICAL_CATEGORIES = {"dentists", "doctors", "dermatologists", "physiotherapists"}

CLINICAL_TABOOS = [
    "guarantee", "guaranteed", "cure", "cures", "cured",
    "will definitely", "100% effective", "no side effects",
    "proven to cure", "permanent solution",
]

# ============================================================================
# Regex patterns
# ============================================================================

GENERIC_OFFER_PATTERNS = [
    re.compile(r"\b\d+\s*%\s*off\b", re.IGNORECASE),   # "30% off"
    re.compile(r"\bflat\s+\d+\b", re.IGNORECASE),       # "flat 99"
    re.compile(r"\bspecial\s+discount\b", re.IGNORECASE),
    re.compile(r"\bbig\s+sale\b", re.IGNORECASE),
]

CTA_PATTERNS = [
    re.compile(r"\breply\s+yes\b", re.IGNORECASE),
    re.compile(r"\breply\s+no\b", re.IGNORECASE),
    re.compile(r"\breply\s+stop\b", re.IGNORECASE),
    re.compile(r"\bclick\s+here\b", re.IGNORECASE),
    re.compile(r"\btap\s+here\b", re.IGNORECASE),
    re.compile(r"\bmsg\s+us\b", re.IGNORECASE),
    re.compile(r"\bsend\s+(it|me)\b", re.IGNORECASE),
    re.compile(r"\bbook\s+now\b", re.IGNORECASE),
    re.compile(r"\bcall\s+now\b", re.IGNORECASE),
]

LONG_PREAMBLE_STARTERS = [
    "i hope this",
    "i hope you",
    "i'm reaching out",
    "i am reaching out",
    "hi there,",
    "hello there,",
    "just wanted to",
    "just checking in",
    "i wanted to",
]

# ============================================================================
# Main validator
# ============================================================================


def validate_message(
    body: str,
    cta: str,
    category_slug: str,
    previous_body: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validate a composed message body against all anti-patterns.

    Returns:
        (True, None)            — valid message
        (False, error_string)   — invalid, with reason
    """

    # 1. Empty body
    if not body or not body.strip():
        return False, "Empty body"

    body_stripped = body.strip()

    # 2. Hard length limit
    if len(body_stripped) > MAX_CHARS:
        return False, f"Body too long ({len(body_stripped)} chars, max {MAX_CHARS})"

    # 3. Soft length warning (treated as error for quality)
    if len(body_stripped) > IDEAL_CHARS:
        return False, f"Body exceeds WhatsApp ideal ({len(body_stripped)} chars, target ≤{IDEAL_CHARS})"

    lower = body_stripped.lower()

    # 4. Long preamble
    for preamble in LONG_PREAMBLE_STARTERS:
        if lower.startswith(preamble):
            return False, f"Long preamble detected: starts with '{preamble}'"

    # 5. Generic offers
    for pattern in GENERIC_OFFER_PATTERNS:
        if pattern.search(body_stripped):
            return False, f"Generic offer detected: '{pattern.pattern}'"

    # 6. Multiple CTAs
    matched_ctas = [p for p in CTA_PATTERNS if p.search(body_stripped)]
    if len(matched_ctas) > 1:
        return False, f"Multiple CTAs detected ({len(matched_ctas)} found)"

    # 7. CTA must be in the last sentence (if cta is not greeting)
    if cta not in ("greeting", "open_ended") and matched_ctas:
        sentences = [s.strip() for s in re.split(r"[.!?]", body_stripped) if s.strip()]
        if sentences:
            last_sentence = sentences[-1]
            if not any(p.search(last_sentence) for p in matched_ctas):
                return False, "CTA not in last sentence"

    # 8. Clinical taboos
    if category_slug.lower() in CLINICAL_CATEGORIES:
        for taboo in CLINICAL_TABOOS:
            if taboo.lower() in lower:
                return False, f"Clinical taboo detected: '{taboo}'"

    # 9. Verbatim repetition (exact match with previous message)
    if previous_body and body_stripped.strip() == previous_body.strip():
        return False, "Verbatim repetition of previous message"

    return True, None


# ============================================================================
# Re-prompt decision
# ============================================================================


def should_re_prompt(
    body: str,
    cta: str,
    category_slug: str,
    attempt_num: int,
    previous_body: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Decide whether the LLM output should be re-prompted.

    Returns:
        (True, error_reason)   — re-prompt
        (False, None)          — accept the message
    """
    is_valid, error = validate_message(body, cta, category_slug, previous_body)

    if not is_valid and attempt_num < MAX_RETRY_ATTEMPTS:
        return True, error

    return False, None


# ============================================================================
# JSON extraction helper
# ============================================================================


def extract_json_from_response(text: str) -> Optional[str]:
    """
    Try to extract a JSON object from an LLM response that might contain
    surrounding text or markdown fences.
    """
    # Try to find {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return None
