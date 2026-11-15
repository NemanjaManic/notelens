"""Prepare approved public MedlinePlus topics locally with traceable source text."""

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import platform
import re
import statistics
import xml.etree.ElementTree as ET
import zipfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT = "data/knowledge/manifests/snapshot.json"
OUTPUT = "data/knowledge/.cache/corpus/selected-topics.jsonl"
REPORT = "data/knowledge/manifests/prepared-corpus.json"
EXTRACTOR_VERSION = "source-topic-extraction-v1"
CLEAN_OUTPUT = "data/knowledge/.cache/corpus/cleaned-topics.jsonl"
CLEAN_REPORT = "data/knowledge/manifests/cleaned-corpus.json"
CLEANER_VERSION = "summary-html-to-text-v1"
PASSAGE_OUTPUT = "data/knowledge/.cache/corpus/passages.jsonl"
PASSAGE_REPORT = "data/knowledge/manifests/passages.json"
CHUNKER_VERSION = "source-block-passages-v1"
MAX_CODE_POINTS = 2500
OVERLAP_CODE_POINTS = 300


class CorpusPreparationError(ValueError):
    """The local source or approved selection cannot be extracted faithfully."""


def owned_path(root, value, scope):
    root = Path(root).resolve()
    path = (root / value).resolve()
    boundary = (root / scope).resolve()
    if not boundary.is_relative_to(root) or not path.is_relative_to(boundary):
        raise CorpusPreparationError("Input or output path is outside its owned data directory.")
    return path


def extract_records(snapshot, payload):
    """Select source records without normalizing, cleaning or following their links."""
    selection = snapshot["selection"]
    selected_ids = selection["selected_topic_ids"]
    if selection["status"] != "approved_initial_selection":
        raise CorpusPreparationError("An approved initial selection is required.")
    if (not isinstance(selected_ids, list) or not selected_ids
            or any(not isinstance(value, str) or not re.fullmatch(r"[0-9]+", value)
                   for value in selected_ids)):
        raise CorpusPreparationError("Selected topic IDs must be nonempty numeric strings.")
    if len(set(selected_ids)) != len(selected_ids):
        raise CorpusPreparationError("The approved selection contains duplicate IDs.")
    if snapshot["counts"]["selected_unique_topics"] != len(selected_ids):
        raise CorpusPreparationError("The recorded selection count does not match the selected IDs.")
    if not selection["selection_rule_version"] or not snapshot["source"]["attribution"]:
        raise CorpusPreparationError("Selection version and source attribution are required.")

    xml_text = payload.decode("utf-8-sig")
    if "<!ENTITY" in xml_text:
        raise CorpusPreparationError("XML entity declarations are not permitted.")
    root = ET.fromstring(xml_text)
    if root.tag != "health-topics":
        raise CorpusPreparationError("Expected a MedlinePlus health-topics XML root.")
    topics = root.findall("health-topic")
    if (int(root.get("total", "-1")) != len(topics)
            or snapshot["counts"]["source_topics"] != len(topics)):
        raise CorpusPreparationError("The source topic count does not match the XML records.")
    by_id = {}
    for topic in topics:
        topic_id = topic.get("id")
        if not topic_id or topic_id in by_id:
            raise CorpusPreparationError("The source has a missing or duplicate topic ID.")
        by_id[topic_id] = topic
    if set(selected_ids) - by_id.keys():
        raise CorpusPreparationError("One or more selected topic IDs are missing from the source.")

    member = snapshot["archive"]["members"][0]
    provenance = {
        "name": snapshot["source"]["name"],
        "snapshot_date": snapshot["source"]["release_date"],
        "attribution": snapshot["source"]["attribution"],
        "archive_sha256": snapshot["archive"]["sha256"],
        "xml_sha256": member["sha256"],
        "selection_rule_version": selection["selection_rule_version"],
    }
    rows = []
    for topic_id in sorted(selected_ids, key=lambda value: (int(value), value)):
        topic = by_id[topic_id]
        if topic.get("language") != "English":
            raise CorpusPreparationError("Every selected topic must be English.")
        if any(not topic.get(field, "").strip() for field in ("title", "url")):
            raise CorpusPreparationError("A selected topic is missing required metadata.")
        summaries = topic.findall("full-summary")
        if len(summaries) != 1:
            raise CorpusPreparationError("A selected topic must have exactly one full summary.")
        summary = summaries[0]
        if len(summary):
            raise CorpusPreparationError("The selected topic summary structure is unsupported.")
        if not (summary.text or "").strip():
            raise CorpusPreparationError("A selected topic has an empty summary.")
        rows.append({
            "record_format_version": 1,
            "topic_id": topic_id,
            "title": topic.get("title"),
            "url": topic.get("url"),
            "language": topic.get("language"),
            "date_created": topic.get("date-created"),
            "synonyms": [node.text or "" for node in topic.findall("also-called")],
            "groups": [{"id": node.get("id"), "name": node.text or "", "url": node.get("url")}
                       for node in topic.findall("group")],
            "summary_format": "source_html",
            "full_summary": summary.text,
            "source": provenance,
        })
    return rows


def extract_corpus(repository_root=REPOSITORY_ROOT, *, snapshot_manifest=SNAPSHOT,
                   output=OUTPUT, output_manifest=REPORT):
    """Verify the local snapshot and write new extraction artifacts without overwrite."""
    root = Path(repository_root).resolve()
    snapshot_path = owned_path(root, snapshot_manifest, "data/knowledge/manifests")
    output_path = owned_path(root, output, "data/knowledge/.cache/corpus")
    report_path = owned_path(root, output_manifest, "data/knowledge/manifests")
    for target in (output_path, report_path):
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite an existing output: {target.relative_to(root)}")

    snapshot_bytes = snapshot_path.read_bytes()
    snapshot = json.loads(snapshot_bytes)
    record = snapshot["archive"]
    archive_path = owned_path(root, record["local_path"], "data/knowledge/raw")
    if archive_path.stat().st_size != record["size_bytes"]:
        raise CorpusPreparationError("Source archive size does not match the approved snapshot.")
    with archive_path.open("rb") as source:
        if hashlib.file_digest(source, "sha256").hexdigest() != record["sha256"]:
            raise CorpusPreparationError("Source archive checksum does not match the approved snapshot.")
    members = record["members"]
    if len(members) != 1 or not members[0]["name"].endswith(".xml"):
        raise CorpusPreparationError("The approved snapshot must identify one XML member.")
    member = members[0]
    with zipfile.ZipFile(archive_path) as archive:
        entries = [entry for entry in archive.infolist() if not entry.is_dir()]
        if len(entries) != 1 or entries[0].filename != member["name"]:
            raise CorpusPreparationError("ZIP members do not match the approved snapshot.")
        if entries[0].file_size != member["size_bytes"]:
            raise CorpusPreparationError("XML member size does not match the approved snapshot.")
        payload = archive.read(entries[0])
    if hashlib.sha256(payload).hexdigest() != member["sha256"]:
        raise CorpusPreparationError("XML member checksum does not match the approved snapshot.")
    rows = extract_records(snapshot, payload)
    output_bytes = b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
        for row in rows
    )
    report = {
        "manifest_version": 1,
        "owner": "Nemanja (A)",
        "task": "A-002",
        "stage": "extraction_only",
        "status": "extracted_not_cleaned_or_chunked",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "extractor": {"version": EXTRACTOR_VERSION, "python_version": platform.python_version(),
                      "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "source": {
            "snapshot_manifest": snapshot_path.relative_to(root).as_posix(),
            "snapshot_manifest_sha256": hashlib.sha256(snapshot_bytes).hexdigest(),
            "archive_path": archive_path.relative_to(root).as_posix(),
            "archive_sha256": record["sha256"],
            "xml_member": member["name"],
            "xml_sha256": member["sha256"],
            "download_url": record["download_url"],
            "snapshot_date": snapshot["source"]["release_date"],
            "attribution": snapshot["source"]["attribution"],
            "selection_rule_version": snapshot["selection"]["selection_rule_version"],
        },
        "artifact": {"local_path": output_path.relative_to(root).as_posix(), "format": "jsonl-utf8",
                     "size_bytes": len(output_bytes), "sha256": hashlib.sha256(output_bytes).hexdigest()},
        "counts": {"source_topics": snapshot["counts"]["source_topics"], "selected_topics": len(rows),
                   "extracted_topics": len(rows), "topics_with_synonyms": sum(bool(row["synonyms"]) for row in rows),
                   "cleaned_topics": None, "passages": None},
        "checks": {"archive_and_xml_checksums": "passed", "zip_member_crc": "passed",
                   "exact_selected_id_set": "passed", "english_and_nonempty_summaries": "passed"},
        "limitations": ["Source HTML is preserved; it has not been cleaned, rendered or chunked.",
                        "No linked content or evaluation QA is extracted; no network or provider calls are made.",
                        "A-002 remains incomplete until later approved cleaning/passage increments pass."],
    }
    report_bytes = (json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    created = []
    try:
        for target, content in ((output_path, output_bytes), (report_path, report_bytes)):
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as destination:
                created.append(target)
                destination.write(content)
    except OSError:
        for target in reversed(created):
            target.unlink()
        raise
    return report


class SummaryTextParser(HTMLParser):
    """Convert the supported summary markup without rendering or fetching anything."""

    INLINE = {"a", "strong", "em", "u", "b", "i", "span", "sup", "sub"}
    BLOCK = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "div"}
    TABLE = {"table", "thead", "tbody", "tfoot", "tr", "th", "td"}
    VOID = {"br", "img"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.blocks = []
        self.fragments = []
        self.prefix = ""
        self.list_depth = 0
        self.table_rows = None
        self.row = None
        self.cell = None
        self.has_visible_text = False
        self.stats = {"tables": 0, "omitted_images": 0, "omitted_comments": 0}

    def flush(self):
        text = "\n".join(re.sub(r"\s+", " ", line).strip()
                         for line in "".join(self.fragments).split("\n")).strip()
        self.fragments = []
        if text:
            self.blocks.append(("list" if self.prefix else "paragraph", self.prefix + text))

    def handle_starttag(self, tag, attrs):
        if tag not in self.INLINE | self.BLOCK | self.TABLE | self.VOID | {"ul", "li"}:
            raise CorpusPreparationError("Unsupported summary HTML element.")
        if tag not in self.VOID:
            self.stack.append(tag)
        if tag == "img":
            self.stats["omitted_images"] += 1
            self.handle_data(" ")
        elif tag == "br":
            (self.cell if self.cell is not None else self.fragments).append("\n")
        elif tag == "table":
            if self.table_rows is not None:
                raise CorpusPreparationError("Nested summary tables are unsupported.")
            self.flush()
            self.table_rows = []
            self.stats["tables"] += 1
        elif tag in {"thead", "tbody", "tfoot"}:
            if self.table_rows is None or self.row is not None:
                raise CorpusPreparationError("Invalid summary table section.")
        elif tag == "tr":
            if self.table_rows is None or self.row is not None:
                raise CorpusPreparationError("Invalid summary table row.")
            self.row = []
        elif tag in {"td", "th"}:
            if self.row is None or self.cell is not None:
                raise CorpusPreparationError("Invalid summary table cell.")
            if any(key in {"rowspan", "colspan"} and value != "1" for key, value in attrs):
                raise CorpusPreparationError("Merged summary table cells are unsupported.")
            self.cell = []
        elif tag in self.BLOCK:
            if self.cell is not None:
                self.cell.append(" ")
            else:
                self.flush()
        elif tag == "ul":
            if self.cell is not None:
                self.cell.append(" ")
            else:
                self.flush()
                self.list_depth += 1
        elif tag == "li":
            if self.cell is not None:
                self.cell.append(" - ")
                return
            if not self.list_depth or self.table_rows is not None:
                raise CorpusPreparationError("Unsupported summary list structure.")
            self.flush()
            self.prefix = "  " * (self.list_depth - 1) + "- "

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            raise CorpusPreparationError("Unbalanced summary HTML structure.")
        self.stack.pop()
        if tag in {"th", "td"}:
            self.row.append(re.sub(r"\s+", " ", "".join(self.cell)).strip())
            self.cell = None
        elif tag == "tr":
            if not self.row:
                raise CorpusPreparationError("Empty summary table row.")
            self.table_rows.append(" | ".join(self.row))
            self.row = None
        elif tag == "table":
            if not self.table_rows:
                raise CorpusPreparationError("Empty summary table.")
            self.blocks.append(("table", "\n".join(self.table_rows)))
            self.table_rows = None
        elif tag in self.BLOCK:
            if self.cell is not None:
                self.cell.append(" ")
            else:
                self.flush()
        elif tag == "li":
            if self.cell is not None:
                self.cell.append(" ")
            else:
                self.flush()
                self.prefix = ""
        elif tag == "ul":
            if self.cell is not None:
                self.cell.append(" ")
            else:
                self.flush()
                self.list_depth -= 1
                self.prefix = ""

    def handle_data(self, data):
        if data.strip():
            self.has_visible_text = True
        if self.table_rows is not None:
            if self.cell is not None:
                self.cell.append(data)
            elif data.strip():
                raise CorpusPreparationError("Summary table text is outside a cell.")
        else:
            # Source newlines are HTML whitespace, unlike explicit <br> separators.
            self.fragments.append(re.sub(r"\s+", " ", data))

    def handle_comment(self, data):
        self.stats["omitted_comments"] += 1

    def handle_decl(self, decl):
        raise CorpusPreparationError("Summary HTML declarations are unsupported.")

    def unknown_decl(self, data):
        raise CorpusPreparationError("Summary HTML declarations are unsupported.")

    def handle_pi(self, data):
        raise CorpusPreparationError("Summary HTML processing instructions are unsupported.")


def clean_summary(summary):
    """Preserve visible text order; this is a text converter, not an HTML sanitizer."""
    if not isinstance(summary, str):
        raise CorpusPreparationError("A source summary string is required.")
    parser = SummaryTextParser()
    parser.feed(summary)
    parser.close()
    if parser.stack:
        raise CorpusPreparationError("Unclosed summary HTML structure.")
    parser.flush()
    if not parser.blocks or not parser.has_visible_text:
        raise CorpusPreparationError("Cleaning produced an empty summary.")
    parts = []
    previous_kind = None
    for kind, text in parser.blocks:
        if parts:
            parts.append("\n" if kind == previous_kind == "list" else "\n\n")
        parts.append(text)
        previous_kind = kind
    return "".join(parts), parser.stats


def clean_corpus(repository_root=REPOSITORY_ROOT, *, extraction_manifest=REPORT,
                 output=CLEAN_OUTPUT, output_manifest=CLEAN_REPORT):
    """Verify extraction provenance and create separate cleaned artifacts exclusively."""
    root = Path(repository_root).resolve()
    input_path = owned_path(root, extraction_manifest, "data/knowledge/manifests")
    output_path = owned_path(root, output, "data/knowledge/.cache/corpus")
    report_path = owned_path(root, output_manifest, "data/knowledge/manifests")
    for target in (output_path, report_path):
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite an existing output: {target.relative_to(root)}")
    input_bytes = input_path.read_bytes()
    extraction = json.loads(input_bytes)
    if extraction["stage"] != "extraction_only":
        raise CorpusPreparationError("An extraction-only input manifest is required.")
    source = extraction["source"]
    snapshot_path = owned_path(root, source["snapshot_manifest"], "data/knowledge/manifests")
    snapshot_bytes = snapshot_path.read_bytes()
    if hashlib.sha256(snapshot_bytes).hexdigest() != source["snapshot_manifest_sha256"]:
        raise CorpusPreparationError("Source snapshot manifest checksum mismatch.")
    snapshot = json.loads(snapshot_bytes)
    if snapshot["selection"]["status"] != "approved_initial_selection":
        raise CorpusPreparationError("An approved source selection is required.")
    expected_ids = snapshot["selection"]["selected_topic_ids"]
    if (not expected_ids or len(set(expected_ids)) != len(expected_ids)
            or len(expected_ids) != snapshot["counts"]["selected_unique_topics"]):
        raise CorpusPreparationError("Invalid source selection IDs or count.")
    artifact = extraction["artifact"]
    artifact_path = owned_path(root, artifact["local_path"], "data/knowledge/.cache/corpus")
    payload = artifact_path.read_bytes()
    if len(payload) != artifact["size_bytes"] or hashlib.sha256(payload).hexdigest() != artifact["sha256"]:
        raise CorpusPreparationError("Extracted artifact size or checksum mismatch.")
    rows = [json.loads(line) for line in payload.decode("utf-8").splitlines()]
    ids = [row["topic_id"] for row in rows]
    if (len(ids) != len(set(ids)) or set(ids) != set(expected_ids)
            or len(ids) != extraction["counts"]["extracted_topics"]):
        raise CorpusPreparationError("Extracted topic IDs do not match the approved selection.")
    expected_source = {
        "name": snapshot["source"]["name"], "snapshot_date": snapshot["source"]["release_date"],
        "attribution": snapshot["source"]["attribution"], "archive_sha256": snapshot["archive"]["sha256"],
        "xml_sha256": snapshot["archive"]["members"][0]["sha256"],
        "selection_rule_version": snapshot["selection"]["selection_rule_version"],
    }
    fields = {"record_format_version", "topic_id", "title", "url", "language", "date_created",
              "synonyms", "groups", "summary_format", "full_summary", "source"}
    totals = {"tables": 0, "omitted_images": 0, "omitted_comments": 0}
    affected = {key: [] for key in totals}
    cleaned = []
    for row in sorted(rows, key=lambda item: (int(item["topic_id"]), item["topic_id"])):
        if (set(row) != fields or row["record_format_version"] != 1
                or row["language"] != "English" or row["summary_format"] != "source_html"
                or row["source"] != expected_source):
            raise CorpusPreparationError("Extracted record fields, language or provenance mismatch.")
        try:
            text, stats = clean_summary(row["full_summary"])
        except CorpusPreparationError as error:
            raise CorpusPreparationError(f"Topic {row['topic_id']}: {error}") from error
        cleaned.append(dict(row, cleaned_summary=text, cleaning={
            "version": CLEANER_VERSION, "format": "plain_text",
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), **stats}))
        for key, value in stats.items():
            totals[key] += value
            if value:
                affected[key].append(row["topic_id"])
    output_bytes = b"".join((json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False)
                             + "\n").encode("utf-8") for row in cleaned)
    report = {
        "manifest_version": 1, "owner": "Nemanja (A)", "task": "A-002",
        "stage": "summary_cleaning", "status": "cleaned_not_chunked",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "cleaner": {"version": CLEANER_VERSION, "python_version": platform.python_version(),
                    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "input": {"extraction_manifest": input_path.relative_to(root).as_posix(),
                  "extraction_manifest_sha256": hashlib.sha256(input_bytes).hexdigest(),
                  "artifact": artifact},
        "source": source,
        "artifact": {"local_path": output_path.relative_to(root).as_posix(), "format": "jsonl-utf8",
                     "size_bytes": len(output_bytes), "sha256": hashlib.sha256(output_bytes).hexdigest()},
        "counts": {"cleaned_topics": len(cleaned), "passages": None, **totals},
        "affected_topic_ids": affected,
        "checks": {"input_checksums": "passed", "exact_selected_id_set": "passed",
                   "english_and_source_provenance": "passed", "nonempty_cleaned_summaries": "passed"},
        "limitations": ["Plain text is not sanitized HTML and must be displayed as text.",
                        "Image tags are omitted and recorded; image content is neither fetched nor inferred.",
                        "No semantic or clinical validation, passages, indexing or provider calls.",
                        "A-002 remains incomplete until the separately approved passage increment passes."],
    }
    report_bytes = (json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    created = []
    try:
        for target, content in ((output_path, output_bytes), (report_path, report_bytes)):
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as destination:
                created.append(target)
                destination.write(content)
    except OSError:
        for target in reversed(created):
            target.unlink()
        raise
    return report


def passage_configuration(max_code_points=MAX_CODE_POINTS, overlap_code_points=OVERLAP_CODE_POINTS):
    if (type(max_code_points) is not int or type(overlap_code_points) is not int
            or max_code_points <= 0 or not 0 <= overlap_code_points < max_code_points):
        raise CorpusPreparationError("Passage limits must be integers with 0 <= overlap < maximum.")
    return {"version": CHUNKER_VERSION, "unit": "unicode_code_points",
            "max_code_points": max_code_points, "overlap_code_points": overlap_code_points,
            "packing": "greedy_source_blocks", "tables": "whole",
            "long_paragraphs": "word_boundaries", "lists": "whole_items",
            "trailing_nih_attribution": "group_with_previous_unit_when_within_maximum",
            "overlap": "whole_trailing_paragraphs_or_items_when_next_unit_fits"}


def source_units(topic, maximum):
    """Recover source block boundaries and verify them against the existing canonical text."""
    text = topic["cleaned_summary"]
    cleaning = topic["cleaning"]
    if (cleaning["version"] != CLEANER_VERSION or cleaning["format"] != "plain_text"
            or hashlib.sha256(text.encode("utf-8")).hexdigest() != cleaning["text_sha256"]):
        raise CorpusPreparationError("Unsupported cleaner version or canonical text checksum.")
    parser = SummaryTextParser()
    parser.feed(topic["full_summary"])
    parser.close()
    if parser.stack:
        raise CorpusPreparationError("Unclosed source block structure.")
    parser.flush()
    if not parser.has_visible_text or any(cleaning[key] != count for key, count in parser.stats.items()):
        raise CorpusPreparationError("Source structure or cleaning counts do not match canonical text.")
    units = []
    cursor, previous_kind = 0, None
    for kind, block in parser.blocks:
        separator = ("\n" if kind == previous_kind == "list" else "\n\n") if cursor else ""
        expected = separator + block
        if text[cursor:cursor + len(expected)] != expected:
            raise CorpusPreparationError("Source block structure does not match canonical text.")
        start, end = cursor + len(separator), cursor + len(expected)
        cursor, previous_kind = end, kind
        if end - start <= maximum:
            units.append({"start": start, "end": end, "kind": kind})
        elif kind in {"table", "list"}:
            raise CorpusPreparationError("A table or single list item exceeds the passage maximum.")
        else:
            # Only paragraph fragments may split, always between complete whitespace-delimited words.
            position = start
            while position < end:
                limit = min(position + maximum, end)
                if limit < end and not text[limit].isspace():
                    boundaries = [match.start() + position for match in re.finditer(r"\s+", text[position:limit])]
                    if not boundaries:
                        raise CorpusPreparationError("An unbreakable word exceeds the passage maximum.")
                    limit = boundaries[-1]
                units.append({"start": position, "end": limit, "kind": "paragraph_fragment"})
                position = limit
                while position < end and text[position].isspace():
                    position += 1
    if cursor != len(text) or not units:
        raise CorpusPreparationError("Source structure does not cover the canonical text.")
    if len(units) > 1 and re.fullmatch(r"NIH: [^\n]+", text[units[-1]["start"]:units[-1]["end"]]):
        preceding, attribution = units[-2:]
        if attribution["end"] - preceding["start"] <= maximum:
            units[-2:] = [{"start": preceding["start"], "end": attribution["end"], "kind": "block_group"}]
    return units


def build_passages(topic, *, max_code_points=MAX_CODE_POINTS, overlap_code_points=OVERLAP_CODE_POINTS):
    """Greedily pack exact source slices, protecting tables/items and bounded optional overlap."""
    configuration = passage_configuration(max_code_points, overlap_code_points)
    units = source_units(topic, max_code_points)
    metadata = {key: topic[key] for key in ("topic_id", "title", "url", "language", "date_created",
                                           "synonyms", "groups", "source")}
    passages = []
    begin, previous_end = 0, 0
    while begin < len(units):
        last = begin
        start = units[begin]["start"]
        while last + 1 < len(units) and units[last + 1]["end"] - start <= max_code_points:
            last += 1
        end = units[last]["end"]
        if end <= previous_end or topic["cleaned_summary"][previous_end:start].strip():
            raise CorpusPreparationError("Passage packing failed to advance or left uncovered text.")
        identity = {"configuration": configuration, "topic": metadata,
                    "topic_text_sha256": topic["cleaning"]["text_sha256"], "start": start, "end": end}
        passage_hash = hashlib.sha256(json.dumps(identity, ensure_ascii=False, sort_keys=True,
                                                 allow_nan=False).encode("utf-8")).hexdigest()
        passages.append({"record_format_version": 1, **metadata,
                         "passage_id": f"mplus-{topic['topic_id']}-{passage_hash}",
                         "topic_text_sha256": topic["cleaning"]["text_sha256"],
                         "cleaning_version": topic["cleaning"]["version"],
                         "chunking": configuration, "start": start, "end": end,
                         "overlap_code_points": max(0, previous_end - start),
                         "text": topic["cleaned_summary"][start:end]})
        previous_end = end
        following = last + 1
        if following == len(units):
            break
        for candidate in range(begin + 1, last + 1):
            suffix = units[candidate:last + 1]
            if (end - suffix[0]["start"] <= overlap_code_points
                    and units[following]["end"] - suffix[0]["start"] <= max_code_points
                    and all(unit["kind"] in {"paragraph", "list"} for unit in suffix)):
                following = candidate
                break
        begin = following
    if topic["cleaned_summary"][previous_end:].strip():
        raise CorpusPreparationError("Passages left uncovered canonical text.")
    return passages


def verified_bytes(path, description):
    payload = path.read_bytes()
    if (("size_bytes" in description and len(payload) != description["size_bytes"])
            or hashlib.sha256(payload).hexdigest() != description["sha256"]):
        raise CorpusPreparationError("Input checksum or size mismatch.")
    return payload


def load_cleaned_topics(root, manifest):
    """Validate the existing extraction/cleaning chain without rewriting an upstream artifact."""
    if manifest["stage"] != "summary_cleaning" or manifest["cleaner"]["version"] != CLEANER_VERSION:
        raise CorpusPreparationError("A supported summary-cleaning manifest is required.")
    source = manifest["source"]
    snapshot_path = owned_path(root, source["snapshot_manifest"], "data/knowledge/manifests")
    snapshot = json.loads(verified_bytes(snapshot_path, {"sha256": source["snapshot_manifest_sha256"]}))
    selection = snapshot["selection"]
    expected_ids = selection["selected_topic_ids"]
    if (selection["status"] != "approved_initial_selection" or not expected_ids
            or len(set(expected_ids)) != len(expected_ids)
            or any(not isinstance(value, str) or not re.fullmatch(r"[0-9]+", value) for value in expected_ids)
            or len(expected_ids) != snapshot["counts"]["selected_unique_topics"]):
        raise CorpusPreparationError("The selected source IDs or approval are invalid.")
    input_record = manifest["input"]
    extraction_path = owned_path(root, input_record["extraction_manifest"], "data/knowledge/manifests")
    extraction = json.loads(verified_bytes(extraction_path, {"sha256": input_record["extraction_manifest_sha256"]}))
    if (extraction["stage"] != "extraction_only" or extraction["source"] != source
            or extraction["artifact"] != input_record["artifact"]):
        raise CorpusPreparationError("Extraction/cleaning provenance chain mismatch.")
    extracted_path = owned_path(root, extraction["artifact"]["local_path"], "data/knowledge/.cache/corpus")
    extracted = [json.loads(line) for line in verified_bytes(extracted_path, extraction["artifact"]).decode("utf-8").splitlines()]
    artifact_path = owned_path(root, manifest["artifact"]["local_path"], "data/knowledge/.cache/corpus")
    topics = [json.loads(line) for line in verified_bytes(artifact_path, manifest["artifact"]).decode("utf-8").splitlines()]
    for records in (extracted, topics):
        ids = [row["topic_id"] for row in records]
        if len(ids) != len(set(ids)) or set(ids) != set(expected_ids):
            raise CorpusPreparationError("Input IDs do not match the approved selected topic set.")
    if (manifest["counts"]["cleaned_topics"] != len(topics)
            or extraction["counts"]["extracted_topics"] != len(topics)):
        raise CorpusPreparationError("Input manifest topic counts do not match the records.")
    originals = {row["topic_id"]: row for row in extracted}
    original_fields = {"record_format_version", "topic_id", "title", "url", "language", "date_created",
                       "synonyms", "groups", "summary_format", "full_summary", "source"}
    expected_source = {"name": snapshot["source"]["name"], "snapshot_date": snapshot["source"]["release_date"],
                       "attribution": snapshot["source"]["attribution"], "archive_sha256": snapshot["archive"]["sha256"],
                       "xml_sha256": snapshot["archive"]["members"][0]["sha256"],
                       "selection_rule_version": selection["selection_rule_version"]}
    for topic in topics:
        original = originals[topic["topic_id"]]
        if (set(original) != original_fields or set(topic) != original_fields | {"cleaned_summary", "cleaning"}
                or any(topic[key] != value for key, value in original.items())
                or topic["source"] != expected_source or topic["language"] != "English"
                or topic["record_format_version"] != 1 or topic["summary_format"] != "source_html"
                or not all(isinstance(topic[key], str) and topic[key].strip() for key in ("title", "url", "cleaned_summary"))):
            raise CorpusPreparationError("An input record has unexpected fields, metadata or source provenance.")
    return sorted(topics, key=lambda row: (int(row["topic_id"]), row["topic_id"]))


def chunk_corpus(repository_root=REPOSITORY_ROOT, *, cleaned_manifest=CLEAN_REPORT,
                 output=PASSAGE_OUTPUT, output_manifest=PASSAGE_REPORT):
    """Prepare the approved candidate passages with checked inputs and exclusive new outputs."""
    root = Path(repository_root).resolve()
    input_path = owned_path(root, cleaned_manifest, "data/knowledge/manifests")
    output_path = owned_path(root, output, "data/knowledge/.cache/corpus")
    report_path = owned_path(root, output_manifest, "data/knowledge/manifests")
    for target in (output_path, report_path):
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite an existing output: {target.relative_to(root)}")
    manifest_bytes = input_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    topics = load_cleaned_topics(root, manifest)
    rows, counts = [], {}
    for topic in topics:
        try:
            passages = build_passages(topic)
        except CorpusPreparationError as error:
            raise CorpusPreparationError(f"Topic {topic['topic_id']}: {error}") from error
        counts[topic["topic_id"]] = len(passages)
        rows.extend(passages)
    if len({row["passage_id"] for row in rows}) != len(rows):
        raise CorpusPreparationError("Passage identifiers are not unique.")
    output_bytes = b"".join((json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False)
                             + "\n").encode("utf-8") for row in rows)
    artifact_hash = hashlib.sha256(output_bytes).hexdigest()
    configuration = passage_configuration()
    corpus_identity = {"cleaned_artifact_sha256": manifest["artifact"]["sha256"],
                       "passage_artifact_sha256": artifact_hash, "configuration": configuration}
    corpus_version = hashlib.sha256(json.dumps(corpus_identity, sort_keys=True).encode("utf-8")).hexdigest()
    lengths = [len(row["text"]) for row in rows]
    overlaps = [row["overlap_code_points"] for row in rows]
    report = {
        "manifest_version": 1, "owner": "Nemanja (A)", "task": "A-002",
        "stage": "passage_preparation", "status": "prepared_candidate_not_retrieval_validated",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "configuration": configuration, "configuration_basis": "User-approved initial candidate; retrieval quality unmeasured.",
        "builder": {"python_version": platform.python_version(),
                    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "corpus_version": corpus_version,
        "input": {"cleaned_manifest": input_path.relative_to(root).as_posix(),
                  "cleaned_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(), "artifact": manifest["artifact"]},
        "source": manifest["source"],
        "artifact": {"local_path": output_path.relative_to(root).as_posix(), "format": "jsonl-utf8",
                     "size_bytes": len(output_bytes), "sha256": artifact_hash},
        "counts": {"topics": len(topics), "passages": len(rows), "passages_by_topic_id": counts,
                   "whole_tables": sum(topic["cleaning"]["tables"] for topic in topics),
                   "passages_with_overlap": sum(value > 0 for value in overlaps),
                   "attribution_only_passages": sum(bool(re.fullmatch(r"NIH: [^\n]+", row["text"])) for row in rows)},
        "observed_code_points": {"passage_min": min(lengths), "passage_median": statistics.median(lengths),
                                 "passage_max": max(lengths), "overlap_max": max(overlaps)},
        "checks": {"input_hash_chain_and_selected_ids": "passed", "source_structure_matches_canonical_text": "passed",
                   "non_whitespace_text_coverage": "passed", "exact_code_point_slices": "passed",
                   "table_and_item_boundaries": "passed", "bounded_progressive_overlap": "passed",
                   "unique_passage_ids": "passed"},
        "limitations": ["The size/overlap policy is an initial candidate, not a measured optimum.",
                        "Oversized tables/list items and unbreakable words fail rather than silently splitting or truncating.",
                        "Source block parsing verifies existing text; passage text is sliced only from cleaned_summary.",
                        "No API contract, tokenizer budget, embedding model, index or retrieval metric is established.",
                        "Prior extraction/cleaning manifests remain unchanged historical stage records."],
    }
    report_bytes = (json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    created = []
    try:
        for target, content in ((output_path, output_bytes), (report_path, report_bytes)):
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as destination:
                created.append(target)
                destination.write(content)
    except OSError:
        for target in reversed(created):
            target.unlink()
        raise
    return report


def main():
    parser = argparse.ArgumentParser(description="Prepare approved local public-corpus artifacts.")
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract", help="Extract source topic records without cleaning or chunking.")
    extract.add_argument("--snapshot-manifest", default=SNAPSHOT)
    extract.add_argument("--output", default=OUTPUT)
    extract.add_argument("--output-manifest", default=REPORT)
    clean = commands.add_parser("clean", help="Convert verified source summaries to attributed plain text.")
    clean.add_argument("--extraction-manifest", default=REPORT)
    clean.add_argument("--output", default=CLEAN_OUTPUT)
    clean.add_argument("--output-manifest", default=CLEAN_REPORT)
    chunk = commands.add_parser("chunk", help="Build exact passages with the approved 2500/300 candidate policy.")
    chunk.add_argument("--cleaned-manifest", default=CLEAN_REPORT)
    chunk.add_argument("--output", default=PASSAGE_OUTPUT)
    chunk.add_argument("--output-manifest", default=PASSAGE_REPORT)
    arguments = parser.parse_args()
    try:
        if arguments.command == "extract":
            report = extract_corpus(snapshot_manifest=arguments.snapshot_manifest, output=arguments.output,
                                    output_manifest=arguments.output_manifest)
        elif arguments.command == "clean":
            report = clean_corpus(extraction_manifest=arguments.extraction_manifest, output=arguments.output,
                                  output_manifest=arguments.output_manifest)
        else:
            report = chunk_corpus(cleaned_manifest=arguments.cleaned_manifest, output=arguments.output,
                                  output_manifest=arguments.output_manifest)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, ET.ParseError) as error:
        parser.exit(1, f"Corpus preparation failed: {error}\n")
    print(json.dumps({"stage": report["stage"],
                      "counts": {key: value for key, value in report["counts"].items() if not isinstance(value, dict)},
                      "artifact": report["artifact"], "manifest": arguments.output_manifest}))


if __name__ == "__main__":
    main()
