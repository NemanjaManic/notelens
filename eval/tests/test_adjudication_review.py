"""Protect complete coverage and safe rendering of restricted review material."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
SPEC = importlib.util.spec_from_file_location("adjudication_builder", TOOLS / "build_adjudication_review.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def packet():
    text = "Synthetic </script><script>unsafe()</script> 🩺 source."
    return {
        "expected_assignment_ids": ["synthetic"],
        "documents": {"synthetic": {"assignment_id": "synthetic", "canonical_text": text,
            "text_sha256": hashlib.sha256(text.encode()).hexdigest(), "entities": []}},
        "items": [{"item_id": "new", "assignment_id": "synthetic", "category": "synthetic",
                   "covers": ["new"], "source_anchors": [{"start": 0, "end": len(text), "quote": text}]}],
        "previously_resolved_item_ids": ["earlier"], "required_coverage_ids": ["earlier", "new"],
    }


def test_render_preserves_packet_bytes_and_escapes_script_payload(tmp_path):
    source = tmp_path / "input.json"
    raw = (json.dumps(packet(), ensure_ascii=False) + "\n").encode()
    source.write_bytes(raw)
    receipt = builder.build(source, tmp_path / "out")
    assert (tmp_path / "out/packet.json").read_bytes() == raw
    rendered = (tmp_path / "out/review.html").read_text(encoding="utf-8")
    assert "</script><script>unsafe()" not in rendered
    assert "\\u003c/script\\u003e" in rendered
    assert receipt["coverage_ids_accounted_for"] == 2
    assert receipt["human_decisions_generated"] == 0
    assert receipt["full_d013_closed"] is False


@pytest.mark.parametrize("change", ["omit_document", "omit_item", "duplicate_id", "double_coverage", "wrong_source", "wrong_anchor"])
def test_incomplete_or_mismatched_packet_is_rejected(change):
    data = copy.deepcopy(packet())
    if change == "omit_document":
        data["documents"] = {}
    elif change == "omit_item":
        data["items"] = []
    elif change == "duplicate_id":
        data["items"].append(copy.deepcopy(data["items"][0]))
    elif change == "double_coverage":
        data["items"][0]["covers"] = ["earlier", "new"]
    elif change == "wrong_source":
        data["documents"]["synthetic"]["canonical_text"] += "changed"
    else:
        data["items"][0]["source_anchors"][0]["quote"] = "wrong"
    with pytest.raises(ValueError):
        builder.validate(data)
