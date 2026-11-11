"""Check the synthetic annotation exercises, not the shared API or real reports.

Run from any directory with Python 3.11+:
    python -B docs/extraction-eval/check_training_examples.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

# Reuse the service's dependency-free evidence primitive; no package install needed.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services/extraction/src"))
from notelens_extraction.evidence import EvidenceError, validate_span


EXAMPLES_PATH = Path(__file__).resolve().with_name("annotation-training-examples.json")
FORMAT = "notelens-draft-annotation-training-v1"
TYPES = {"diagnosis", "symptom", "procedure"}
ASSERTIONS = {"confirmed", "suspected", "negated"}
TEMPORALITIES = {"current", "historical", "unknown"}
SUBJECTS = {"patient", "family", "other", "unknown"}


def validate(data: Any) -> tuple[list[str], dict[str, int]]:
    """Return location-only structural errors and counts for draft examples.

    This deliberately cannot determine whether a label is clinically or semantically
    supported. It never prints a document body, quote, hash, or error input value.
    """
    errors: list[str] = []
    counts = {"documents": 0, "mentions": 0, "spans": 0}

    if not isinstance(data, dict):
        return ["root must be an object"], counts
    if data.get("format") != FORMAT:
        errors.append("root: unexpected training format")
    examples = data.get("examples")
    if not isinstance(examples, list) or not examples:
        return errors + ["root: examples must be a non-empty array"], counts

    identifiers: set[str] = set()

    def check_span(text: str, span: Any, where: str) -> bool:
        counts["spans"] += 1
        if not isinstance(span, dict):
            errors.append(f"{where}: span must be an object")
            return False
        start, end, quote = span.get("start"), span.get("end"), span.get("quote")
        # bool is a subclass of int, but is not a meaningful offset.
        if type(start) is not int or type(end) is not int:
            errors.append(f"{where}: start and end must be integers")
            return False
        if not isinstance(quote, str) or not quote:
            errors.append(f"{where}: quote must be non-empty text")
            return False
        try:
            validate_span(text, span)
        except EvidenceError as exc:
            errors.append(f"{where}: {exc}")
            return False
        return True

    for document_index, example in enumerate(examples, start=1):
        where = f"document {document_index}"
        counts["documents"] += 1
        if not isinstance(example, dict):
            errors.append(f"{where}: example must be an object")
            continue

        identifier = example.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9_]+", identifier):
            errors.append(f"{where}: id must contain lowercase letters, digits or underscores")
        elif identifier in identifiers:
            errors.append(f"{where}: duplicate example id")
        else:
            identifiers.add(identifier)

        text = example.get("canonical_text")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{where}: canonical_text must be non-empty")
            continue
        if example.get("canonicalization_version") != "nfc-lf-v1":
            errors.append(f"{where}: unexpected canonicalization version")
        if text.startswith("\ufeff") or "\r" in text or unicodedata.normalize("NFC", text) != text:
            errors.append(f"{where}: text does not satisfy nfc-lf-v1")
        try:
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        except UnicodeEncodeError:
            errors.append(f"{where}: text contains invalid Unicode")
            continue
        if digest != example.get("text_sha256"):
            errors.append(f"{where}: SHA-256 does not match canonical text")

        mentions = example.get("mentions")
        if not isinstance(mentions, list):
            errors.append(f"{where}: mentions must be an array")
            continue
        seen_spans: set[tuple[int, int, str]] = set()
        for mention_index, item in enumerate(mentions, start=1):
            location = f"{where}, mention {mention_index}"
            counts["mentions"] += 1
            if not isinstance(item, dict):
                errors.append(f"{location}: mention must be an object")
                continue
            kind = item.get("type")
            if not isinstance(kind, str) or kind not in TYPES:
                errors.append(f"{location}: invalid type")
            assertion = item.get("assertion")
            if "assertion" not in item or (
                assertion is not None and (not isinstance(assertion, str) or assertion not in ASSERTIONS)
            ):
                errors.append(f"{location}: invalid assertion")
            if assertion is None and not (
                isinstance(item.get("unresolved_question"), str)
                and item["unresolved_question"].strip()
            ):
                errors.append(f"{location}: unresolved assertion needs a review question")
            if not isinstance(item.get("temporality"), str) or item["temporality"] not in TEMPORALITIES:
                errors.append(f"{location}: invalid temporality")
            if not isinstance(item.get("subject"), str) or item["subject"] not in SUBJECTS:
                errors.append(f"{location}: invalid subject")

            mention = item.get("mention")
            if check_span(text, mention, f"{location}, mention span") and isinstance(kind, str):
                key = (mention["start"], mention["end"], kind)
                if key in seen_spans:
                    errors.append(f"{location}: duplicate mention span and type")
                seen_spans.add(key)

            evidence = item.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"{location}: at least one evidence span is required")
            else:
                for index, span in enumerate(evidence, start=1):
                    check_span(text, span, f"{location}, evidence {index}")

            if "icd" in item:
                icd = item["icd"]
                if not isinstance(icd, dict):
                    errors.append(f"{location}: icd must be an object")
                else:
                    code = icd.get("code")
                    if not isinstance(code, str) or not code:
                        errors.append(f"{location}: icd code must be non-empty text")
                    valid = check_span(text, icd.get("evidence"), f"{location}, icd evidence")
                    if valid and code != icd["evidence"]["quote"]:
                        errors.append(f"{location}: icd code differs from its evidence")

    return errors, counts


def main() -> int:
    try:
        with EXAMPLES_PATH.open(encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, UnicodeError, json.JSONDecodeError):
        print("FAIL: could not read the synthetic training JSON.", file=sys.stderr)
        return 1
    errors, counts = validate(data)
    if errors:
        print(f"FAIL: {len(errors)} issue(s) in the synthetic training examples.")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"PASS: {counts['documents']} synthetic documents, {counts['mentions']} mentions, "
        f"and {counts['spans']} mention/evidence/code spans checked."
    )
    print("Structural checks only; semantic support and clinical validity were not evaluated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
