#!/usr/bin/env bash
# Guarded Cloud Shell deployment for the synthetic-only Vice CEO demo.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/deploy-cloud-run.sh --project PROJECT --region REGION --service SERVICE \
    --service-account SERVICE_ACCOUNT --revision GIT_REVISION [--execute]

Without --execute this script prints a pinned, no-effect plan only.
EOF
}

PROJECT_ID=""
REGION=""
SERVICE_NAME=""
SERVICE_ACCOUNT=""
REVISION=""
EXECUTE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT_ID="${2:?project value required}"; shift 2 ;;
    --region) REGION="${2:?region value required}"; shift 2 ;;
    --service) SERVICE_NAME="${2:?service value required}"; shift 2 ;;
    --service-account) SERVICE_ACCOUNT="${2:?service account value required}"; shift 2 ;;
    --revision) REVISION="${2:?revision value required}"; shift 2 ;;
    --execute) EXECUTE=true; shift ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ -n "$PROJECT_ID" && -n "$REGION" && -n "$SERVICE_NAME" && -n "$SERVICE_ACCOUNT" && -n "$REVISION" ]] || {
  usage >&2
  exit 2
}
[[ "$PROJECT_ID" =~ ^[a-z][a-z0-9-]{4,62}$ ]] || { echo "invalid_project_id" >&2; exit 2; }
[[ "$REGION" =~ ^[a-z]+-[a-z0-9]+[0-9]$ ]] || { echo "invalid_region" >&2; exit 2; }
[[ "$SERVICE_NAME" =~ ^[a-z]([-a-z0-9]*[a-z0-9])?$ ]] || { echo "invalid_service_name" >&2; exit 2; }
[[ "$SERVICE_ACCOUNT" =~ ^[^@[:space:]]+@[^@[:space:]]+\.iam\.gserviceaccount\.com$ ]] || { echo "invalid_service_account" >&2; exit 2; }
[[ "$REVISION" =~ ^[0-9a-fA-F]{7,40}$ ]] || { echo "invalid_revision" >&2; exit 2; }

command -v git >/dev/null || { echo "git_cli_required_for_revision_pinning" >&2; exit 1; }
RUNTIME_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKED_OUT_REVISION="$(git -C "$RUNTIME_ROOT" rev-parse --verify HEAD | tr '[:upper:]' '[:lower:]')"
REQUESTED_REVISION="$(tr '[:upper:]' '[:lower:]' <<<"$REVISION")"
[[ "$CHECKED_OUT_REVISION" == "$REQUESTED_REVISION"* || "$REQUESTED_REVISION" == "$CHECKED_OUT_REVISION"* ]] || {
  echo "checked_out_revision_does_not_match_requested_revision" >&2
  exit 1
}

if [[ "$EXECUTE" != true ]]; then
  echo "Plan only. No Cloud Run deployment will occur without --execute."
  printf 'Project: %s\nRegion: %s\nService: %s\nService account: %s\nPinned revision: %s\n' \
    "$PROJECT_ID" "$REGION" "$SERVICE_NAME" "$SERVICE_ACCOUNT" "$CHECKED_OUT_REVISION"
  echo "Runtime: synthetic-only, in-memory claims, no connector flags."
  exit 0
fi

command -v gcloud >/dev/null || { echo "gcloud_cli_required" >&2; exit 1; }

gcloud run deploy "$SERVICE_NAME" \
  --source "$RUNTIME_ROOT" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --service-account "$SERVICE_ACCOUNT" \
  --no-allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,GOOGLE_GENAI_USE_VERTEXAI=TRUE,VICE_CEO_CLAIM_STORE=in_memory,VICE_CEO_PROVIDER_CANARY_ENABLED=false" \
  --labels "app=vice-ceo-hackathon-runtime,runtime=synthetic-only,revision=${CHECKED_OUT_REVISION:0:63}"

READY_REVISION="$(gcloud run services describe "$SERVICE_NAME" --project "$PROJECT_ID" --region "$REGION" --format='value(status.latestReadyRevisionName)')"
[[ -n "$READY_REVISION" ]] || { echo "cloud_run_ready_revision_unavailable" >&2; exit 1; }
printf 'Deployment command completed. Ready Cloud Run revision: %s\n' "$READY_REVISION"
echo "Verify through an authenticated local proxy before any public-access decision."
