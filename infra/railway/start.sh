#!/usr/bin/env bash
# Start the NoteLens key-free mock stack in one container (Railway).
# The web app reaches the three Python services only on 127.0.0.1, and the
# services accept loopback clients only, so all four processes share this container.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PORT="${PORT:-3000}"

if [[ -z "${NOTELENS_SESSION_ORIGIN:-}" ]]; then
  if [[ -n "${RAILWAY_PUBLIC_DOMAIN:-}" ]]; then
    export NOTELENS_SESSION_ORIGIN="https://${RAILWAY_PUBLIC_DOMAIN}"
  else
    echo "Set NOTELENS_SESSION_ORIGIN (for example https://your-app.up.railway.app)." >&2
    exit 1
  fi
fi

TOKEN="$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
RUN_MARKER="$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')"

export NOTELENS_MODE=mock NOTELENS_RAG_MODE=mock NOTELENS_CLASSIFIER_MODE=mock
export NEXT_TELEMETRY_DISABLED=1 ANONYMIZED_TELEMETRY=False PYTHONDONTWRITEBYTECODE=1

RAG_PORT=8101
CLASSIFIER_PORT=8102
EXTRACTION_PORT=8103

start_service() { # name module port token_variable
  local name="$1" module="$2" port="$3" token_var="$4"
  (cd "$ROOT/services/$name" && env "$token_var=$TOKEN" .venv/bin/python -B -m uvicorn "$module.main:app" \
     --host 127.0.0.1 --port "$port" --no-proxy-headers --no-access-log --log-level warning) &
}

start_service rag notelens_rag "$RAG_PORT" NOTELENS_RAG_SERVICE_TOKEN
start_service classifier notelens_classifier "$CLASSIFIER_PORT" NOTELENS_CLASSIFIER_SERVICE_TOKEN
start_service extraction notelens_extraction "$EXTRACTION_PORT" NOTELENS_SERVICE_TOKEN

# Wait until every service reports ready with the bearer token.
for port in "$RAG_PORT" "$CLASSIFIER_PORT" "$EXTRACTION_PORT"; do
  "$ROOT/services/rag/.venv/bin/python" - "$port" "$TOKEN" <<'PY'
import sys, time, urllib.request
port, token = sys.argv[1], sys.argv[2]
deadline = time.monotonic() + 60
while time.monotonic() < deadline:
    try:
        request = urllib.request.Request(f'http://127.0.0.1:{port}/health/ready',
                                         headers={'Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(request, timeout=2) as response:
            if response.status == 200:
                sys.exit(0)
    except Exception:
        pass
    time.sleep(0.5)
print(f'Service on port {port} did not become ready.', file=sys.stderr)
sys.exit(1)
PY
done
echo "Python mock services ready."

cd "$ROOT/apps/web"
env NOTELENS_DEMO_RUN="$RUN_MARKER" NOTELENS_DEMO_TOKEN="$TOKEN" \
    NOTELENS_DEMO_RAG_PORT="$RAG_PORT" NOTELENS_DEMO_CLASSIFIER_PORT="$CLASSIFIER_PORT" \
    NOTELENS_DEMO_EXTRACTION_PORT="$EXTRACTION_PORT" \
    node "$ROOT/node_modules/next/dist/bin/next" start --hostname 0.0.0.0 --port "$PORT" &

echo "NoteLens web listening on port $PORT for origin $NOTELENS_SESSION_ORIGIN"
# If any process exits, stop the container so the platform restarts it.
wait -n
echo "A NoteLens process exited; stopping the container." >&2
exit 1
