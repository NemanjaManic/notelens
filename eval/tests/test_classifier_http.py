from pathlib import Path
import json

import pytest

from notelens_eval.classifier_http import check_classifier, check_response, synthetic_request


@pytest.fixture
def uncertain():
    root = Path(__file__).resolve().parents[2]
    fixtures = json.loads((root / "contracts/v1/fixtures/payloads.json").read_text(encoding="utf-8"))
    document = synthetic_request("uncertain")["document"]
    return document, {**fixtures["classification-uncertain"],
                      "doc_id": document["doc_id"], "text_sha256": document["text_sha256"]}


def test_uncertain_is_an_abstention_even_when_scores_are_present(uncertain):
    document, record = uncertain
    result = check_response(record, document, mode="mock", model_version=None, case="uncertain")
    assert result["outcome"] == "abstained"
    assert result["category"] is None
    assert len(result["score_labels"]) == 5


@pytest.mark.parametrize(("field", "value", "error"), [
    ("mode", "mock", "mode differs"),
    ("model_version", "different-model", "model version differs"),
    ("doc_id", "different-document", "document identity"),
    ("text_sha256", "0" * 64, "document identity"),
    ("category", "Neurology", "frozen classification contract"),
    ("scores", [], "frozen classification contract"),
])
def test_fitted_check_rejects_mismatches(uncertain, field, value, error):
    document, record = uncertain
    fitted = {**record, "mode": "live", "model_version": "synthetic-fitted", "score_kind": "probability",
              "scores": [{**score, "score": 0.2} for score in record["scores"]]}
    assert check_response(fitted, document, mode="live", model_version="synthetic-fitted",
                          case="uncertain")["outcome"] == "abstained"
    with pytest.raises(ValueError, match=error):
        check_response({**fitted, field: value}, document, mode="live", model_version="synthetic-fitted",
                       case="uncertain")


def test_frozen_contract_rejects_reordered_scores(uncertain):
    document, record = uncertain
    record["scores"].reverse()
    with pytest.raises(ValueError, match="frozen classification contract"):
        check_response(record, document, mode="mock", model_version=None, case="uncertain")


def test_repeatability_check_uses_authenticated_no_store_loopback(uncertain, monkeypatch):
    _, record = uncertain
    responses = iter((record, {**record, "confidence_note": "Different explanation."}))

    def post(port, path, payload, *, token, require_no_store):
        assert (port, path, token, require_no_store) == (8002, "/v1/classify", "test-token", True)
        assert payload == synthetic_request("uncertain")
        return next(responses)

    monkeypatch.setattr("notelens_eval.classifier_http.post_loopback", post)
    with pytest.raises(ValueError, match="Repeated classifier results differed"):
        check_classifier(8002, "test-token", mode="mock", model_version=None, case="uncertain")
