#!/usr/bin/env bash
# Start the NoteLens public live demo in one container (Railway).
# Live RAG (public_runtime), live extraction and the fitted classifier listen on loopback only;
# the web app reaches them with per-start bearer tokens. Hard caps bound provider spend.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PORT="${PORT:-3000}"

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "Set OPENAI_API_KEY as a Railway variable." >&2
  exit 1
fi
if [[ -z "${NOTELENS_SESSION_ORIGIN:-}" ]]; then
  if [[ -n "${RAILWAY_PUBLIC_DOMAIN:-}" ]]; then
    export NOTELENS_SESSION_ORIGIN="https://${RAILWAY_PUBLIC_DOMAIN}"
  else
    echo "Set NOTELENS_SESSION_ORIGIN (for example https://your-app.up.railway.app)." >&2
    exit 1
  fi
fi

# Free authenticated check; logs only the HTTP status, never the key.
"$ROOT/services/rag/.venv/bin/python" - <<'PY'
import os, urllib.request, urllib.error
key = os.environ['OPENAI_API_KEY']
note = ' (key has surrounding whitespace or quotes)' if key != key.strip().strip('"').strip("'") else ''
try:
    request = urllib.request.Request('https://api.openai.com/v1/models/gpt-6-luna',
                                     headers={'Authorization': 'Bearer ' + key.strip()})
    status = urllib.request.urlopen(request, timeout=15).status
except urllib.error.HTTPError as error:
    status = error.code
except Exception as error:
    status = type(error).__name__
print(f'OpenAI key check: HTTP {status}{note}', flush=True)
PY

token() { head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n'; }
RAG_TOKEN="$(token)"; EXTRACTION_TOKEN="$(token)"; CLASSIFIER_TOKEN="$(token)"; DEMO_TOKEN="$(token)"
RUN_ID="$(cat /proc/sys/kernel/random/uuid)"

RAG_PORT=8101; CLASSIFIER_PORT=8102; EXTRACTION_PORT=8103
# Per-operation caps for this container start (web side) and provider caps (service side).
EXTRACT_LIMIT="${NOTELENS_LIVE_EXTRACT_LIMIT:-150}"
DOC_ANSWER_LIMIT="${NOTELENS_LIVE_DOCUMENT_ANSWER_LIMIT:-150}"
LIT_ANSWER_LIMIT="${NOTELENS_LIVE_LITERATURE_ANSWER_LIMIT:-150}"
D_CALLS=$((EXTRACT_LIMIT + DOC_ANSWER_LIMIT))
D_BUDGET="${NOTELENS_LIVE_EXTRACTION_BUDGET_USD:-5.00}"
CLASSIFIER_MODEL_VERSION="c008-short-text-matched-v1-ec4f77b94c735790aca7cf8a3eb8a83cdc4e263ce2ad56e599e477f219fe6e8d"
CLASSIFIER_MANIFEST_SHA256="affe7af9e2d0f8df46d25642fd2e0cbf0ff3e45f2a8576b9c87cc2cc257d7f32"

RUNTIME_DIR="$(mktemp -d)"
cat > "$RUNTIME_DIR/d-policy.json" <<JSON
{"version": "d-extraction-provider-policy-v1", "approved": true,
 "approved_by": "Nemanja (repository owner)", "operator": "Railway public live demo",
 "scope": "Public live demo ${RUN_ID}", "model_access_confirmed": true, "model": "gpt-6-luna",
 "receipt_path": "d-receipt-${RUN_ID}.json", "automatic_retries": 0,
 "max_input_tokens": 64000, "max_output_tokens": 12288, "max_provider_calls": ${D_CALLS},
 "remaining_budget_usd": "${D_BUDGET}", "input_usd_per_million_tokens": "0.1375",
 "output_usd_per_million_tokens": "0.55", "timeout_seconds": 30, "input_format": "messages",
 "output_format": "quote_hints", "prompt_profile": "coverage_v2", "reasoning_effort": "low",
 "run_id": "${RUN_ID}"}
JSON

export NEXT_TELEMETRY_DISABLED=1 ANONYMIZED_TELEMETRY=False PYTHONDONTWRITEBYTECODE=1

(cd "$ROOT" && env NOTELENS_RAG_SERVICE_TOKEN="$RAG_TOKEN" NOTELENS_RAG_ALLOW_PAID_EMBEDDINGS=true \
   NOTELENS_RAG_ALLOW_PAID_ASSESSMENTS=true NOTELENS_RAG_PUBLIC_MAX_REQUESTS="$LIT_ANSWER_LIMIT" \
   NOTELENS_RAG_PUBLIC_BUDGET_USD="${NOTELENS_LIVE_RAG_BUDGET_USD:-2.00}" \
   NOTELENS_RAG_PUBLIC_RECEIPT_DIR="$RUNTIME_DIR" \
   services/rag/.venv/bin/python -B -m notelens_rag.public_runtime --port "$RAG_PORT") &

(cd "$ROOT/services/extraction" && env NOTELENS_SERVICE_TOKEN="$EXTRACTION_TOKEN" NOTELENS_MODE=live \
   NOTELENS_EXTRACTION_PROVIDER_POLICY="$RUNTIME_DIR/d-policy.json" \
   .venv/bin/python -B -m notelens_extraction.cli serve --port "$EXTRACTION_PORT") &

(cd "$ROOT/services/classifier" && env -u OPENAI_API_KEY NOTELENS_CLASSIFIER_MODE=live \
   NOTELENS_CLASSIFIER_SERVICE_TOKEN="$CLASSIFIER_TOKEN" \
   .venv/bin/python -B -m notelens_classifier --port "$CLASSIFIER_PORT" \
   --development-model "$ROOT/services/classifier/.cache/model" \
   --model-manifest-sha256 "$CLASSIFIER_MANIFEST_SHA256") &

wait_ready() { # port token name
  "$ROOT/services/rag/.venv/bin/python" - "$1" "$2" "$3" <<'PY'
import json, sys, time, urllib.request
port, token, name = sys.argv[1:4]
deadline = time.monotonic() + 120
while time.monotonic() < deadline:
    try:
        request = urllib.request.Request(f'http://127.0.0.1:{port}/health/ready',
                                         headers={'Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(request, timeout=3) as response:
            body = json.loads(response.read(2048))
            if response.status == 200 and body.get('mode') == 'live':
                print(f'{name} ready (live).')
                sys.exit(0)
    except Exception:
        pass
    time.sleep(0.5)
print(f'{name} did not become ready in live mode.', file=sys.stderr)
sys.exit(1)
PY
}
wait_ready "$RAG_PORT" "$RAG_TOKEN" rag
wait_ready "$EXTRACTION_PORT" "$EXTRACTION_TOKEN" extraction
wait_ready "$CLASSIFIER_PORT" "$CLASSIFIER_TOKEN" classifier

cd "$ROOT/apps/web"
env -u OPENAI_API_KEY NOTELENS_MODE=mock NOTELENS_DEMO_RUN="$RUN_ID" NOTELENS_DEMO_TOKEN="$DEMO_TOKEN" \
    NOTELENS_DEMO_RAG_PORT="$RAG_PORT" NOTELENS_DEMO_CLASSIFIER_PORT="$CLASSIFIER_PORT" \
    NOTELENS_DEMO_EXTRACTION_PORT="$EXTRACTION_PORT" \
    NOTELENS_BOUNDED_EVALUATION=public-live \
    NOTELENS_BOUNDED_LIMITS="{\"extract\": ${EXTRACT_LIMIT}, \"document-answer\": ${DOC_ANSWER_LIMIT}, \"literature-answer\": ${LIT_ANSWER_LIMIT}}" \
    NOTELENS_BOUNDED_HTTP_TIMEOUT_MS=240000 \
    NOTELENS_BOUNDED_RAG_TOKEN="$RAG_TOKEN" NOTELENS_BOUNDED_EXTRACTION_TOKEN="$EXTRACTION_TOKEN" \
    NOTELENS_LOCAL_CLASSIFIER_PROFILE=fitted NOTELENS_LOCAL_CLASSIFIER_PORT="$CLASSIFIER_PORT" \
    NOTELENS_LOCAL_CLASSIFIER_MODEL_VERSION="$CLASSIFIER_MODEL_VERSION" \
    NOTELENS_CLASSIFIER_SERVICE_TOKEN="$CLASSIFIER_TOKEN" \
    node "$ROOT/node_modules/next/dist/bin/next" start --hostname 0.0.0.0 --port "$PORT" &

echo "NoteLens live web listening on port $PORT for origin $NOTELENS_SESSION_ORIGIN"
wait -n
echo "A NoteLens process exited; stopping the container." >&2
exit 1
