#!/usr/bin/env bash
# Open the authenticated private owner-review inbox through Cloud Run's local proxy.

set -euo pipefail

PROJECT_ID="vice-ceo-agentic-2026"
REGION="us-central1"
SERVICE="vice-ceo-registry-worker"
PORT="8765"
OPEN_BROWSER=true

usage() {
  cat <<'EOF'
Usage: scripts/open-owner-review.sh [options]

Opens the private Registry Change Watch owner-review inbox through an
authenticated local Cloud Run proxy. It never creates a queue item, sends an
email, or performs a business action.

Options:
  --project ID       Google Cloud project (default: vice-ceo-agentic-2026)
  --region REGION    Cloud Run region (default: us-central1)
  --service NAME     Cloud Run service (default: vice-ceo-registry-worker)
  --port PORT        Local-only proxy port (default: 8765)
  --no-open          Do not open the browser automatically
  --help             Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT_ID="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --service) SERVICE="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --no-open) OPEN_BROWSER=false; shift ;;
    --help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud is required. Install or add Google Cloud CLI to PATH first." >&2
  exit 1
fi
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1024 || PORT > 65535 )); then
  echo "--port must be an available local port between 1024 and 65535." >&2
  exit 2
fi

INBOX_URL="http://127.0.0.1:${PORT}/owner/registry-actions/inbox"
PROXY_LOG=$(mktemp -t vice-ceo-owner-review.XXXXXX)
cleanup() {
  if [[ -n "${PROXY_PID:-}" ]] && kill -0 "$PROXY_PID" 2>/dev/null; then
    kill "$PROXY_PID" 2>/dev/null || true
  fi
  rm -f "$PROXY_LOG"
}
trap cleanup EXIT INT TERM

echo "Starting an authenticated local proxy to ${SERVICE}…"
gcloud run services proxy "$SERVICE" --project "$PROJECT_ID" --region "$REGION" --port "$PORT" >"$PROXY_LOG" 2>&1 &
PROXY_PID=$!

for attempt in {1..30}; do
  if curl --silent --fail "$INBOX_URL" >/dev/null 2>&1; then break; fi
  if ! kill -0 "$PROXY_PID" 2>/dev/null; then cat "$PROXY_LOG" >&2 || true; exit 1; fi
  sleep 1
done
if ! curl --silent --fail "$INBOX_URL" >/dev/null 2>&1; then
  echo "The authenticated owner-review proxy did not become ready." >&2
  exit 1
fi

echo "Owner review is available at: $INBOX_URL"
if [[ "$OPEN_BROWSER" == true ]]; then open "$INBOX_URL"; fi
echo "Press Ctrl-C here when you are finished reviewing."
wait "$PROXY_PID"
