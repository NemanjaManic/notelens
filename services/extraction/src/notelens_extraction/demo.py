"""Versioned synthetic demo input, independent of annotation answer files."""

from .evidence import digest

TEXT = ("Demo \U0001fa7a\nThe patient denies chest pain.\nPneumonia is suspected.\n"
        "The patient's mother has diabetes.\nThe patient had an appendectomy in 2018.\n"
        "The patient reports cough.")


def request(question: str | None = None) -> dict:
    result = {"schema_version": "1.0.0", "document": {
        "schema_version": "1.0.0", "doc_id": "synthetic-demo-v1", "text": TEXT,
        "text_sha256": digest(TEXT), "canonicalization_version": "nfc-lf-v1",
        "source": {"kind": "synthetic_text", "name": "D offline demo"}, "language": "en",
        "language_validation": {"outcome": "accepted", "language": "en",
                                "policy_version": "known-english-fixture-v1", "reason": None}}}
    if question is not None:
        result["question"] = question
    return result
