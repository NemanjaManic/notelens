"""Exercise the production HTTP entry point with a local synthetic fitted artifact."""

from hashlib import sha256
import json
import sys

from fastapi.testclient import TestClient
import pytest
from notelens_contracts.v1 import validate_record

pytest.importorskip("sklearn", reason="Optional training dependency group is not installed")

import joblib

from conftest import REQUEST_ID, prepared
from notelens_classifier.inference import LABELS, MANIFEST_FILE, MODEL_FILE, load_model
from notelens_classifier.main import Settings, create_app


TOKEN = "synthetic-local-inference-token"
HEADERS = {"X-Request-ID": REQUEST_ID, "Authorization": "Bearer " + TOKEN}


def test_http_model_readiness_identity_and_repeatability(model_bundle):
    model = load_model(*model_bundle)
    with TestClient(create_app(Settings(mode="live", token=TOKEN), model=model),
                    client=("127.0.0.1", 50000)) as http:
        ready = http.get("/health/ready", headers=HEADERS)
        assert ready.status_code == 200
        assert validate_record("HealthResult", ready.json())["model_version"] == model.model_version
        for text, expected in (("cardiac", LABELS[0]), ("unseenmarker", None)):
            document = prepared(text)
            body = {"schema_version": "1.0.0", "document": document}
            first = http.post("/v1/classify", json=body, headers=HEADERS)
            second = http.post("/v1/classify", json=body, headers=HEADERS)
            assert first.status_code == second.status_code == 200
            assert first.headers["x-request-id"] == REQUEST_ID and first.headers["cache-control"] == "no-store"
            result = validate_record("ClassificationResult", first.json(), document=document)
            assert result == second.json()
            assert result["mode"] == "live"
            assert result["category"] == expected
            assert result["status"] == ("supported" if expected else "uncertain")
            assert [score["category"] for score in result["scores"]] == list(LABELS)


def test_model_is_limited_to_configured_loopback_clients(model_bundle, body):
    model = load_model(*model_bundle)
    for settings in (Settings(mode="mock", token=TOKEN), Settings(mode="live")):
        with pytest.raises(ValueError, match="requires live mode and a service token"):
            create_app(settings, model=model)
    app = create_app(Settings(mode="live", token=TOKEN), model=model)
    for peer, headers in (("203.0.113.5", HEADERS), ("127.0.0.1", {"X-Request-ID": REQUEST_ID})):
        with TestClient(app, client=(peer, 50000)) as http:
            assert http.get("/health/ready", headers=headers).status_code == 401
            response = http.post("/v1/classify", json=body, headers=headers)
            assert response.status_code == 401
            assert response.json()["request_id"] == REQUEST_ID


def test_artifact_is_verified_before_deserialization(model_bundle, monkeypatch):
    directory, checksum = model_bundle

    def forbidden(*args):
        pytest.fail("A mismatched artifact was deserialized")

    monkeypatch.setattr(joblib, "load", forbidden)
    with pytest.raises(ValueError, match="manifest checksum mismatch"):
        load_model(directory, "0" * 64)
    (directory / MODEL_FILE).write_bytes(b"corrupted model")
    with pytest.raises(ValueError, match="model checksum mismatch"):
        load_model(directory, checksum)


def test_pinned_artifact_with_wrong_labels_fails_at_startup(model_bundle):
    directory, _ = model_bundle
    model_path = directory / MODEL_FILE
    pipeline = joblib.load(model_path)
    pipeline.named_steps["classifier"].classes_[0] = "Invalid Specialty"
    joblib.dump(pipeline, model_path)
    manifest_path = directory / MANIFEST_FILE
    manifest = json.loads(manifest_path.read_bytes())
    manifest["artifact_sha256"] = sha256(model_path.read_bytes()).hexdigest()
    payload = json.dumps(manifest).encode()
    manifest_path.write_bytes(payload)

    with pytest.raises(ValueError, match="label mapping differs"):
        load_model(directory, sha256(payload).hexdigest())


def test_startup_checks_full_result_and_score_width(model_bundle, monkeypatch):
    directory, checksum = model_bundle
    from sklearn.linear_model import LogisticRegression

    monkeypatch.setattr(LogisticRegression, "predict_proba", lambda *_: [[0.2] * 5 + [0.0]])
    with pytest.raises(ValueError, match="score width"):
        load_model(directory, checksum)


def test_missing_artifact_stops_launcher_with_safe_error(tmp_path, monkeypatch, capsys):
    from notelens_classifier import __main__ as launcher

    private_path = tmp_path / "private-artifact-location"
    monkeypatch.setattr(sys, "argv", ["notelens_classifier", "--development-model", str(private_path),
                                    "--model-manifest-sha256", "0" * 64])
    monkeypatch.setenv("NOTELENS_CLASSIFIER_MODE", "live")
    monkeypatch.setenv("NOTELENS_CLASSIFIER_SERVICE_TOKEN", TOKEN)
    monkeypatch.setattr(launcher.uvicorn, "run", lambda *args, **kwargs: pytest.fail("Started without the model"))

    with pytest.raises(SystemExit) as stopped:
        launcher.main()
    assert stopped.value.code == 2
    error = capsys.readouterr().err
    assert "Could not start with the trusted development model" in error
    assert private_path.name not in error and TOKEN not in error


def test_manifest_margin_is_applied_and_legacy_bundle_still_loads(model_bundle):
    directory, checksum = model_bundle
    document = prepared("cardiac")
    old = load_model(directory, checksum)
    assert old.classify(document)["category"] == LABELS[0]
    assert old.minimum_margin == 0

    manifest_path = directory / MANIFEST_FILE
    manifest = json.loads(manifest_path.read_bytes())
    manifest["minimum_margin"] = 0.5
    raw_manifest = json.dumps(manifest).encode()
    manifest_path.write_bytes(raw_manifest)
    new = load_model(directory, sha256(raw_manifest).hexdigest())
    assert new.minimum_margin == 0.5
    assert new.classify(document)["status"] == "uncertain"


def test_ambiguity_policy_checks_the_fitted_model_without_altering_scores(model_bundle):
    directory, checksum = model_bundle
    reference = load_model(directory, checksum)
    manifest_path = directory / MANIFEST_FILE
    manifest = json.loads(manifest_path.read_bytes())
    manifest["ambiguity_policy"] = {
        "minimum_word_evidence": 0.2, "segment_threshold": 0.3, "segment_margin": 0.05, "competing_score_ratio": 0.35,
        "minimum_section_share": 0.2,
    }
    raw_manifest = json.dumps(manifest).encode()
    manifest_path.write_bytes(raw_manifest)
    candidate = load_model(directory, sha256(raw_manifest).hexdigest())

    assert candidate.classify(prepared("cardiac"))["category"] == LABELS[0]
    document = prepared("cardiac cardiac cardiac and urologic")
    before = reference.classify(document)
    after = candidate.classify(document)
    assert before["status"] == "supported"
    assert after["status"] == "uncertain"
    assert "Different parts of the text" in after["confidence_note"]
    assert before["scores"] == after["scores"]
    validate_record("ClassificationResult", after, document=document)
