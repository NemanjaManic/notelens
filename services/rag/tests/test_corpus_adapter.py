"""Verify prepared artifacts independently of retrieval, models and raw downloads."""

from dataclasses import FrozenInstanceError
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest import mock
from uuid import uuid4
import xml.etree.ElementTree as ET
import zipfile

from fastapi.testclient import TestClient
import pytest

from notelens_rag.ingestion import CorpusLoadError, load_corpus
from notelens_rag.main import DEMO_QUESTION, Settings, create_app


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = 'data/knowledge/manifests/passages.json'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def identity(row):
    keys = ('topic_id', 'title', 'url', 'language', 'date_created', 'synonyms', 'groups', 'source')
    value = {'configuration': row['chunking'], 'topic': {key: row[key] for key in keys},
             'topic_text_sha256': row['topic_text_sha256'], 'start': row['start'], 'end': row['end']}
    return 'mplus-' + row['topic_id'] + '-' + hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()).hexdigest()


def mutate_passages(root, mutation, update_counts=False):
    path = root / MANIFEST
    manifest = read_json(path)
    artifact = root / manifest['artifact']['local_path']
    rows = [json.loads(line) for line in artifact.read_text(encoding='utf-8').splitlines()]
    mutation(rows)
    payload = ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows).encode()
    artifact.write_bytes(payload)
    manifest['artifact'].update(size_bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    if update_counts:
        counts = {}
        for row in rows: counts[row['topic_id']] = counts.get(row['topic_id'], 0) + 1
        manifest['counts'].update(topics=len(counts), passages=len(rows), passages_by_topic_id=counts)
    corpus_identity = {'cleaned_artifact_sha256': manifest['input']['artifact']['sha256'],
                       'passage_artifact_sha256': manifest['artifact']['sha256'],
                       'configuration': manifest['configuration']}
    manifest['corpus_version'] = hashlib.sha256(json.dumps(corpus_identity, sort_keys=True).encode()).hexdigest()
    write_json(path, manifest)


@pytest.fixture
def prepared_repository():
    parent = Path(__file__).resolve().parents[1] / '.cache' / 'test-runs'
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='corpus-reader-', dir=parent) as directory:
        root = Path(directory).resolve()
        assert root.is_relative_to(parent.resolve())
        spec = importlib.util.spec_from_file_location('corpus_fixture_builder', ROOT / 'data/knowledge/scripts/prepare_corpus.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        tree = ET.Element('health-topics', {'total': '3'})
        for topic_id, language in [('20', 'English'), ('3', 'English'), ('8', 'Spanish')]:
            topic = ET.SubElement(tree, 'health-topic', {'id': topic_id, 'title': f'Synthetic topic {topic_id}',
                'url': f'https://medlineplus.gov/synthetic{topic_id}.html', 'language': language,
                'date-created': '01/02/2020'})
            summary = '<p>Demo \U0001fa7a &amp; context.</p><p>No chest pain.</p>'
            if topic_id == '3': summary += '<p>No chest pain.</p>' * 200
            ET.SubElement(topic, 'full-summary').text = summary
            ET.SubElement(topic, 'also-called').text = 'Synthetic synonym'
            ET.SubElement(topic, 'group', {'id': '14', 'url': 'https://medlineplus.gov/brainandnerves.html'}).text = 'Brain and Nerves'
        payload = ET.tostring(tree, encoding='utf-8')
        archive = root / 'data/knowledge/raw/source.zip'
        archive.parent.mkdir(parents=True)
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as destination:
            destination.writestr('topics.xml', payload)
        snapshot = {'source': {'name': 'Synthetic MedlinePlus-shaped fixture', 'release_date': '2026-11-10',
                               'attribution': 'Synthetic public fixture'},
                    'archive': {'local_path': 'data/knowledge/raw/source.zip', 'size_bytes': archive.stat().st_size,
                                'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                                'download_url': 'https://example.invalid/source.zip',
                                'members': [{'name': 'topics.xml', 'size_bytes': len(payload),
                                             'sha256': hashlib.sha256(payload).hexdigest()}]},
                    'selection': {'status': 'approved_initial_selection', 'selection_rule_version': 'synthetic-v1',
                                  'selected_topic_ids': ['3', '20'], 'selected_topic_ids_by_specialty': {
                                      'Cardiovascular / Pulmonary': [], 'Orthopedic': [], 'Gastroenterology': [],
                                      'Neurology': ['3'], 'Urology': ['20']}},
                    'counts': {'source_topics': 3, 'selected_unique_topics': 2}}
        snapshot_path = root / 'data/knowledge/manifests/snapshot.json'
        snapshot_path.parent.mkdir(parents=True)
        write_json(snapshot_path, snapshot)
        builder.extract_corpus(root)
        builder.clean_corpus(root)
        builder.chunk_corpus(root)
        yield root


def test_reader_keeps_unicode_ids_metadata_and_explicit_specialty_overrides(prepared_repository):
    root = prepared_repository
    before = {path: path.read_bytes() for path in root.rglob('*') if path.is_file()}
    with mock.patch('socket.socket', side_effect=AssertionError('No network permitted')):
        corpus = load_corpus(repository_root=root)
    assert corpus.topic_count == 2 and corpus.passage_count >= 3
    assert corpus.topic_ids == ('3', '20')
    assert any('\U0001fa7a' in passage.text for passage in corpus.passages)
    assert len(corpus.by_id) == corpus.passage_count
    assert corpus.by_topic_id['20'][0].specialties == ('Urology',)
    assert corpus.by_topic_id['3'][0].specialties == ('Neurology',)
    for passage in corpus.passages:
        assert corpus.by_id[passage.passage_id] is passage
        assert passage.source['attribution'] == 'Synthetic public fixture'
        assert passage.title == f'Synthetic topic {passage.topic_id}'
        assert passage.synonyms == ('Synthetic synonym',)
    for path, content in before.items(): assert path.read_bytes() == content


def test_loaded_records_are_immutable(prepared_repository):
    corpus = load_corpus(repository_root=prepared_repository)
    with pytest.raises(FrozenInstanceError): corpus.passages[0].text = 'Changed'
    with pytest.raises(TypeError): corpus.by_id['new'] = corpus.passages[0]
    with pytest.raises(TypeError): corpus.passages[0].source['attribution'] = 'Changed'
    with pytest.raises(TypeError): corpus.passages[0].groups[0]['name'] = 'Changed'


@pytest.mark.parametrize('which', ['manifest', 'passages', 'cleaned_manifest', 'cleaned_topics', 'snapshot'])
def test_missing_required_files_get_safe_errors(prepared_repository, which):
    root = prepared_repository; manifest = read_json(root / MANIFEST)
    paths = {'manifest': MANIFEST, 'passages': manifest['artifact']['local_path'],
             'cleaned_manifest': manifest['input']['cleaned_manifest'],
             'cleaned_topics': manifest['input']['artifact']['local_path'],
             'snapshot': manifest['source']['snapshot_manifest']}
    (root / paths[which]).unlink()
    with pytest.raises(CorpusLoadError) as error: load_corpus(repository_root=root)
    assert error.value.code == 'corpus_file_missing'
    assert str(root) not in str(error.value)


@pytest.mark.parametrize('which', ['passages', 'cleaned_manifest', 'cleaned_topics', 'snapshot'])
def test_changed_files_fail_checksum_verification(prepared_repository, which):
    root = prepared_repository; manifest = read_json(root / MANIFEST)
    paths = {'passages': manifest['artifact']['local_path'], 'cleaned_manifest': manifest['input']['cleaned_manifest'],
             'cleaned_topics': manifest['input']['artifact']['local_path'], 'snapshot': manifest['source']['snapshot_manifest']}
    with (root / paths[which]).open('ab') as destination: destination.write(b' changed')
    with pytest.raises(CorpusLoadError) as error: load_corpus(repository_root=root)
    assert error.value.code == 'corpus_integrity_failure'


@pytest.mark.parametrize('change', ['duplicate_id', 'wrong_quote', 'bad_offset', 'wrong_metadata',
                                   'wrong_policy', 'wrong_overlap', 'foreign_qa_field'])
def test_bad_records_fail_even_after_artifact_hash_is_updated(prepared_repository, change):
    def mutate(rows):
        if change == 'duplicate_id': rows.append(rows[0])
        elif change == 'wrong_quote': rows[0]['text'] = 'WRONG TEXT'
        elif change == 'bad_offset': rows[0]['start'] = True
        elif change == 'wrong_metadata': rows[0]['title'] = 'Wrong title'
        elif change == 'wrong_policy': rows[0]['chunking']['max_code_points'] = 9999
        elif change == 'wrong_overlap': rows[1]['overlap_code_points'] = 9999
        else: rows[0]['evaluation_answer'] = 'DO NOT INDEX QA'
    mutate_passages(prepared_repository, mutate)
    with pytest.raises(CorpusLoadError): load_corpus(repository_root=prepared_repository)


def test_missing_selected_topic_cannot_be_hidden_by_changed_counts(prepared_repository):
    mutate_passages(prepared_repository, lambda rows: rows.__setitem__(slice(None), [r for r in rows if r['topic_id'] != '20']), True)
    with pytest.raises(CorpusLoadError): load_corpus(repository_root=prepared_repository)


def test_uncovered_text_is_rejected_even_with_recomputed_ids(prepared_repository):
    root = prepared_repository; manifest = read_json(root / MANIFEST)
    topics = {r['topic_id']: r for r in (json.loads(line) for line in (root / manifest['input']['artifact']['local_path']).read_text(encoding='utf-8').splitlines())}
    def mutate(rows):
        previous, last = [row for row in rows if row['topic_id'] == '3'][-2:]
        last['start'] = previous['end'] + 3
        last['text'] = topics['3']['cleaned_summary'][last['start']:last['end']]
        last['overlap_code_points'] = 0
        last['passage_id'] = identity(last)
    mutate_passages(root, mutate)
    with pytest.raises(CorpusLoadError): load_corpus(repository_root=root)


def test_expected_corpus_version_is_checked(prepared_repository):
    corpus = load_corpus(repository_root=prepared_repository)
    assert load_corpus(repository_root=prepared_repository, expected_corpus_version=corpus.corpus_version).corpus_version == corpus.corpus_version
    with pytest.raises(CorpusLoadError) as error:
        load_corpus(repository_root=prepared_repository, expected_corpus_version='0' * 64)
    assert error.value.code == 'corpus_version_mismatch'


@pytest.mark.parametrize('change', ['manifest_version', 'boolean_topic_count', 'corpus_version', 'unknown_policy'])
def test_manifest_versions_counts_and_policy_are_checked(prepared_repository, change):
    path = prepared_repository / MANIFEST
    manifest = read_json(path)
    if change == 'manifest_version': manifest['manifest_version'] = 99
    elif change == 'boolean_topic_count': manifest['counts']['passages_by_topic_id']['20'] = True
    elif change == 'corpus_version': manifest['corpus_version'] = '0' * 64
    else: manifest['configuration']['version'] = 'unknown-v99'
    write_json(path, manifest)
    with pytest.raises(CorpusLoadError): load_corpus(repository_root=prepared_repository)


@pytest.mark.parametrize('payload', [b'not JSON PRIVATE_FIXTURE_BODY', b'{"key":1,"key":2}', b'{"value":NaN}'])
def test_malformed_duplicate_or_nonfinite_manifest_json_is_safe(prepared_repository, payload):
    (prepared_repository / MANIFEST).write_bytes(payload)
    with pytest.raises(CorpusLoadError) as error: load_corpus(repository_root=prepared_repository)
    assert error.value.code == 'corpus_format_invalid'
    assert 'PRIVATE_FIXTURE_BODY' not in str(error.value)


def test_inaccessible_repository_error_is_safe():
    with mock.patch('notelens_rag.ingestion.repository_directory', side_effect=PermissionError('PRIVATE_FIXTURE_PATH')):
        with pytest.raises(CorpusLoadError) as error: load_corpus()
    assert error.value.code == 'corpus_file_unreadable'
    assert 'PRIVATE_FIXTURE_PATH' not in str(error.value)


def test_manifest_must_be_utf8_even_when_json_itself_is_otherwise_valid(prepared_repository):
    path = prepared_repository / MANIFEST
    path.write_bytes(path.read_text(encoding='utf-8').encode('utf-16'))
    with pytest.raises(CorpusLoadError) as error: load_corpus(repository_root=prepared_repository)
    assert error.value.code == 'corpus_format_invalid'


def test_loaded_snapshot_is_unchanged_and_a_new_load_detects_disk_tampering(prepared_repository):
    corpus = load_corpus(repository_root=prepared_repository)
    text = corpus.passages[0].text
    manifest = read_json(prepared_repository / MANIFEST)
    with (prepared_repository / manifest['artifact']['local_path']).open('ab') as output:
        output.write(b' changed')
    assert corpus.passages[0].text == text
    with pytest.raises(CorpusLoadError): load_corpus(repository_root=prepared_repository)


def test_paths_cannot_escape_owned_corpus_directories(prepared_repository):
    manifest = read_json(prepared_repository / MANIFEST)
    manifest['artifact']['local_path'] = '../outside.jsonl'
    write_json(prepared_repository / MANIFEST, manifest)
    with pytest.raises(CorpusLoadError) as error: load_corpus(repository_root=prepared_repository)
    assert error.value.code == 'corpus_path_invalid'


def test_reader_needs_no_raw_zip_or_extraction_artifact(prepared_repository):
    (prepared_repository / 'data/knowledge/raw/source.zip').unlink()
    (prepared_repository / 'data/knowledge/.cache/corpus/selected-topics.jsonl').unlink()
    (prepared_repository / 'data/knowledge/manifests/prepared-corpus.json').unlink()
    assert load_corpus(repository_root=prepared_repository).topic_count == 2


def test_cli_reports_counts_without_content_and_safe_errors(prepared_repository):
    arguments = [sys.executable, '-m', 'notelens_rag.ingestion', '--repository-root', str(prepared_repository)]
    good = subprocess.run(arguments, cwd=prepared_repository, capture_output=True, text=True)
    assert good.returncode == 0, good.stderr
    summary = json.loads(good.stdout)
    assert summary['status'] == 'verified' and summary['topics'] == 2
    assert 'No chest pain' not in good.stdout
    manifest = read_json(prepared_repository / MANIFEST)
    with (prepared_repository / manifest['artifact']['local_path']).open('ab') as destination:
        destination.write(b'PRIVATE_FIXTURE_BODY')
    bad = subprocess.run(arguments, cwd=prepared_repository, capture_output=True, text=True)
    assert bad.returncode == 1 and bad.stdout == ''
    assert json.loads(bad.stderr)['code'] == 'corpus_integrity_failure'
    assert 'PRIVATE_FIXTURE_BODY' not in bad.stderr and 'Traceback' not in bad.stderr


def test_configured_service_loads_corpus_but_does_not_claim_a_live_index(prepared_repository):
    settings = Settings(corpus_manifest=MANIFEST, repository_root=str(prepared_repository))
    with TestClient(create_app(settings), client=('127.0.0.1', 45000)) as client:
        assert client.app.state.prepared_corpus.topic_count == 2
        ready = client.get('/health/ready')
        assert ready.status_code == 200 and ready.json()['mode'] == 'mock'
        assert ready.json()['model_version'] is None
        response = client.post('/v1/retrieve', json={'schema_version': '1.0.0', 'question': DEMO_QUESTION},
                               headers={'X-Request-ID': str(uuid4())})
        assert response.status_code == 200 and response.json()['passages'][0]['topic_id'] == 'mock-topic-1'


def test_configured_missing_corpus_keeps_process_alive_but_not_ready(prepared_repository):
    (prepared_repository / MANIFEST).unlink()
    settings = Settings(corpus_manifest=MANIFEST, repository_root=str(prepared_repository))
    with TestClient(create_app(settings), client=('127.0.0.1', 45000)) as client:
        assert client.get('/health/live').status_code == 200
        ready = client.get('/health/ready')
        assert ready.status_code == 503 and str(prepared_repository) not in ready.text
        response = client.post('/v1/retrieve', json={'schema_version': '1.0.0', 'question': DEMO_QUESTION},
                               headers={'X-Request-ID': str(uuid4())})
        assert response.status_code == 503 and response.json()['error']['code'] == 'configuration_required'
