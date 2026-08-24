#!/usr/bin/env bash
# Open the authenticated private owner-review inbox through Cloud Run's local proxy.

set -euo pipefail

PROJECT_ID="vice-ceo-agentic-2026"
REGION="us-central1"
SERVICE="vice-ceo-registry-worker"
PORT="8765"
OPEN_BROWSER=true
VIEW="operations"
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

usage() {
  cat <<'EOF'
Usage: scripts/open-owner-review.sh [options]

Opens the private Registry Change Watch owner workspace through an
authenticated local Cloud Run proxy. It never creates a queue item, sends an
email, or performs a business action.

Options:
  --project ID       Google Cloud project (default: vice-ceo-agentic-2026)
  --region REGION    Cloud Run region (default: us-central1)
  --service NAME     Cloud Run service (default: vice-ceo-registry-worker)
  --port PORT        Local-only proxy port (default: 8765)
  --view NAME        operations or inbox (default: operations)
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
    --view) VIEW="$2"; shift 2 ;;
    --no-open) OPEN_BROWSER=false; shift ;;
    --help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

GCLOUD_BIN="${GCLOUD_BIN:-$(command -v gcloud 2>/dev/null || true)}"
if [[ -z "$GCLOUD_BIN" && -x "/Users/${USER}/.local/google-cloud-sdk/bin/gcloud" ]]; then
  GCLOUD_BIN="/Users/${USER}/.local/google-cloud-sdk/bin/gcloud"
fi
if [[ -z "$GCLOUD_BIN" ]]; then
  echo "gcloud is required. Install Google Cloud CLI or set GCLOUD_BIN to its executable path." >&2
  exit 1
fi
if [[ -z "${CLOUDSDK_PYTHON:-}" && -x "$SCRIPT_DIR/../.venv/bin/python" ]]; then
  export CLOUDSDK_PYTHON="$SCRIPT_DIR/../.venv/bin/python"
fi
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1024 || PORT > 65535 )); then
  echo "--port must be an available local port between 1024 and 65535." >&2
  exit 2
fi

case "$VIEW" in
  operations) OWNER_PATH="/owner/registry-operations/console" ;;
  inbox) OWNER_PATH="/owner/registry-actions/inbox" ;;
  *) echo "--view must be operations or inbox." >&2; exit 2 ;;
esac

OWNER_URL="http://127.0.0.1:${PORT}${OWNER_PATH}"
PROXY_LOG=$(mktemp -t vice-ceo-owner-review.XXXXXX)
cleanup() {
  if [[ -n "${PROXY_PID:-}" ]] && kill -0 "$PROXY_PID" 2>/dev/null; then
    kill "$PROXY_PID" 2>/dev/null || true
  fi
  rm -f "$PROXY_LOG"
}
trap cleanup EXIT INT TERM

echo "Starting an authenticated local proxy to ${SERVICE}…"
"$GCLOUD_BIN" run services proxy "$SERVICE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --port "$PORT" \
  >"$PROXY_LOG" 2>&1 &
PROXY_PID=$!

for attempt in {1..30}; do
  if curl --silent --fail "$OWNER_URL" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$PROXY_PID" 2>/dev/null; then
    cat "$PROXY_LOG" >&2 || true
    exit 1
  fi
  sleep 1
done

if ! curl --silent --fail "$OWNER_URL" >/dev/null 2>&1; then
  echo "The authenticated owner-review proxy did not become ready." >&2
  exit 1
fi

echo "Owner workspace is available at: $OWNER_URL"
if [[ "$OPEN_BROWSER" == true ]]; then
  open "$OWNER_URL"
fi
echo "Press Ctrl-C here when you are finished reviewing."
wait "$PROXY_PID"
