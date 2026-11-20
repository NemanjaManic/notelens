import copy
import json
from pathlib import Path

import pytest

from notelens_eval.acceptance import evaluate


def inputs():
    config = json.loads((Path(__file__).parents[1] / "config/acceptance.json").read_text())
    measurement = {"version": "synthetic-test", "acceptance_version": config["version"],
                   "sample_count": 10, "metrics": {"schema_validity": 1, "span_validity": 1}}
    return config, measurement


def test_unset_quality_decisions_prevent_acceptance():
    config, measurement = inputs()
    original = copy.deepcopy(config)
    assert evaluate(config, measurement)["status"] == "pending"
    assert config == original
    measurement["metrics"]["span_validity"] = 0.9
    assert evaluate(config, measurement)["status"] == "failed"


def test_named_quality_decisions_and_zero_risk():
    config, measurement = inputs()
    config["criteria"] = {"answer_risk": config["criteria"]["answer_risk"]}
    config["criteria"]["answer_risk"].update(threshold=0)
    measurement["metrics"]["answer_risk"] = 0
    with pytest.raises(ValueError, match="named recorded"):
        evaluate(config, measurement)
    config["criteria"]["answer_risk"].update(decision_by="synthetic-test",
                                           decision_record="test-only")
    assert evaluate(config, measurement)["status"] == "passed"
    measurement["metrics"]["answer_risk"] = 0.1
    assert evaluate(config, measurement)["status"] == "failed"
