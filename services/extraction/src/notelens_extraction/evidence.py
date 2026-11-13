"""Dependency-free canonical evidence checks shared by runtime and annotations."""

import hashlib
import unicodedata


class EvidenceError(ValueError):
    """Safe error: callers must not include document bodies in messages."""


def digest(text: str) -> str:
    try:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    except (AttributeError, UnicodeEncodeError) as exc:
        raise EvidenceError("Invalid Unicode text.") from exc


def validate_text(text: str, expected_hash: str) -> None:
    if not isinstance(text, str) or not text.strip():
        raise EvidenceError("Canonical text must be non-empty.")
    if len(text) > 100_000:
        raise EvidenceError("Canonical text exceeds 100,000 code points.")
    if text.startswith("\ufeff") or "\r" in text or unicodedata.normalize("NFC", text) != text:
        raise EvidenceError("Canonical text does not satisfy nfc-lf-v1.")
    if digest(text) != expected_hash:
        raise EvidenceError("Canonical text digest mismatch.")


def validate_span(text: str, span: dict) -> None:
    if not isinstance(span, dict):
        raise EvidenceError("Evidence must be an object.")
    start, end, quote = (span.get(key) for key in ("start", "end", "quote"))
    if type(start) is not int or type(end) is not int:
        raise EvidenceError("Evidence offsets must be integers.")
    if not isinstance(quote, str) or not quote:
        raise EvidenceError("Evidence quote must be non-empty.")
    if not 0 <= start < end <= len(text):
        raise EvidenceError("Evidence offsets are outside the document.")
    if text[start:end] != quote:
        raise EvidenceError("Evidence quote does not match its code-point interval.")


def resolve_quote(text: str, quote: str, occurrence: int | None = None) -> dict:
    """Resolve a private provider quote hint; repeated text needs an explicit index.

    occurrence is zero-based and is not an extra wire-contract field.
    """
    if not isinstance(quote, str) or not quote:
        raise EvidenceError("A non-empty evidence quote is required.")
    positions = []
    offset = 0
    while (found := text.find(quote, offset)) >= 0:
        positions.append(found)
        offset = found + 1
    if occurrence is None:
        if len(positions) != 1:
            raise EvidenceError("Evidence quote is absent or ambiguous; specify its occurrence.")
        occurrence = 0
    if type(occurrence) is not int or not 0 <= occurrence < len(positions):
        raise EvidenceError("Invalid evidence occurrence.")
    start = positions[occurrence]
    return {"start": start, "end": start + len(quote), "quote": quote}
