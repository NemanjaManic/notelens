"""Synthetic input only; never read the MTSamples source or submitted reports."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from notelens_classifier.main import Settings, create_app

ROOT = Path(__file__).resolve().parents[3]
REQUEST_ID = "11111111-1111-4111-8111-111111111111"


def prepared(text="Synthetic note: chest pain. 🩺 No chest pain. No chest pain.", doc_id="synthetic-c-scaffold"):
    return {
        "schema_version": "1.0.0", "doc_id": doc_id, "text": text,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "canonicalization_version": "nfc-lf-v1", "source": {"kind": "synthetic_text"},
        "language": "en",
        "language_validation": {"outcome": "accepted", "language": "en",
                                "policy_version": "fixture-language-policy-v0", "reason": None},
    }


@pytest.fixture
def document():
    return prepared()


@pytest.fixture
def body(document):
    return {"schema_version": "1.0.0", "document": deepcopy(document)}


@pytest.fixture
def client():
    with TestClient(create_app(Settings(mode="mock", scenario="supported")),
                    base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as value:
        yield value


@pytest.fixture
def shared_payloads():
    return json.loads((ROOT / "contracts/v1/fixtures/payloads.json").read_text(encoding="utf-8"))
