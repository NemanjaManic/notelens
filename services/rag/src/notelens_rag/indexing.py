"""Build and verify an owned, versioned public-corpus Chroma index."""

import argparse
from contextlib import contextmanager
from decimal import Decimal
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import struct
import sys
from uuid import uuid4

from .embeddings import (DIMENSIONS, MODEL, PRICE_PER_MILLION, EmbeddingError,
    OpenAIEmbedder, TokenBudget, identity, plan_corpus, read_settings)
from .ingestion import CorpusLoadError, load_corpus, owned_file, parse_json, repository_directory


COLLECTION = 'public-passages'
PROBE_TEXT = 'Public medical literature embedding connection check.'
BUILD_FORMAT = 'notelens-public-chroma-v1'
CHROMA_CONFIGURATION = {'hnsw': {'space': 'cosine'}}


class IndexBuildError(ValueError):
    def __init__(self, message, code='index_integrity_failure'):
        super().__init__(message)
        self.code = code


def require(condition, message, code='index_integrity_failure'):
    if not condition:
        raise IndexBuildError(message, code)


def atomic_json(path, value):
    temporary = path.with_name(path.name + '.' + uuid4().hex + '.tmp')
    try:
        with temporary.open('x', encoding='utf-8', newline='\n') as output:
            json.dump(value, output, sort_keys=True, allow_nan=False)
            output.write('\n')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path):
    try:
        result = parse_json(path.read_bytes(), 'Index state')
        require(isinstance(result, dict), 'Index state must be an object.')
        return result
    except (OSError, CorpusLoadError):
        raise IndexBuildError('The local index state is missing or invalid.') from None


def index_specification(plan, *, mode):
    require(mode in ('mock', 'live'), 'An explicit index execution mode is required.')
    fields = ('embedding_plan_version', 'embedding_space_version', 'corpus_version',
              'passage_manifest_sha256', 'passage_artifact_sha256', 'model', 'dimensions')
    spec = {name: plan[name] for name in fields}
    spec.update(format=BUILD_FORMAT, mode=mode, vector_store='chroma',
                chromadb_version=version('chromadb'), configuration=CHROMA_CONFIGURATION,
                vector_storage='chroma-float32-roundtrip-v1')
    return {**spec, 'index_version': identity(spec)}


class PersistentTokenBudget(TokenBudget):
    """Reserve before transmission and retain uncertain charges across explicit resumes."""

    def __init__(self, path, ledger):
        try:
            super().__init__(Decimal(ledger['max_usd']), Decimal(ledger['price_per_million']))
            count = ledger['reserved_tokens']
            require(type(count) is int and count >= 0, 'The token reservation ledger is invalid.')
            require(Decimal(count) * self.price_per_million / 1_000_000 <= self.max_usd,
                    'The token ledger exceeds its approved budget.')
        except (KeyError, ArithmeticError, TypeError):
            raise IndexBuildError('The token reservation ledger is invalid.') from None
        self.path, self.ledger, self.reserved_tokens = path, dict(ledger), count

    def reserve(self, tokens):
        require(type(tokens) is int and tokens > 0, 'A positive token reservation is required.')
        with self._lock:
            count = self.reserved_tokens + tokens
            if Decimal(count) * self.price_per_million / 1_000_000 > self.max_usd:
                raise EmbeddingError('budget_exceeded', 'The embedding run budget would be exceeded.')
            record = {**self.ledger, 'reserved_tokens': count}
            atomic_json(self.path, record)
            self.ledger, self.reserved_tokens = record, count

    def update(self, **fields):
        with self._lock:
            record = {**self.ledger, **fields}
            atomic_json(self.path, record)
            self.ledger = record


@contextmanager
def exclusive_build(folder):
    lock = folder / '.build.lock'
    try:
        stream = lock.open('x', encoding='ascii')
    except FileExistsError:
        raise IndexBuildError('An index build is already locked; inspect before retrying.', 'index_locked') from None
    try:
        stream.write('Owned local index build.\n')
        stream.close()
        yield
    finally:
        if not stream.closed:
            stream.close()
        lock.unlink()


def passage_metadata(passage, corpus):
    return {'topic_id': passage.topic_id, 'title': passage.title, 'url': passage.url,
            'language': passage.language, 'snapshot_date': passage.source['snapshot_date'],
            'start': passage.start, 'end': passage.end,
            'text_sha256': hashlib.sha256(passage.text.encode('utf-8')).hexdigest(),
            'topic_text_sha256': passage.topic_text_sha256,
            'corpus_version': corpus.corpus_version,
            'specialties_json': json.dumps(passage.specialties)}


def vector_digest(vector):
    require(len(vector) == DIMENSIONS and all(math.isfinite(float(v)) for v in vector)
            and any(float(v) != 0 for v in vector), 'A stored index vector is invalid.')
    try:
        return hashlib.sha256(struct.pack('<' + 'f' * DIMENSIONS, *vector)).hexdigest()
    except (OverflowError, struct.error):
        raise IndexBuildError('A stored index vector is invalid.') from None


def inspect_rows(collection, corpus, *, new_vectors=None):
    rows = collection.get(include=['documents', 'metadatas', 'embeddings'])
    ids = rows['ids']
    require(len(ids) == len(set(ids)) and set(ids) <= set(corpus.by_id),
            'The index contains invalid or unexpected passage IDs.')
    digests = {}
    for position, key in enumerate(ids):
        passage = corpus.by_id[key]
        require(rows['documents'][position] == passage.text
                and rows['metadatas'][position] == passage_metadata(passage, corpus),
                'Stored passage text or metadata differs from the prepared corpus.')
        stored_vector = rows['embeddings'][position]
        digests[key] = vector_digest(stored_vector)
        if new_vectors is not None and key in new_vectors:
            original = new_vectors[key]
            # Chroma's float32 roundtrip can differ by a few ULPs from a direct cast.
            # Compare new writes numerically, then fingerprint their stored representation.
            require(all(
                math.isclose(float(actual), float(expected), rel_tol=0.00001, abs_tol=0.0000001)
                for actual, expected in zip(stored_vector, original, strict=True)),
                'A stored vector does not preserve the completed embedding values.')
    return digests


def client_for(folder):
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    # Explicit local persistence; no CloudClient, automatic embedding function or telemetry.
    return chromadb.PersistentClient(path=str(folder / 'chroma'),
        settings=ChromaSettings(anonymized_telemetry=False, allow_reset=False))


class LocalIndex:
    def __init__(self, corpus, folder, spec, manifest):
        self.corpus, self.folder, self.spec, self.manifest = corpus, folder, spec, manifest
        self.client = client_for(folder)
        self.collection = self.client.get_collection(COLLECTION, embedding_function=None)

    def verify(self):
        require(self.manifest['status'] == 'complete', 'The local index is not complete.', 'index_not_ready')
        for key, value in self.spec.items():
            require(self.manifest.get(key) == value, 'The index manifest does not match this corpus/configuration.')
        require(self.collection.metadata == {'index_version': self.spec['index_version'],
                    'embedding_space_version': self.spec['embedding_space_version'],
                    'corpus_version': self.corpus.corpus_version, 'mode': self.spec['mode']},
                'The Chroma collection identity does not match this index.')
        require(self.collection.configuration_json['hnsw']['space'] == 'cosine', 'The Chroma distance configuration is invalid.')
        stored = inspect_rows(self.collection, self.corpus)
        require(set(stored) == set(self.corpus.by_id) and stored == self.manifest['vector_sha256'],
                'The index is incomplete or its stored vectors changed.')
        return {'status': 'complete', 'passages': len(stored), 'mode': self.spec['mode'],
                'index_version': self.spec['index_version'], 'corpus_version': self.corpus.corpus_version,
                'embedding_space_version': self.spec['embedding_space_version']}


def index_folder(repository_root, spec):
    root = Path(repository_root).resolve()
    return owned_file(root, Path('data/knowledge/indexes') / spec['index_version'], 'data/knowledge/indexes')


def load_index(corpus, *, repository_root, plan=None, mode='live', expected_index_version=None):
    plan = plan if plan is not None else plan_corpus(corpus)
    spec = index_specification(plan, mode=mode)
    if expected_index_version is not None:
        require(spec['index_version'] == expected_index_version,
                'The local index does not match its configured version.', 'index_not_ready')
    folder = index_folder(repository_root, spec)
    manifest = read_json(folder / 'manifest.json')
    require(manifest.get('status') == 'complete', 'The local index is not complete.', 'index_not_ready')
    if expected_index_version is not None:
        require((folder / 'chroma/chroma.sqlite3').is_file(),
                'The stored Chroma database is missing.', 'index_not_ready')
    index = LocalIndex(corpus, folder, spec, manifest)
    index.verify()
    return index


def build_index(corpus, *, repository_root, embedder, max_usd, plan=None,
                batch_size=32, resume=False, include_probe=False, progress=None):
    require(type(batch_size) is int and 1 <= batch_size <= 32, 'The approved batch size is at most 32 inputs.')
    require(isinstance(max_usd, Decimal) and max_usd.is_finite() and 0 < max_usd <= Decimal('0.10'),
            'This initial embedding step is approved only up to USD 0.10.')
    plan = plan if plan is not None else plan_corpus(corpus)
    require(plan['corpus_version'] == corpus.corpus_version and plan['model'] == MODEL
            and plan['dimensions'] == DIMENSIONS and plan['passages'] == len(corpus.passages),
            'The embedding plan does not match the prepared corpus.')
    mode = embedder.mode
    spec = index_specification(plan, mode=mode)
    folder = index_folder(repository_root, spec)
    folder.mkdir(parents=True, exist_ok=True)
    with exclusive_build(folder):
        manifest_path, usage_path = folder / 'manifest.json', folder / 'usage.json'
        if manifest_path.exists():
            manifest = read_json(manifest_path)
            require(all(manifest.get(key) == value for key, value in spec.items()), 'The existing index has different inputs.')
            if manifest.get('status') == 'complete':
                index = load_index(corpus, repository_root=repository_root, plan=plan, mode=mode)
                return {**index.verify(), 'reused': True, 'provider_calls_this_run': 0}
            require(resume, 'An interrupted build needs an explicit resume request.', 'index_resume_required')
            ledger = read_json(usage_path)
            require(ledger.get('index_version') == spec['index_version']
                    and Decimal(ledger['max_usd']) == max_usd
                    and Decimal(ledger['price_per_million']) == PRICE_PER_MILLION,
                    'The existing budget ledger does not match this approved run.')
        else:
            require(not usage_path.exists(), 'Unmatched usage state requires manual review.')
            manifest = {**spec, 'status': 'building', 'vector_sha256': {}}
            ledger = {'index_version': spec['index_version'], 'reserved_tokens': 0,
                      'confirmed_tokens': 0, 'max_usd': str(max_usd),
                      'price_per_million': str(PRICE_PER_MILLION), 'probe': 'not_attempted'}
            atomic_json(manifest_path, manifest)
            atomic_json(usage_path, ledger)
        budget = PersistentTokenBudget(usage_path, ledger)
        embedder.budget = budget
        client = client_for(folder)
        metadata = {'index_version': spec['index_version'], 'embedding_space_version': spec['embedding_space_version'],
                    'corpus_version': corpus.corpus_version, 'mode': mode}
        collection = client.get_or_create_collection(COLLECTION, embedding_function=None,
            metadata=metadata, configuration=CHROMA_CONFIGURATION)
        require(collection.metadata == metadata and collection.configuration_json['hnsw']['space'] == 'cosine',
                'The existing Chroma collection has a different configuration.')
        stored = inspect_rows(collection, corpus)
        require(stored == manifest['vector_sha256'], 'Unverified partial index writes require manual review.')
        calls = 0
        try:
            if include_probe and budget.ledger['probe'] == 'not_attempted':
                budget.update(probe='attempted')
                result = embedder.embed([PROBE_TEXT]); calls += 1
                budget.update(probe='verified', confirmed_tokens=budget.ledger['confirmed_tokens'] + result.input_tokens)
                if progress:
                    progress({'status': 'probe_verified', 'dimensions': DIMENSIONS, 'input_tokens': result.input_tokens})
            pending = [passage for passage in corpus.passages if passage.passage_id not in stored]
            for start in range(0, len(pending), batch_size):
                batch = pending[start:start + batch_size]
                result = embedder.embed([passage.text for passage in batch]); calls += 1
                budget.update(confirmed_tokens=budget.ledger['confirmed_tokens'] + result.input_tokens)
                collection.add(ids=[p.passage_id for p in batch], embeddings=[list(v) for v in result.vectors],
                    documents=[p.text for p in batch], metadatas=[passage_metadata(p, corpus) for p in batch])
                new_vectors = {p.passage_id: v for p, v in zip(batch, result.vectors, strict=True)}
                previous = stored
                stored = inspect_rows(collection, corpus, new_vectors=new_vectors)
                require(set(stored) == set(previous) | set(new_vectors)
                        and all(stored[key] == digest for key, digest in previous.items()),
                        'The stored vectors do not match the completed embedding batch.')
                manifest.update(vector_sha256=stored)
                atomic_json(manifest_path, manifest)
                if progress:
                    progress({'status': 'indexing', 'completed_passages': len(stored), 'total_passages': len(corpus.passages),
                              'reserved_tokens': budget.reserved_tokens})
            manifest.update(status='complete')
            atomic_json(manifest_path, manifest)
            index = LocalIndex(corpus, folder, spec, manifest)
            summary = index.verify()
            return {**summary, 'reused': False, 'provider_calls_this_run': calls,
                    'reserved_tokens': budget.reserved_tokens, 'confirmed_tokens': budget.ledger['confirmed_tokens'],
                    'reserved_usd': format(Decimal(budget.reserved_tokens) * PRICE_PER_MILLION / 1_000_000, 'f')}
        except BaseException:
            manifest.update(status='interrupted')
            atomic_json(manifest_path, manifest)
            raise


def main():
    parser = argparse.ArgumentParser(description='Verify or explicitly build the approved public-corpus index.')
    parser.add_argument('--repository-root')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--budget-usd', type=Decimal)
    args = parser.parse_args()
    embedder = None
    try:
        root = repository_directory(args.repository_root)
        corpus = load_corpus(repository_root=root)
        plan = plan_corpus(corpus)
        if args.execute:
            settings = read_settings()
            require(settings.enabled and settings.api_key, 'Enable the approved run and configure the key in the local .env.',
                    'configuration_required')
            require(args.budget_usd is not None, 'An explicit approved run budget is required.', 'configuration_required')
            embedder = OpenAIEmbedder(api_key=settings.api_key, enabled=True, timeout_seconds=30,
                                      budget=TokenBudget(args.budget_usd, PRICE_PER_MILLION))
            summary = build_index(corpus, repository_root=root, embedder=embedder, max_usd=args.budget_usd,
                                  plan=plan, resume=args.resume, include_probe=True,
                                  progress=lambda value: print(json.dumps(value), flush=True))
        else:
            summary = load_index(corpus, repository_root=root, plan=plan).verify()
        print(json.dumps(summary))
        return 0
    except (EmbeddingError, CorpusLoadError, IndexBuildError) as error:
        print(json.dumps({'status': 'error', 'code': error.code, 'message': str(error)}), file=sys.stderr)
        return 1
    except Exception:
        print(json.dumps({'status': 'error', 'code': 'index_io_failure',
                          'message': 'The local index operation failed; no payload details are emitted.'}), file=sys.stderr)
        return 1
    finally:
        if embedder is not None:
            embedder.close()


if __name__ == '__main__':
    raise SystemExit(main())
