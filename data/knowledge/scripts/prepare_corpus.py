"""Prepare approved public MedlinePlus topics locally with traceable source text."""

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import platform
import re
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
    arguments = parser.parse_args()
    try:
        if arguments.command == "extract":
            report = extract_corpus(snapshot_manifest=arguments.snapshot_manifest, output=arguments.output,
                                    output_manifest=arguments.output_manifest)
        else:
            report = clean_corpus(extraction_manifest=arguments.extraction_manifest, output=arguments.output,
                                  output_manifest=arguments.output_manifest)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, ET.ParseError) as error:
        parser.exit(1, f"Corpus preparation failed: {error}\n")
    print(json.dumps({"stage": report["stage"], "counts": report["counts"],
                      "artifact": report["artifact"], "manifest": arguments.output_manifest}))


if __name__ == "__main__":
    main()
