"""Evaluate versioned acceptance decisions without inventing missing thresholds."""

import argparse
import json
import math
from pathlib import Path


def number(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1


def evaluate(config, measurement):
    if config["version"] != measurement["acceptance_version"]:
        raise ValueError("Measurement targets another acceptance configuration.")
    if (not measurement["version"] or type(measurement["sample_count"]) is not int
            or measurement["sample_count"] <= 0):
        raise ValueError("A version and nonempty measured sample are required.")
    rows = []
    for name, criterion in config["criteria"].items():
        threshold = criterion["threshold"]
        direction = criterion["direction"]
        if direction not in ("minimum", "maximum"):
            raise ValueError("Invalid threshold direction.")
        if threshold is not None and not number(threshold):
            raise ValueError("Threshold must be between zero and one.")
        if criterion["kind"] == "structural":
            if threshold != 1 or direction != "minimum":
                raise ValueError("Structural acceptance requires complete validity.")
        elif criterion["kind"] == "quality":
            if threshold is not None and not all(
                isinstance(criterion.get(key), str) and criterion[key].strip()
                for key in ("decision_by", "decision_record")
            ):
                raise ValueError("Quality thresholds require a named recorded decision.")
        else:
            raise ValueError("Invalid criterion kind.")
        value = measurement["metrics"].get(name)
        if value is not None and not number(value):
            raise ValueError("Measured rates must be between zero and one.")
        status = "decision_pending" if threshold is None else "measurement_missing"
        if threshold is not None and value is not None:
            passed = value >= threshold if direction == "minimum" else value <= threshold
            status = "passed" if passed else "failed"
        rows.append({"metric": name, "threshold": threshold, "value": value, "status": status})
    return {
        "acceptance_version": config["version"], "measurement_version": measurement["version"],
        "sample_count": measurement["sample_count"], "criteria": rows,
        "status": "failed" if any(row["status"] == "failed" for row in rows)
        else "passed" if rows and all(row["status"] == "passed" for row in rows) else "pending",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--measurement", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(json.loads(args.config.read_text(encoding="utf-8")),
                      json.loads(args.measurement.read_text(encoding="utf-8")))
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
