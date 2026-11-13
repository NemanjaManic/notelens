"""Read immutable prepared corpus artifacts; never clean, chunk, embed or fetch."""

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from types import MappingProxyType
from typing import Mapping


DEFAULT_MANIFEST = "data/knowledge/manifests/passages.json"
CLEANER_VERSION = "summary-html-to-text-v1"
META = ("topic_id", "title", "url", "language", "date_created", "synonyms", "groups", "source")
ORIGINAL_FIELDS = {"record_format_version", "topic_id", "title", "url", "language", "date_created",
                   "synonyms", "groups", "summary_format", "full_summary", "source"}
PASSAGE_FIELDS = set(META) | {"record_format_version", "passage_id", "topic_text_sha256",
    "cleaning_version", "chunking", "start", "end", "overlap_code_points", "text"}
SPECIALTIES = ("Cardiovascular / Pulmonary", "Orthopedic", "Gastroenterology", "Neurology", "Urology")
POLICY = {"version": "source-block-passages-v1", "unit": "unicode_code_points",
          "packing": "greedy_source_blocks", "tables": "whole", "long_paragraphs": "word_boundaries",
          "lists": "whole_items", "trailing_nih_attribution": "group_with_previous_unit_when_within_maximum",
          "overlap": "whole_trailing_paragraphs_or_items_when_next_unit_fits"}


class CorpusLoadError(ValueError):
    """A safe English diagnostic with no source text or filesystem values."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def require(condition, message, code="corpus_integrity_failure"):
    if not condition:
        raise CorpusLoadError(code, message)


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def valid_hash(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Prepared JSON contains duplicate object keys.", "corpus_format_invalid")
        result[key] = value
    return result


def finite_tree(value):
    require(not isinstance(value, float) or math.isfinite(value),
            "Prepared JSON contains a non-finite number.", "corpus_format_invalid")
    if isinstance(value, dict):
        for child in value.values(): finite_tree(child)
    elif isinstance(value, list):
        for child in value: finite_tree(child)


def parse_json(payload, label):
    try:
        if isinstance(payload, bytes): payload = payload.decode("utf-8")
        result = json.loads(payload, object_pairs_hook=unique_object)
        finite_tree(result)
        return result
    except CorpusLoadError:
        raise
    except (ValueError, UnicodeError, RecursionError):
        raise CorpusLoadError("corpus_format_invalid", f"{label} is not valid finite UTF-8 JSON.") from None


def owned_file(root, value, scope):
    require(isinstance(value, (str, Path)), "A prepared-file path is invalid.", "corpus_path_invalid")
    try:
        path = (root / value).resolve()
        boundary = (root / scope).resolve()
        require(boundary.is_relative_to(root) and path.is_relative_to(boundary),
                "A prepared-file path escapes its owned directory.", "corpus_path_invalid")
        return path
    except (OSError, RuntimeError):
        raise CorpusLoadError("corpus_path_invalid", "A prepared-file path cannot be resolved.") from None


def repository_directory(explicit):
    if explicit is not None:
        root = Path(explicit).resolve()
        require(root.is_dir(), "The configured repository directory is unavailable.", "corpus_file_missing")
        return root
    start = Path.cwd().resolve()
    for candidate in (start, *start.parents):
        if (candidate / "data/knowledge/manifests/snapshot.json").is_file():
            return candidate
    raise CorpusLoadError("corpus_file_missing", "Run from this checkout or supply its repository directory.")


def read_bytes(path, label, expected=None):
    try:
        payload = path.read_bytes()
    except FileNotFoundError:
        raise CorpusLoadError("corpus_file_missing", f"{label} is missing.") from None
    except OSError:
        raise CorpusLoadError("corpus_file_unreadable", f"{label} cannot be read.") from None
    if expected is not None:
        require(valid_hash(expected["sha256"]), f"{label} has an invalid recorded checksum.")
        require(sha256(payload) == expected["sha256"], f"{label} checksum does not match its manifest.")
        if "size_bytes" in expected:
            require(integer(expected["size_bytes"]) and len(payload) == expected["size_bytes"],
                    f"{label} size does not match its manifest.")
    return payload


def read_records(payload, label):
    lines = payload.decode("utf-8").split("\n")
    if lines and lines[-1] == "": lines.pop()
    require(bool(lines), f"{label} has no records.")
    records = [parse_json(line, label) for line in lines]
    require(all(isinstance(record, dict) for record in records), f"{label} must contain object records.", "corpus_format_invalid")
    return records


def check_policy(configuration):
    require(isinstance(configuration, dict)
            and set(configuration) == set(POLICY) | {"max_code_points", "overlap_code_points"}
            and all(configuration[key] == value for key, value in POLICY.items()),
            "The prepared passage policy is unsupported.", "corpus_format_invalid")
    require(integer(configuration["max_code_points"], 1) and integer(configuration["overlap_code_points"])
            and configuration["overlap_code_points"] < configuration["max_code_points"],
            "The prepared passage limits are invalid.", "corpus_format_invalid")


@dataclass(frozen=True, slots=True)
class PreparedPassage:
    topic_id: str
    passage_id: str
    title: str
    url: str
    language: str
    date_created: str | None
    synonyms: tuple[str, ...]
    groups: tuple[Mapping[str, str | None], ...]
    source: Mapping[str, str]
    specialties: tuple[str, ...]
    topic_text_sha256: str
    cleaning_version: str
    start: int
    end: int
    overlap_code_points: int
    text: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class PreparedCorpus:
    corpus_version: str
    snapshot_date: str
    manifest_sha256: str
    artifact_sha256: str
    configuration: Mapping
    topic_ids: tuple[str, ...]
    passages: tuple[PreparedPassage, ...] = field(repr=False)
    by_id: Mapping[str, PreparedPassage] = field(repr=False)
    by_topic_id: Mapping[str, tuple[PreparedPassage, ...]] = field(repr=False)

    @property
    def topic_count(self):
        return len(self.topic_ids)

    @property
    def passage_count(self):
        return len(self.passages)

    def summary(self):
        return {"status": "verified", "topics": self.topic_count, "passages": self.passage_count,
                "corpus_version": self.corpus_version, "snapshot_date": self.snapshot_date,
                "manifest_sha256": self.manifest_sha256, "artifact_sha256": self.artifact_sha256}


def load_corpus(*, repository_root=None, manifest=DEFAULT_MANIFEST, expected_corpus_version=None):
    try:
        return _load_corpus(repository_directory(repository_root), manifest, expected_corpus_version)
    except CorpusLoadError:
        raise
    except OSError:
        raise CorpusLoadError("corpus_file_unreadable", "The configured corpus directory cannot be accessed.") from None
    except (KeyError, TypeError, ValueError, AttributeError, RecursionError):
        raise CorpusLoadError("corpus_format_invalid", "Prepared corpus metadata or records have an invalid format.") from None


def _load_corpus(root, manifest_name, expected_version):
    manifest_path = owned_file(root, manifest_name, "data/knowledge/manifests")
    manifest_bytes = read_bytes(manifest_path, "Passage manifest")
    manifest = parse_json(manifest_bytes, "Passage manifest")
    require(type(manifest["manifest_version"]) is int and manifest["manifest_version"] == 1
            and manifest["stage"] == "passage_preparation", "Unsupported passage manifest version or stage.", "corpus_format_invalid")
    configuration = manifest["configuration"]
    check_policy(configuration)
    input_record, source = manifest["input"], manifest["source"]
    clean_path = owned_file(root, input_record["cleaned_manifest"], "data/knowledge/manifests")
    clean = parse_json(read_bytes(clean_path, "Cleaned-topic manifest",
                      {"sha256": input_record["cleaned_manifest_sha256"]}), "Cleaned-topic manifest")
    require(type(clean["manifest_version"]) is int and clean["manifest_version"] == 1 and clean["stage"] == "summary_cleaning"
            and clean["cleaner"]["version"] == CLEANER_VERSION and clean["source"] == source
            and clean["artifact"] == input_record["artifact"], "Cleaning and passage provenance do not match.")
    snapshot_path = owned_file(root, source["snapshot_manifest"], "data/knowledge/manifests")
    snapshot = parse_json(read_bytes(snapshot_path, "Source snapshot manifest",
                         {"sha256": source["snapshot_manifest_sha256"]}), "Source snapshot manifest")
    selection = snapshot["selection"]
    ids = selection["selected_topic_ids"]
    require(selection["status"] == "approved_initial_selection" and isinstance(ids, list) and bool(ids)
            and all(isinstance(value, str) and re.fullmatch(r"[0-9]+", value) for value in ids)
            and len(set(ids)) == len(ids) and integer(snapshot["counts"]["selected_unique_topics"], 1)
            and snapshot["counts"]["selected_unique_topics"] == len(ids),
            "The source selection approval, IDs or counts are invalid.")
    specialties = selection["selected_topic_ids_by_specialty"]
    require(set(specialties) == set(SPECIALTIES), "Source specialty mapping is invalid.")
    for values in specialties.values():
        require(isinstance(values, list) and len(set(values)) == len(values) and set(values) <= set(ids),
                "Source specialty membership is invalid.")
    require(set().union(*(set(values) for values in specialties.values())) == set(ids),
            "Selected topics are missing specialty membership.")
    topic_source = {"name": snapshot["source"]["name"], "snapshot_date": snapshot["source"]["release_date"],
                    "attribution": snapshot["source"]["attribution"], "archive_sha256": snapshot["archive"]["sha256"],
                    "xml_sha256": snapshot["archive"]["members"][0]["sha256"],
                    "selection_rule_version": selection["selection_rule_version"]}
    require(all(isinstance(value, str) and bool(value.strip()) for value in topic_source.values()),
            "Source identity is incomplete.")
    require(all(source[key] == topic_source[key] for key in
                ("snapshot_date", "attribution", "archive_sha256", "xml_sha256", "selection_rule_version")),
            "Manifest source identity does not match the snapshot.")
    clean_artifact = clean["artifact"]
    require(clean_artifact["format"] == manifest["artifact"]["format"] == "jsonl-utf8", "Unsupported corpus artifact format.", "corpus_format_invalid")
    clean_records = read_records(read_bytes(owned_file(root, clean_artifact["local_path"], "data/knowledge/.cache/corpus"),
                                 "Cleaned-topic artifact", clean_artifact), "Cleaned-topic artifact")
    topics = {}
    for topic in clean_records:
        require(set(topic) == ORIGINAL_FIELDS | {"cleaned_summary", "cleaning"}
                and type(topic["record_format_version"]) is int and topic["record_format_version"] == 1
                and topic["language"] == "English" and topic["summary_format"] == "source_html"
                and topic["source"] == topic_source, "A cleaned topic has unexpected fields or provenance.")
        require(topic["topic_id"] in ids and topic["topic_id"] not in topics, "A cleaned topic ID is missing, duplicated or unselected.")
        require(all(isinstance(topic[key], str) and bool(topic[key].strip()) for key in
                    ("title", "url", "full_summary", "cleaned_summary")), "A cleaned topic is missing required text or metadata.")
        require(topic["date_created"] is None or isinstance(topic["date_created"], str), "A source date is invalid.")
        require(isinstance(topic["synonyms"], list) and all(isinstance(value, str) for value in topic["synonyms"]), "Source synonyms are invalid.")
        require(isinstance(topic["groups"], list) and all(isinstance(group, dict) and set(group) == {"id", "name", "url"}
                and all(value is None or isinstance(value, str) for value in group.values()) for group in topic["groups"]), "Source groups are invalid.")
        cleaning = topic["cleaning"]
        require(cleaning["version"] == CLEANER_VERSION and cleaning["format"] == "plain_text"
                and valid_hash(cleaning["text_sha256"]) and sha256(topic["cleaned_summary"].encode("utf-8")) == cleaning["text_sha256"],
                "A canonical topic checksum or cleaning version is invalid.")
        topics[topic["topic_id"]] = topic
    require(set(topics) == set(ids) and integer(clean["counts"]["cleaned_topics"], 1)
            and clean["counts"]["cleaned_topics"] == len(ids), "Cleaned topics do not match the selected source set.")
    artifact = manifest["artifact"]
    rows = read_records(read_bytes(owned_file(root, artifact["local_path"], "data/knowledge/.cache/corpus"),
                        "Passage artifact", artifact), "Passage artifact")
    passages, by_id, by_topic = [], {}, defaultdict(list)
    previous_ends, previous_starts = defaultdict(int), defaultdict(lambda: -1)
    previous_key = None
    for row in rows:
        require(set(row) == PASSAGE_FIELDS and type(row["record_format_version"]) is int and row["record_format_version"] == 1,
                "A passage has unexpected fields or record version.")
        topic_id = row["topic_id"]
        require(topic_id in topics, "A passage references an unselected topic.")
        topic = topics[topic_id]
        require(all(row[key] == topic[key] for key in META), "Passage metadata does not match its source topic.")
        check_policy(row["chunking"])
        require(row["chunking"] == configuration and row["cleaning_version"] == CLEANER_VERSION
                and row["topic_text_sha256"] == topic["cleaning"]["text_sha256"], "Passage preparation identities do not match.")
        text, start, end = topic["cleaned_summary"], row["start"], row["end"]
        require(integer(start) and integer(end, 1) and start < end <= len(text)
                and end - start <= configuration["max_code_points"], "Passage code-point boundaries are invalid.")
        key = (int(topic_id), topic_id, start)
        require(previous_key is None or previous_key < key, "Passages are not in stable topic/position order.")
        previous_key = key
        require(row["text"] == text[start:end] and bool(row["text"].strip()), "Passage text does not match its canonical slice.")
        old_end = previous_ends[topic_id]
        require(start > previous_starts[topic_id] and end > old_end and not text[old_end:start].strip(),
                "Passages fail to advance or leave canonical content uncovered.")
        require(integer(row["overlap_code_points"]) and row["overlap_code_points"] == max(0, old_end - start)
                and row["overlap_code_points"] <= configuration["overlap_code_points"], "Passage overlap is invalid.")
        identity = {"configuration": configuration, "topic": {key: row[key] for key in META},
                    "topic_text_sha256": row["topic_text_sha256"], "start": start, "end": end}
        expected_id = f"mplus-{topic_id}-" + sha256(json.dumps(identity, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8"))
        require(row["passage_id"] == expected_id and expected_id not in by_id, "A passage ID is invalid or duplicated.")
        passage = PreparedPassage(topic_id=topic_id, passage_id=expected_id, title=row["title"], url=row["url"],
            language=row["language"], date_created=row["date_created"], synonyms=tuple(row["synonyms"]),
            groups=tuple(MappingProxyType(dict(group)) for group in row["groups"]), source=MappingProxyType(dict(row["source"])),
            specialties=tuple(category for category in SPECIALTIES if topic_id in specialties[category]),
            topic_text_sha256=row["topic_text_sha256"], cleaning_version=row["cleaning_version"],
            start=start, end=end, overlap_code_points=row["overlap_code_points"], text=row["text"])
        passages.append(passage); by_id[expected_id] = passage; by_topic[topic_id].append(passage)
        previous_ends[topic_id], previous_starts[topic_id] = end, start
    require(set(by_topic) == set(ids), "Passages do not cover every selected topic.")
    require(all(not topics[key]["cleaned_summary"][previous_ends[key]:].strip() for key in ids), "Passages leave trailing canonical content uncovered.")
    counts = manifest["counts"]
    require(integer(counts["topics"]) and integer(counts["passages"]) and counts["topics"] == len(ids)
            and counts["passages"] == len(passages) and isinstance(counts["passages_by_topic_id"], dict)
            and all(integer(value, 1) for value in counts["passages_by_topic_id"].values())
            and counts["passages_by_topic_id"] == dict(Counter(row["topic_id"] for row in rows)),
            "Prepared passage counts do not match the actual records.")
    corpus_identity = {"cleaned_artifact_sha256": clean_artifact["sha256"], "passage_artifact_sha256": artifact["sha256"],
                       "configuration": configuration}
    version = sha256(json.dumps(corpus_identity, sort_keys=True).encode("utf-8"))
    require(valid_hash(manifest["corpus_version"]) and version == manifest["corpus_version"], "The corpus version does not match its recorded inputs.")
    if expected_version is not None:
        require(valid_hash(expected_version) and version == expected_version, "The loaded corpus does not match the expected version.", "corpus_version_mismatch")
    return PreparedCorpus(corpus_version=version, snapshot_date=topic_source["snapshot_date"],
        manifest_sha256=sha256(manifest_bytes), artifact_sha256=artifact["sha256"],
        configuration=MappingProxyType(dict(configuration)), topic_ids=tuple(sorted(ids, key=lambda value: (int(value), value))),
        passages=tuple(passages), by_id=MappingProxyType(by_id),
        by_topic_id=MappingProxyType({key: tuple(values) for key, values in by_topic.items()}))


def main():
    parser = argparse.ArgumentParser(description="Verify and load prepared public corpus records without indexing.")
    parser.add_argument("--repository-root")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--expected-corpus-version")
    arguments = parser.parse_args()
    try:
        corpus = load_corpus(repository_root=arguments.repository_root, manifest=arguments.manifest,
                             expected_corpus_version=arguments.expected_corpus_version)
    except CorpusLoadError as error:
        print(json.dumps({"status": "error", "code": error.code, "message": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(corpus.summary()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
