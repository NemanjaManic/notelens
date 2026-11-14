"""Plan public-corpus embeddings offline; paid calls require explicit activation."""

import argparse
from dataclasses import dataclass, field
from decimal import Decimal
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import sys
import threading

from dotenv import dotenv_values
import openai
import tiktoken

from .ingestion import CorpusLoadError, DEFAULT_MANIFEST, load_corpus


SERVICE_ROOT = Path(__file__).resolve().parents[2]
MODEL = 'text-embedding-3-small'
DIMENSIONS = 1536
PRICE_PER_MILLION = Decimal('0.02')
PRICE_CHECKED_ON = '2026-11-14'
TOKENIZER_URL = 'https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken'
TOKENIZER_SHA256 = '223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7'
_tokenizer_lock = threading.Lock()


class EmbeddingError(ValueError):
    """A fixed diagnostic that omits credentials, request text and upstream bodies."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def require(condition, message, code='embedding_configuration'):
    if not condition:
        raise EmbeddingError(code, message)


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class EmbeddingSettings:
    api_key: str | None = field(default=None, repr=False)
    enabled: bool = False
    model: str = MODEL
    dimensions: int = DIMENSIONS

    def public_summary(self):
        return {'model': self.model, 'dimensions': self.dimensions,
                'paid_embeddings_enabled': self.enabled, 'key_present': bool(self.api_key)}


def read_settings(env_file=None):
    """Process variables override this service's explicit .env; interpolation is off."""
    path = Path(env_file) if env_file is not None else SERVICE_ROOT / '.env'
    try:
        values = dict(dotenv_values(path, interpolate=False)) if path.is_file() else {}
    except (OSError, UnicodeError):
        raise EmbeddingError('embedding_configuration', 'The local environment file is unreadable.') from None
    keys = ('OPENAI_API_KEY', 'NOTELENS_RAG_ALLOW_PAID_EMBEDDINGS',
            'NOTELENS_RAG_EMBEDDING_MODEL', 'NOTELENS_RAG_EMBEDDING_DIMENSIONS')
    values.update({key: os.environ[key] for key in keys if key in os.environ})
    enabled = values.get('NOTELENS_RAG_ALLOW_PAID_EMBEDDINGS') or 'false'
    require(enabled in ('true', 'false'), 'Paid embedding activation must be true or false.')
    require((values.get('NOTELENS_RAG_EMBEDDING_MODEL') or MODEL) == MODEL,
            'A different embedding model requires a reviewed configuration and new index.')
    require((values.get('NOTELENS_RAG_EMBEDDING_DIMENSIONS') or str(DIMENSIONS)) == str(DIMENSIONS),
            'Different embedding dimensions require a reviewed configuration and new index.')
    key = values.get('OPENAI_API_KEY')
    return EmbeddingSettings(api_key=key if key and key.strip() else None, enabled=enabled == 'true')


def local_tokenizer(*, prepare=False):
    """Normal execution requires the verified vocabulary locally, without network."""
    with _tokenizer_lock:
        cache = Path(os.environ.setdefault('TIKTOKEN_CACHE_DIR', str(SERVICE_ROOT / '.cache/tiktoken')))
        vocabulary = cache / hashlib.sha1(TOKENIZER_URL.encode()).hexdigest()
        if not prepare:
            try:
                valid = hashlib.sha256(vocabulary.read_bytes()).hexdigest() == TOKENIZER_SHA256
            except OSError:
                valid = False
            require(valid, 'Prepare the verified tokenizer cache before offline token counting.', 'tokenizer_unavailable')
        try:
            return tiktoken.get_encoding('cl100k_base')
        except Exception:
            raise EmbeddingError('tokenizer_unavailable', 'The verified tokenizer could not be loaded.') from None


def count_tokens(text, encoder):
    require(isinstance(text, str) and bool(text.strip()), 'Embedding input must contain text.', 'embedding_input_invalid')
    try:
        text.encode('utf-8', errors='strict')
        # Treat literal special-token strings as ordinary, unchanged source text.
        count = len(encoder.encode(text, disallowed_special=()))
    except (UnicodeError, ValueError):
        raise EmbeddingError('embedding_input_invalid', 'Embedding input must be valid Unicode text.') from None
    require(0 < count <= 8192, 'Embedding input exceeds the model token limit.', 'embedding_input_invalid')
    return count


def plan_corpus(corpus, *, encoder=None):
    encoder = encoder if encoder is not None else local_tokenizer()
    counts = [count_tokens(passage.text, encoder) for passage in corpus.passages]
    require(bool(counts), 'The corpus has no passages.', 'embedding_input_invalid')
    space = {'provider': 'openai', 'model': MODEL, 'dimensions': DIMENSIONS,
             'input_policy': 'unchanged-canonical-passage-text-v1'}
    plan_identity = {'embedding_space_version': identity(space), 'corpus_version': corpus.corpus_version,
                     'passage_manifest_sha256': corpus.manifest_sha256,
                     'passage_artifact_sha256': corpus.artifact_sha256}
    return {'status': 'planned', **space, **plan_identity, 'embedding_plan_version': identity(plan_identity),
            'topics': corpus.topic_count, 'passages': len(counts), 'input_tokens': sum(counts),
            'max_passage_tokens': max(counts), 'tokenizer': 'cl100k_base',
            'tiktoken_version': version('tiktoken'), 'price_usd_per_million_tokens': str(PRICE_PER_MILLION),
            'price_checked_on': PRICE_CHECKED_ON,
            'estimated_usd': format(Decimal(sum(counts)) * PRICE_PER_MILLION / 1_000_000, 'f'),
            'provider_calls': 0}


@dataclass
class TokenBudget:
    """A per-run reservation limit, not an account-wide provider spending cap."""

    max_usd: Decimal
    price_per_million: Decimal
    reserved_tokens: int = field(default=0, init=False)
    _lock: object = field(default_factory=threading.Lock, init=False, repr=False)

    def __post_init__(self):
        require(all(isinstance(v, Decimal) and v.is_finite() and v > 0
                    for v in (self.max_usd, self.price_per_million)),
                'A positive finite budget and reviewed token price are required.')

    def reserve(self, tokens):
        require(type(tokens) is int and tokens > 0, 'A positive token reservation is required.')
        with self._lock:
            amount = Decimal(self.reserved_tokens + tokens) * self.price_per_million / 1_000_000
            require(amount <= self.max_usd, 'The embedding run budget would be exceeded.', 'budget_exceeded')
            # Failed/uncertain requests keep their reservation; never retry them silently.
            self.reserved_tokens += tokens


@dataclass(frozen=True)
class EmbeddingBatch:
    vectors: tuple[tuple[float, ...], ...] = field(repr=False)
    input_tokens: int
    model: str = MODEL


class OpenAIEmbedder:
    def __init__(self, *, api_key, enabled, timeout_seconds, budget, encoder=None, http_client=None):
        require(type(enabled) is bool, 'Paid embedding activation must be explicit.')
        require(isinstance(api_key, str) and bool(api_key.strip()), 'The server-side API key is not configured.')
        require(type(timeout_seconds) in (int, float) and math.isfinite(timeout_seconds) and timeout_seconds > 0,
                'An explicit positive request timeout is required.')
        require(isinstance(budget, TokenBudget), 'An explicit embedding budget is required.')
        self.enabled, self.budget = enabled, budget
        self.encoder = encoder if encoder is not None else local_tokenizer()
        self.client = openai.OpenAI(api_key=api_key, base_url='https://api.openai.com/v1',
                                    timeout=timeout_seconds, max_retries=0, http_client=http_client)

    def close(self):
        self.client.close()

    def embed(self, texts):
        require(self.enabled, 'Paid embedding execution is disabled.', 'configuration_required')
        require(isinstance(texts, (tuple, list)) and 1 <= len(texts) <= 2048,
                'An embedding batch must contain between 1 and 2048 inputs.', 'embedding_input_invalid')
        counts = [count_tokens(text, self.encoder) for text in texts]
        total = sum(counts)
        require(total <= 300_000, 'The embedding request exceeds its token limit.', 'embedding_input_invalid')
        self.budget.reserve(total)
        try:
            raw = self.client.embeddings.with_raw_response.create(model=MODEL, input=list(texts),
                                                                  dimensions=DIMENSIONS, encoding_format='float')
        except openai.APITimeoutError:
            raise EmbeddingError('timeout', 'The embedding provider request timed out.') from None
        except openai.RateLimitError:
            raise EmbeddingError('rate_limit', 'The embedding provider rate limit was reached.') from None
        except (openai.AuthenticationError, openai.PermissionDeniedError):
            raise EmbeddingError('provider_authentication', 'The embedding provider rejected authentication or permissions.') from None
        except openai.APIError:
            raise EmbeddingError('provider_unavailable', 'The embedding provider request failed.') from None
        try:
            # Inspect native JSON before SDK/Pydantic coercion could turn booleans into floats.
            result = raw.http_response.json()
            require(isinstance(result, dict) and result.get('model') == MODEL and result.get('object') == 'list',
                    'The embedding response identity is invalid.', 'invalid_upstream')
            usage = result['usage']
            require(type(usage['prompt_tokens']) is int and type(usage['total_tokens']) is int
                    and usage['prompt_tokens'] == usage['total_tokens'] == total,
                    'The embedding response usage does not match the counted input.', 'invalid_upstream')
            require(isinstance(result['data'], list) and len(result['data']) == len(texts),
                    'The embedding response count is invalid.', 'invalid_upstream')
            vectors = {}
            for row in result['data']:
                index = row['index']
                require(type(index) is int and 0 <= index < len(texts) and index not in vectors
                        and row['object'] == 'embedding', 'The embedding response indices are invalid.', 'invalid_upstream')
                vector = row['embedding']
                require(isinstance(vector, list) and len(vector) == DIMENSIONS
                        and all(type(v) in (int, float) and math.isfinite(v) for v in vector)
                        and any(v != 0 for v in vector), 'An embedding vector is invalid.', 'invalid_upstream')
                vectors[index] = tuple(float(v) for v in vector)
            return EmbeddingBatch(tuple(vectors[i] for i in range(len(texts))), total)
        except EmbeddingError:
            raise
        except (ValueError, AttributeError, TypeError, KeyError, OverflowError):
            raise EmbeddingError('invalid_upstream', 'The embedding response is malformed.') from None


def main():
    parser = argparse.ArgumentParser(description='Plan embeddings offline; this command never calls the model API.')
    parser.add_argument('--repository-root')
    parser.add_argument('--manifest', default=DEFAULT_MANIFEST)
    parser.add_argument('--expected-corpus-version')
    parser.add_argument('--prepare-tokenizer', action='store_true',
                        help='Download the public tokenizer vocabulary only; no source text or API key is sent.')
    args = parser.parse_args()
    try:
        if args.prepare_tokenizer:
            local_tokenizer(prepare=True)
            print(json.dumps({'status': 'tokenizer_ready', 'tokenizer': 'cl100k_base', 'provider_calls': 0}))
            return 0
        settings = read_settings()
        corpus = load_corpus(repository_root=args.repository_root, manifest=args.manifest,
                             expected_corpus_version=args.expected_corpus_version)
        print(json.dumps({**plan_corpus(corpus), **settings.public_summary()}))
        return 0
    except (EmbeddingError, CorpusLoadError) as error:
        print(json.dumps({'status': 'error', 'code': error.code, 'message': str(error)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
