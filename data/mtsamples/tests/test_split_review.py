"""Synthetic review records test quarantine and exposure invariants."""

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from freeze_splits import FOUNDATION_COMMIT, SPLITS, VERSION, json_bytes, verify_frozen
from prepare_split_review import build_review
from preview_reviewed_split import preview
from record_split_review import record_access, record_decision, reserve_pair


def group(group_id, split, *, quarantined=False):
    return {"group_id": group_id, "draft_split": split, "labels": ["Neurology"],
            "flags": ["unresolved_near_candidate"] if quarantined else [],
            "documents": [{"document_id": f"document-{group_id}", "transcription": "SYNTHETIC_BODY_MARKER"}]}


class SplitReviewTests(unittest.TestCase):
    def setUp(self):
        self.draft = {
            "status": "DRAFT", "source_sha256": "source",
            "groups": [group("train", "train"), group("validation", "validation"), group("heldout", "test"),
                       group("left", None, quarantined=True), group("right", None, quarantined=True)],
            "near_candidates": [{"group_a": "left", "group_b": "right", "intersection": 9,
                                 "shingles_a": 9, "shingles_b": 10, "decision": "unresolved"}],
        }
        self.receipt = {"source_sha256": "source", "split_sha256": "draft", "test_scored": False,
                        "train_rows": 1, "train_groups": 1, "validation_rows": 1, "validation_groups": 1}

    def test_pending_queue_and_exposure_exclude_document_text_and_heldout_ids(self):
        queue, exposure = build_review(self.draft, self.receipt, "draft", "receipt")
        self.assertEqual(queue["pairs"][0]["status"], "pending_review")
        self.assertEqual(queue["pairs"][0]["containment"], 1.0)
        self.assertEqual(exposure["training"], [{"group_id": "train", "document_ids": ["document-train"]}])
        self.assertNotIn("heldout", str((queue, exposure)))
        self.assertNotIn("SYNTHETIC_BODY_MARKER", str((queue, exposure)))

    def test_mismatched_or_test_scored_receipt_is_rejected(self):
        with self.assertRaises(ValueError):
            build_review(self.draft, self.receipt, "other", "receipt")
        self.receipt["test_scored"] = True
        with self.assertRaises(ValueError):
            build_review(self.draft, self.receipt, "draft", "receipt")

    def test_duplicate_pair_cannot_include_an_assigned_group(self):
        self.draft["near_candidates"][0]["group_b"] = "train"
        with self.assertRaisesRegex(ValueError, "not quarantined"):
            build_review(self.draft, self.receipt, "draft", "receipt")

    def test_frozen_verification_needs_only_pinned_manifests(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)
            checksums = {}
            for split in SPLITS:
                name = f"{split}.json"
                payload = json_bytes({"split": split, "groups": []})
                (path / name).write_bytes(payload)
                checksums[name] = sha256(payload).hexdigest()
            summary = {"status": "frozen local split membership", "manifest_version": VERSION,
                       "foundation_commit": FOUNDATION_COMMIT, "split_checksums": checksums}
            summary_bytes = json_bytes(summary)
            (path / "manifest.json").write_bytes(summary_bytes)
            pin = sha256(summary_bytes).hexdigest()
            self.assertEqual(verify_frozen(path, pin), summary)
            with self.assertRaisesRegex(ValueError, "pinned SHA-256"):
                verify_frozen(path, "0" * 64)
            (path / "test.json").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "partition differs"):
                verify_frozen(path, pin)


def candidate(left, right):
    return {"group_a": left, "group_b": right, "intersection": 9,
            "shingles_a": 9, "shingles_b": 10, "decision": "unresolved"}


class SplitPreviewTests(unittest.TestCase):
    def setUp(self):
        self.draft = {
            "status": "DRAFT", "source_sha256": "source", "summary": {"target_rows": 6},
            "allocation": {"seed": "synthetic-review-v1"},
            "groups": [group("train", "train"), group("validation", "validation"), group("heldout", "test"),
                       *(group(name, None, quarantined=True) for name in ("left", "middle", "right"))],
            "near_candidates": [candidate("left", "middle"), candidate("middle", "right")],
        }
        self.receipt = {"source_sha256": "source", "split_sha256": "draft", "test_scored": False,
                        "train_rows": 1, "train_groups": 1, "validation_rows": 1, "validation_groups": 1}
        self.reset_inputs()

    def reset_inputs(self):
        self.generated, self.model_exposure = build_review(self.draft, self.receipt, "draft", "receipt")
        self.queue = deepcopy(self.generated)
        self.exposure = deepcopy(self.model_exposure)

    def record_exposure(self, *names):
        self.exposure["reviews"] = [
            {"group_id": name, "document_ids": [f"document-{name}"], "reviewer": "Synthetic reviewer",
             "purpose": "Synthetic test", "review_date": "2026-11-19"}
            for name in names
        ]

    def decide(self, index, decision):
        self.queue["pairs"][index].update(
            status="reviewed", decision=decision, reviewer="Synthetic reviewer",
            review_date="2026-11-19", reason="Synthetic test"
        )

    def check(self):
        return preview(self.draft, self.queue, self.exposure, self.generated, self.model_exposure)

    def test_pending_pairs_keep_all_members_quarantined(self):
        report = self.check()
        self.assertEqual(report["pair_status_counts"], {"pending_review": 2})
        self.assertEqual(report["unassigned_components"], 3)
        self.assertEqual(report["retained_partitions"]["test"]["documents"], 1)
        self.assertNotIn("heldout", str(report))
        self.queue["pairs"].reverse()
        self.assertEqual(self.check(), report)

    def test_confirmed_duplicates_merge_transitively_and_stay_development_only(self):
        self.record_exposure("left", "middle", "right")
        self.decide(0, "duplicate")
        self.decide(1, "duplicate")
        report = self.check()
        self.assertEqual(report["eligible_needing_assignment"], [
            {"group_ids": ["left", "middle", "right"], "label": "Neurology", "documents": 3,
             "development_only": True}
        ])
        self.assertEqual(report["unassigned_components"], 1)
        change, = report["group_changes"]
        self.assertEqual([entry["group_id"] for entry in change["previous_groups"]], ["left", "middle", "right"])
        self.assertEqual([entry["document_ids"] for entry in change["previous_groups"]],
                         [["document-left"], ["document-middle"], ["document-right"]])
        self.assertEqual(len(change["new_group_id"]), 70)
        self.assertIsNone(change["proposed_split"])
        self.assertTrue(change["development_only"])

    def test_unresolved_edge_quarantines_the_merged_component(self):
        self.record_exposure("left", "middle")
        self.decide(0, "duplicate")
        report = self.check()
        self.assertEqual(report["eligible_needing_assignment"], [])
        self.assertIn({"group_ids": ["left", "middle"], "flags": ["pending_review"], "development_only": True},
                      report["components_needing_review"])

    def test_merge_with_conflicting_labels_stays_excluded(self):
        self.draft["groups"][-1]["labels"] = ["Urology"]
        self.reset_inputs()
        self.record_exposure("left", "middle", "right")
        self.decide(0, "duplicate")
        self.decide(1, "duplicate")
        report = self.check()
        self.assertEqual(report["eligible_needing_assignment"], [])
        self.assertEqual(report["flagged_components_by_reason"], {"conflicting_target_labels": 1})

    def test_exposure_blocks_heldout_retention(self):
        self.record_exposure("heldout")
        report = self.check()
        self.assertEqual(report["retained_partitions"]["test"]["documents"], 0)
        self.assertEqual(report["flagged_components_by_reason"]["heldout_component_exposed"], 1)

    def test_review_decision_without_exposure_stays_quarantined(self):
        self.decide(0, "non_duplicate")
        report = self.check()
        self.assertEqual(report["pair_status_counts"], {"missing_review_exposure": 1, "pending_review": 1})
        self.assertEqual(report["eligible_needing_assignment"], [])

    def test_contradictory_transitive_decisions_are_rejected(self):
        self.draft["near_candidates"].append(candidate("left", "right"))
        self.reset_inputs()
        self.record_exposure("left", "middle", "right")
        self.decide(0, "duplicate")
        self.decide(1, "duplicate")
        self.decide(2, "non_duplicate")
        with self.assertRaisesRegex(ValueError, "transitive"):
            self.check()

    def test_tampering_with_queue_or_model_exposure_is_rejected(self):
        self.queue["pairs"][0]["intersection"] = 7
        with self.assertRaisesRegex(ValueError, "generated queue"):
            self.check()
        self.reset_inputs()
        self.exposure["training"] = []
        with self.assertRaisesRegex(ValueError, "development receipt"):
            self.check()

    def test_reservation_uses_original_pair_number_when_queue_is_reordered(self):
        self.queue["pairs"].reverse()
        updated = reserve_pair(
            self.queue, self.exposure, self.generated, 1, "Synthetic reviewer", "2026-11-19", "Synthetic test"
        )
        self.assertNotIn("reviews", self.exposure)
        self.assertEqual({entry["group_id"] for entry in updated["reviews"]}, {"left", "middle"})
        repeated = reserve_pair(
            self.queue, updated, self.generated, 1, "Synthetic reviewer", "2026-11-19", "Synthetic test"
        )
        self.assertEqual(repeated, updated)

    def test_decision_requires_prior_exposure_and_returns_new_valid_queue(self):
        with self.assertRaisesRegex(ValueError, "recorded exposure"):
            record_decision(self.draft, self.queue, self.exposure, self.generated, 1, "Synthetic reviewer",
                            "2026-11-19", "duplicate", "Synthetic test")
        self.exposure = reserve_pair(
            self.queue, self.exposure, self.generated, 1, "Synthetic reviewer", "2026-11-19", "Synthetic test"
        )
        with self.assertRaisesRegex(ValueError, "recorded exposure"):
            record_decision(self.draft, self.queue, self.exposure, self.generated, 1, "Synthetic reviewer",
                            "2026-11-18", "duplicate", "Synthetic test")
        updated = record_decision(
            self.draft, self.queue, self.exposure, self.generated, 1, "Synthetic reviewer",
            "2026-11-19", "duplicate", "Synthetic test"
        )
        self.assertEqual(self.queue["pairs"][0]["status"], "pending_review")
        self.queue = updated
        report = self.check()
        self.assertEqual(report["pair_status_counts"], {"duplicate": 1, "pending_review": 1})
        self.assertIn({"group_ids": ["left", "middle"], "flags": ["pending_review"], "development_only": True},
                      report["components_needing_review"])

    def test_versioned_reservation_guards_test_but_does_not_record_actual_access(self):
        version = self.draft["allocation"]["seed"]
        self.exposure = reserve_pair(
            self.queue, self.exposure, self.generated, 1, "Synthetic reviewer", "2026-11-19", "Synthetic test",
            split_version=version, reserved_at="2026-11-19T10:00:00+01:00"
        )
        self.assertEqual(self.check()["development_groups_recorded"], 4)
        self.assertNotIn("accesses", self.exposure)
        with self.assertRaisesRegex(ValueError, "recorded exposure"):
            record_decision(self.draft, self.queue, self.exposure, self.generated, 1, "Synthetic reviewer",
                            "2026-11-19", "duplicate", "Synthetic test")

        prior = self.exposure
        self.exposure = record_access(
            self.queue, prior, self.generated, 1, "Synthetic reviewer", "2026-11-19T09:59:59+01:00",
            ["document-left"], "Synthetic comparison", version
        )
        with self.assertRaisesRegex(ValueError, "follow a reservation"):
            self.check()
        self.exposure = record_access(
            self.queue, prior, self.generated, 1, "Synthetic reviewer", "2026-11-19T10:05:00+01:00",
            ["document-left", "document-middle"], "Synthetic comparison", version
        )
        self.assertEqual(self.exposure["accesses"][0]["split_version"], version)
        self.assertEqual(self.exposure["accesses"][0]["reviewed"], "Synthetic comparison")
        with self.assertRaisesRegex(ValueError, "outside the selected pair"):
            record_access(self.queue, self.exposure, self.generated, 1, "Synthetic reviewer",
                          "2026-11-19T10:05:00+01:00", ["document-heldout"], "Synthetic test", version)
        self.queue = record_decision(
            self.draft, self.queue, self.exposure, self.generated, 1, "Synthetic reviewer",
            "2026-11-19", "duplicate", "Synthetic test"
        )
        self.assertEqual(self.check()["pair_status_counts"], {"duplicate": 1, "pending_review": 1})
