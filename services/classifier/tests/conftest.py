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


@pytest.fixture
def model_bundle(tmp_path):
    pytest.importorskip("sklearn", reason="Optional training dependency group is not installed")
    from importlib.metadata import version

    import joblib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    from notelens_classifier.inference import LABELS, MANIFEST_FILE, MODEL_FILE

    pipeline = Pipeline([("tfidf", TfidfVectorizer()), ("classifier", LogisticRegression(random_state=42))])
    pipeline.fit(["cardiac", "orthopedic", "gastric", "neuro", "urologic"], LABELS)
    model_path = tmp_path / MODEL_FILE
    joblib.dump(pipeline, model_path)
    manifest = {
        "stage": "development", "estimator": "logistic_regression", "model_version": "synthetic-model",
        "labels": LABELS, "threshold": 0.30, "artifact_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "packages": {name: version(name) for name in ("scikit-learn", "numpy", "scipy", "joblib")},
    }
    payload = json.dumps(manifest).encode()
    (tmp_path / MANIFEST_FILE).write_bytes(payload)
    return tmp_path, hashlib.sha256(payload).hexdigest()
