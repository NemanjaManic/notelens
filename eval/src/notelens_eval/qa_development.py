"""Inventory development-only questions backed by synthetic and pinned public evidence."""

import argparse
from collections import Counter
import json
from pathlib import Path

from notelens_extraction.contracts import validate_schema

from .qa_inventory import ROOT, digest, inventory, load_pinned_passages
from .suite import validate_references


SOURCE_PATHS = {
    "document_fixture": "eval/fixtures/extraction-qa-synthetic-v1.json",
    "literature_proposal": "docs/rag/qa-proposals.json",
    "literature_source_review": "eval/references/qa/a-public-qa-pinned-source-review-v1.json",
    "corpus_manifest": "data/knowledge/manifests/passages.json",
}
DEFAULT_MANIFEST = ROOT / "eval/datasets/qa/cross-module-development-v1.json"
CITATION_FIELDS = ("topic_id", "passage_id", "passage_start", "passage_end", "quote_sha256")


def combined_state(states: set[str]) -> str:
    return next(iter(states)) if len(states) == 1 else "partial"


def literature_state(parts: list[dict]) -> str:
    return combined_state({"sufficient" if part["verified_citations"] else "insufficient" for part in parts})


def document_expectation(case_id: str, qa: dict) -> dict:
    return {"case_id": case_id, "qa_id": qa["id"], "state": qa["expected_evidence_state"],
            "required_fact_ids": [fact["fact_id"] for fact in qa["required_facts"]],
            "expected_gaps": qa["expected_gaps"]}


def literature_expectation(case_id: str, parts: list[dict]) -> dict:
    citations = [ref for part in parts for ref in part["verified_citations"]]
    return {"case_id": case_id, "parts": [part["part"] for part in parts], "state": literature_state(parts),
            "topic_ids": sorted({ref["topic_id"] for ref in citations}),
            "passage_ids": sorted({ref["passage_id"] for ref in citations})}


def reviewed_literature(proposal: dict, review: dict, corpus: dict) -> dict:
    artifact = review["passage_artifact"]
    if (review["partition"], artifact["corpus_version"], artifact["sha256"]) != (
        "development_candidate", corpus["corpus_version"], corpus["artifact"]["sha256"],
    ):
        raise ValueError("The source review does not cover the pinned development corpus.")
    reviewed = {row["id"]: row for row in review["cases"]}
    if len(reviewed) != len(review["cases"]) or reviewed.keys() != {case["id"] for case in proposal["cases"]}:
        raise ValueError("The source review must cover each literature case exactly once.")
    states = {"sufficient": "full", "partial": "partial", "insufficient": "none"}
    for proposal_case in proposal["cases"]:
        row = reviewed[proposal_case["id"]]
        for index, (part, reviewed_part) in enumerate(zip(proposal_case["parts"], row["parts"], strict=True), 1):
            citations = [{key: ref[key] for key in CITATION_FIELDS} for ref in part["evidence"]]
            outcome = "supported_by_pinned_source" if citations else "gap_in_pinned_snapshot"
            if (reviewed_part["part"], reviewed_part["outcome"], reviewed_part["verified_citations"]) != (
                index, outcome, citations,
            ):
                raise ValueError("Reviewed literature parts differ from the pinned proposal evidence.")
        if row["snapshot_answerability"] != states[literature_state(row["parts"])]:
            raise ValueError("Reviewed literature answerability differs from its parts.")
    return reviewed


def source_groups(cases: dict) -> dict:
    """Group connected cases by canonical document, literature origin or passage reuse."""
    owners = {}
    components = {}
    for case_id, row in cases.items():
        group = {case_id}
        keys = []
        if "document_sha256" in row:
            keys.append(("document", row["document_sha256"]))
        if "literature" in row:
            keys.append(("literature_case", row["literature"]["case_id"]))
            keys.extend(("passage", passage) for passage in row["literature"]["passage_ids"])
        for key in keys:
            group.update(components.get(owners.setdefault(key, case_id), ()))
        for member in group:
            components[member] = group
    groups = {min(group): sorted(group) for group in components.values()}
    return dict(sorted(groups.items()))


def build_inventory(manifest: dict, documents: dict, proposal: dict, review: dict, corpus: dict,
                    passages: dict | None = None) -> dict:
    if manifest["partition"] != "development_candidate":
        raise ValueError("The cross-module inventory accepts development candidates only.")
    validate_references(documents)
    citations = inventory(proposal, corpus, passages)
    literature = reviewed_literature(proposal, review, corpus)
    cases = {}
    questions = {}
    overlap = []
    document_qa = {}
    for source in documents["cases"]:
        doc = source["request"]["document"]
        for qa in source["qa"]:
            source_key = (source["id"], qa["id"])
            document_qa[source_key] = (source["request"], qa)
            case_id = f"D-DOC/{source['id']}/{qa['id']}"
            fingerprint = (doc["text_sha256"], " ".join(qa["question"].casefold().split()))
            if fingerprint in questions:
                kept = questions[fingerprint]
                kept_doc = cases[kept]["document"]
                _, retained = document_qa[(kept_doc["case_id"], kept_doc["qa_id"])]
                if any(qa[key] != retained[key] for key in ("expected_evidence_state", "expected_support", "expected_gaps")):
                    raise ValueError("Duplicate document questions disagree on their reference outcome.")
                overlap.append({"retained_id": kept, "excluded_id": case_id})
                continue
            questions[fingerprint] = case_id
            cases[case_id] = {"scope": "document", "state": qa["expected_evidence_state"],
                              "document_sha256": doc["text_sha256"], "document": document_expectation(source["id"], qa)}
    for case_id, row in literature.items():
        if case_id in cases:
            raise ValueError("Duplicate development case ID.")
        expectation = literature_expectation(case_id, row["parts"])
        cases[case_id] = {"scope": "literature", "state": expectation["state"], "literature": expectation}
    for mixed in manifest["mixed_cases"]:
        case_id = mixed["id"]
        if not case_id or case_id in cases:
            raise ValueError("Duplicate or empty development case ID.")
        request, qa = document_qa[(mixed["document_case_id"], mixed["document_qa_id"])]
        doc = request["document"]
        question = mixed["question"]
        validate_schema({**request, "question": question}, "DocumentQuestionRequest", document=doc)
        fingerprint = (doc["text_sha256"], " ".join(question.casefold().split()))
        if fingerprint in questions:
            raise ValueError("Mixed question repeats an existing question on the same document.")
        questions[fingerprint] = case_id
        a_case = literature[mixed["literature_case_id"]]
        part_numbers = mixed["literature_parts"]
        if not part_numbers or len(set(part_numbers)) != len(part_numbers) or any(
            type(number) is not int or not 1 <= number <= len(a_case["parts"]) for number in part_numbers
        ):
            raise ValueError("Mixed questions need unique, existing literature parts.")
        a_expected = literature_expectation(a_case["id"], [a_case["parts"][number - 1] for number in part_numbers])
        d_expected = document_expectation(mixed["document_case_id"], qa)
        state = combined_state({d_expected["state"], a_expected["state"]})
        if state != mixed["expected_state"]:
            raise ValueError("Mixed answerability differs from the selected document and literature parts.")
        cases[case_id] = {"scope": "mixed", "state": state, "document_sha256": doc["text_sha256"],
                          "document": d_expected, "literature": a_expected}
    groups = source_groups(cases)
    return {
        "version": manifest["version"], "partition": manifest["partition"], "cases": len(cases),
        "by_scope_and_state": {scope: Counter(row["state"] for row in cases.values() if row["scope"] == scope)
                               for scope in ("document", "literature", "mixed")},
        "requests_with_unavailable_parts": sum(row["state"] != "sufficient" for row in cases.values()),
        "multi_source_requests": sum(row["scope"] == "mixed" or len(row.get("literature", {}).get("topic_ids", ())) > 1
                                     for row in cases.values()),
        "cases_with_more_than_five_literature_topics": [case_id for case_id, row in cases.items()
                                                        if len(row.get("literature", {}).get("topic_ids", ())) > 5],
        "duplicate_document_questions": overlap, "source_groups": groups,
        "verified_proposal_slices_this_run": citations["verified_passage_slices"],
        "case_references": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--passages", type=Path, help="Reverify the original citation slices against the pinned JSONL.")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_bytes())
        sources = {}
        for key, relative in SOURCE_PATHS.items():
            raw = (ROOT / relative).read_bytes()
            if manifest["inputs"][key] != {"path": relative, "sha256": digest(raw)}:
                raise ValueError(f"Development source pin differs for {key}.")
            sources[key] = json.loads(raw)
        corpus = sources["corpus_manifest"]
        passages = load_pinned_passages(args.passages, corpus) if args.passages else None
        result = build_inventory(manifest, sources["document_fixture"], sources["literature_proposal"],
                                 sources["literature_source_review"], corpus, passages)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
