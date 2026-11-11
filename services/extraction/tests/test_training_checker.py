"""Persist the eight earlier inline negative experiments as repeatable regressions."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parents[3] / "docs/extraction-eval"
spec = importlib.util.spec_from_file_location("training_checker", DOCS / "check_training_examples.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def data():
    return json.loads((DOCS / "annotation-training-examples.json").read_text(encoding="utf-8"))


def test_original_command_counts():
    errors, counts = checker.validate(data())
    assert not errors
    assert counts == {"documents": 16, "mentions": 18, "spans": 37}


@pytest.mark.parametrize("case", ["hash", "quote", "utf16", "duplicate", "icd", "unresolved", "subject", "boolean"])
def test_eight_negative_training_cases(case):
    source = data()
    first = source["examples"][0]
    if case == "hash":
        first["text_sha256"] = "0" * 64
    elif case == "quote":
        first["mentions"][0]["mention"]["quote"] = "wrong quote"
    elif case == "utf16":
        repeated = next(c for c in source["examples"] if c["id"] == "repeated_denial")
        repeated["mentions"][1]["evidence"][0].update(start=18, end=32)
    elif case == "duplicate":
        first["mentions"].append(copy.deepcopy(first["mentions"][0]))
    elif case == "icd":
        next(c for c in source["examples"] if c["id"] == "explicit_icd")["mentions"][0]["icd"]["code"] = "J00"
    elif case == "unresolved":
        first["mentions"][0].update(assertion=None, unresolved_question=None)
    elif case == "subject":
        first["mentions"][0]["subject"] = []
    elif case == "boolean":
        first["mentions"][0]["mention"]["start"] = True
    errors, _ = checker.validate(source)
    assert errors
