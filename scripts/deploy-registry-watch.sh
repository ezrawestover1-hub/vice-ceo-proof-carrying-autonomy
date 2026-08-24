#!/usr/bin/env bash
# Deploy the isolated Registry Change Watch worker and its reviewer-only demo.
# Plan mode is default. --execute creates billable Google Cloud resources.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/deploy-registry-watch.sh --project PROJECT --region REGION \
    --worker-service WORKER --demo-service DEMO --service-account SERVICE_ACCOUNT \
    --scheduler-service-account SCHEDULER_ACCOUNT --revision GIT_REVISION \
    --sources-file SOURCES.json \
    [--model-location global|us|eu] [--gemini-briefs] \
    [--resend-secret SECRET --brief-from ADDRESS --brief-to ADDRESS] \\
    [--enable-internal-delivery-probe] [--execute]

SOURCES.json must be a nonempty JSON array of reviewed source objects. Each
object records source_id, display_name, canonical_url, jurisdiction,
source_owner, refresh_schedule, and operational_focus. It contains public URLs
only. The deployment creates one private Scheduler job per source.
Without --execute, this command performs no Google Cloud operation.
EOF
}

PROJECT_ID=""
REGION=""
WORKER_SERVICE=""
DEMO_SERVICE=""
SERVICE_ACCOUNT=""
SCHEDULER_SERVICE_ACCOUNT=""
REVISION=""
SOURCES_FILE=""
MODEL_LOCATION="us"
GEMINI_BRIEFS=false
RESEND_SECRET=""
BRIEF_FROM=""
BRIEF_TO=""
INTERNAL_DELIVERY_PROBE_ENABLED=false
EXECUTE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT_ID="${2:?project value required}"; shift 2 ;;
    --region) REGION="${2:?region value required}"; shift 2 ;;
    --worker-service) WORKER_SERVICE="${2:?worker service required}"; shift 2 ;;
    --demo-service) DEMO_SERVICE="${2:?demo service required}"; shift 2 ;;
    --service-account) SERVICE_ACCOUNT="${2:?service account required}"; shift 2 ;;
    --scheduler-service-account) SCHEDULER_SERVICE_ACCOUNT="${2:?scheduler account required}"; shift 2 ;;
    --revision) REVISION="${2:?revision required}"; shift 2 ;;
    --sources-file) SOURCES_FILE="${2:?sources file required}"; shift 2 ;;
    --model-location) MODEL_LOCATION="${2:?model location required}"; shift 2 ;;
    --gemini-briefs) GEMINI_BRIEFS=true; shift ;;
    --resend-secret) RESEND_SECRET="${2:?resend secret name required}"; shift 2 ;;
    --brief-from) BRIEF_FROM="${2:?brief sender required}"; shift 2 ;;
    --brief-to) BRIEF_TO="${2:?brief recipient required}"; shift 2 ;;
    --enable-internal-delivery-probe) INTERNAL_DELIVERY_PROBE_ENABLED=true; shift ;;
    --execute) EXECUTE=true; shift ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ -n "$PROJECT_ID" && -n "$REGION" && -n "$WORKER_SERVICE" && -n "$DEMO_SERVICE" && -n "$SERVICE_ACCOUNT" && -n "$SCHEDULER_SERVICE_ACCOUNT" && -n "$REVISION" && -n "$SOURCES_FILE" ]] || { usage >&2; exit 2; }
[[ "$PROJECT_ID" =~ ^[a-z][a-z0-9-]{4,62}$ ]] || { echo "invalid_project_id" >&2; exit 2; }
[[ "$REGION" =~ ^[a-z]+-[a-z0-9]+[0-9]$ ]] || { echo "invalid_region" >&2; exit 2; }
[[ "$WORKER_SERVICE" =~ ^[a-z]([-a-z0-9]*[a-z0-9])?$ && "$DEMO_SERVICE" =~ ^[a-z]([-a-z0-9]*[a-z0-9])?$ ]] || { echo "invalid_service_name" >&2; exit 2; }
[[ "$SERVICE_ACCOUNT" =~ ^[^@[:space:]]+@[^@[:space:]]+\.iam\.gserviceaccount\.com$ && "$SCHEDULER_SERVICE_ACCOUNT" =~ ^[^@[:space:]]+@[^@[:space:]]+\.iam\.gserviceaccount\.com$ ]] || { echo "invalid_service_account" >&2; exit 2; }
[[ "$REVISION" =~ ^[0-9a-fA-F]{7,40}$ ]] || { echo "invalid_revision" >&2; exit 2; }
[[ "$MODEL_LOCATION" =~ ^(global|us|eu)$ ]] || { echo "invalid_model_location" >&2; exit 2; }
[[ -f "$SOURCES_FILE" ]] || { echo "registry_sources_file_missing" >&2; exit 2; }
if [[ -n "$RESEND_SECRET$BRIEF_FROM$BRIEF_TO" ]] && [[ -z "$RESEND_SECRET" || -z "$BRIEF_FROM" || -z "$BRIEF_TO" ]]; then
  echo "resend_owner_brief_configuration_incomplete" >&2
  exit 2
fi
if [[ -n "$RESEND_SECRET" ]]; then
  [[ "$RESEND_SECRET" =~ ^[A-Za-z][A-Za-z0-9_-]{0,254}$ ]] || { echo "invalid_resend_secret_name" >&2; exit 2; }
  [[ "$BRIEF_FROM" =~ ^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$ ]] || { echo "invalid_brief_from" >&2; exit 2; }
  [[ "$BRIEF_TO" =~ ^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$ ]] || { echo "invalid_brief_to" >&2; exit 2; }
fi
if [[ "$INTERNAL_DELIVERY_PROBE_ENABLED" == true && -z "$RESEND_SECRET" ]]; then
  echo "internal_delivery_probe_requires_resend_owner_brief_configuration" >&2
  exit 2
fi
command -v python3 >/dev/null || { echo "python3_required" >&2; exit 1; }

SOURCES_JSON="$(python3 - "$SOURCES_FILE" <<'PY'
import json, sys
expected = {
    "source_id", "display_name", "canonical_url", "jurisdiction",
    "source_owner", "refresh_schedule", "operational_focus",
}
with open(sys.argv[1], encoding="utf-8") as source:
    value = json.load(source)
if not isinstance(value, list) or not value:
    raise SystemExit("registry_sources_must_be_nonempty_array")
if any(not isinstance(item, dict) or set(item) != expected for item in value):
    raise SystemExit("registry_sources_fields_invalid")
if any(not all(isinstance(item[key], str) and item[key].strip() for key in expected) for item in value):
    raise SystemExit("registry_sources_values_invalid")
if any(not item["canonical_url"].startswith("https://") for item in value):
    raise SystemExit("registry_sources_require_https")
if any(not item["source_id"].replace("_", "").isalnum() for item in value):
    raise SystemExit("registry_source_ids_must_be_alphanumeric_or_underscore")
if any("\n" in item["refresh_schedule"] or "\r" in item["refresh_schedule"] for item in value):
    raise SystemExit("registry_source_schedule_invalid")
print(json.dumps(value, separators=(",", ":")))
PY
)"

RUNTIME_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKED_OUT_REVISION="$(git -C "$RUNTIME_ROOT" rev-parse --verify HEAD | tr '[:upper:]' '[:lower:]')"
REQUESTED_REVISION="$(tr '[:upper:]' '[:lower:]' <<<"$REVISION")"
[[ "$CHECKED_OUT_REVISION" == "$REQUESTED_REVISION"* || "$REQUESTED_REVISION" == "$CHECKED_OUT_REVISION"* ]] || { echo "checked_out_revision_does_not_match_requested_revision" >&2; exit 1; }

if [[ "$EXECUTE" != true ]]; then
  echo "Plan only. No Cloud Run, Firestore, Scheduler, or billing-affecting action will occur without --execute."
  printf 'Project: %s\nCloud Run region: %s\nGemini model location: %s\nWorker: %s\nPublic demo: %s\nService account: %s\nScheduler identity: %s\nPinned revision: %s\nSources: %s\n' \
    "$PROJECT_ID" "$REGION" "$MODEL_LOCATION" "$WORKER_SERVICE" "$DEMO_SERVICE" "$SERVICE_ACCOUNT" "$SCHEDULER_SERVICE_ACCOUNT" "$CHECKED_OUT_REVISION" "$SOURCES_FILE"
  python3 - <<'PY' "$SOURCES_JSON"
import json, sys
for source in json.loads(sys.argv[1]):
    print(f"Source schedule: {source['source_id']} -> {source['refresh_schedule']}")
PY
  if [[ "$GEMINI_BRIEFS" == true ]]; then
    echo "Worker: Firestore + configured HTTPS sources + bounded Gemini briefs."
  else
    echo "Worker: Firestore + configured HTTPS sources + deterministic briefs; Gemini remains disabled."
  fi
  if [[ -n "$RESEND_SECRET" ]]; then
    printf 'Owner brief: Resend secret %s will be bound to allowlisted recipient %s.\n' "$RESEND_SECRET" "$BRIEF_TO"
    if [[ "$INTERNAL_DELIVERY_PROBE_ENABLED" == true ]]; then
      echo "Owner delivery probe: enabled on the private worker for one controlled mailbox verification."
    else
      echo "Owner delivery probe: disabled."
    fi
  else
    echo "Owner brief: disabled."
  fi
  echo "Demo: public, fixture-only, and unable to receive registry-worker events."
  exit 0
fi

command -v gcloud >/dev/null || { echo "gcloud_cli_required" >&2; exit 1; }
gcloud services enable run.googleapis.com cloudscheduler.googleapis.com firestore.googleapis.com aiplatform.googleapis.com secretmanager.googleapis.com --project "$PROJECT_ID"

if [[ -z "$(gcloud firestore databases list --project "$PROJECT_ID" --format='value(name)' | head -1)" ]]; then
  gcloud firestore databases create --project "$PROJECT_ID" --location "$REGION"
fi

PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
SCHEDULER_SERVICE_AGENT="service-${PROJECT_NUMBER}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"

BRIEF_GENERATOR="deterministic"
GEMINI_ENABLED="false"
if [[ "$GEMINI_BRIEFS" == true ]]; then
  BRIEF_GENERATOR="gemini"
  GEMINI_ENABLED="true"
fi
DELIVERY_KIND="disabled"
DELIVERY_ENABLED="false"
if [[ -n "$RESEND_SECRET" ]]; then
  DELIVERY_KIND="resend"
  DELIVERY_ENABLED="true"
  gcloud secrets describe "$RESEND_SECRET" --project "$PROJECT_ID" >/dev/null 2>&1 || {
    echo "resend_secret_not_found" >&2
    exit 1
  }
  if [[ -z "$(gcloud secrets versions list "$RESEND_SECRET" --project "$PROJECT_ID" --filter='state=ENABLED' --limit=1 --format='value(name)')" ]]; then
    echo "resend_secret_has_no_enabled_version" >&2
    exit 1
  fi
  gcloud secrets add-iam-policy-binding "$RESEND_SECRET" --project "$PROJECT_ID" --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor" >/dev/null
fi
WORKER_ENV="^|^GOOGLE_CLOUD_PROJECT=$PROJECT_ID|GOOGLE_CLOUD_LOCATION=$MODEL_LOCATION|GOOGLE_GENAI_USE_VERTEXAI=TRUE|VICE_CEO_REGISTRY_WATCH_MODE=configured|VICE_CEO_REGISTRY_WATCH_STORE=firestore|VICE_CEO_REGISTRY_SOURCES_JSON=$SOURCES_JSON|VICE_CEO_REGISTRY_BRIEF_GENERATOR=$BRIEF_GENERATOR|VICE_CEO_REGISTRY_GEMINI_ENABLED=$GEMINI_ENABLED|VICE_CEO_INTERNAL_BRIEF_DELIVERY=$DELIVERY_KIND|VICE_CEO_INTERNAL_RESEND_DELIVERY_ENABLED=$DELIVERY_ENABLED|VICE_CEO_INTERNAL_BRIEF_FROM=$BRIEF_FROM|VICE_CEO_INTERNAL_BRIEF_TO=$BRIEF_TO|VICE_CEO_INTERNAL_DELIVERY_PROBE_ENABLED=$INTERNAL_DELIVERY_PROBE_ENABLED|VICE_CEO_PROVIDER_CANARY_ENABLED=false"
if [[ -n "$RESEND_SECRET" ]]; then
  gcloud run deploy "$WORKER_SERVICE" --source "$RUNTIME_ROOT" --project "$PROJECT_ID" --region "$REGION" --service-account "$SERVICE_ACCOUNT" --no-allow-unauthenticated --set-env-vars "$WORKER_ENV" --set-secrets "VICE_CEO_INTERNAL_RESEND_API_KEY=${RESEND_SECRET}:latest" --labels "app=vice-ceo-registry-watch,revision=${CHECKED_OUT_REVISION:0:63}"
else
  gcloud run deploy "$WORKER_SERVICE" --source "$RUNTIME_ROOT" --project "$PROJECT_ID" --region "$REGION" --service-account "$SERVICE_ACCOUNT" --no-allow-unauthenticated --set-env-vars "$WORKER_ENV" --labels "app=vice-ceo-registry-watch,revision=${CHECKED_OUT_REVISION:0:63}"
fi
WORKER_URL="$(gcloud run services describe "$WORKER_SERVICE" --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)')"

gcloud run services add-iam-policy-binding "$WORKER_SERVICE" --project "$PROJECT_ID" --region "$REGION" --member="serviceAccount:$SCHEDULER_SERVICE_ACCOUNT" --role="roles/run.invoker"
gcloud iam service-accounts add-iam-policy-binding "$SCHEDULER_SERVICE_ACCOUNT" --project "$PROJECT_ID" --member="serviceAccount:$SCHEDULER_SERVICE_AGENT" --role="roles/iam.serviceAccountTokenCreator" >/dev/null

gcloud run deploy "$DEMO_SERVICE" --source "$RUNTIME_ROOT" --project "$PROJECT_ID" --region "$REGION" --service-account "$SERVICE_ACCOUNT" --allow-unauthenticated --set-env-vars "VICE_CEO_PUBLIC_DEMO_ONLY=true,VICE_CEO_REGISTRY_WATCH_MODE=fixture,VICE_CEO_PROVIDER_CANARY_ENABLED=false" --labels "app=vice-ceo-registry-watch-demo,revision=${CHECKED_OUT_REVISION:0:63}"
DEMO_URL="$(gcloud run services describe "$DEMO_SERVICE" --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)')"

SCHEDULER_JOBS=()
SOURCE_INDEX=0
while IFS=$'\t' read -r SOURCE_ID SOURCE_SCHEDULE; do
  if [[ "$SOURCE_INDEX" -eq 0 ]]; then
    # Retain the original job identity so its observed run history remains easy to find.
    SCHEDULER_JOB="vice-ceo-registry-watch-direct-daily"
  else
    SCHEDULER_JOB="vice-ceo-registry-watch-${SOURCE_ID//_/-}"
  fi
  SCHEDULER_PAYLOAD='{"source_id":"'"$SOURCE_ID"'","event_type":"registry.watch.requested","source":"vice_ceo_registry_watch","schema_version":"vice-ceo-registry-watch-event-v1"}'
  if gcloud scheduler jobs describe "$SCHEDULER_JOB" --project "$PROJECT_ID" --location "$REGION" >/dev/null 2>&1; then
    gcloud scheduler jobs update http "$SCHEDULER_JOB" --project "$PROJECT_ID" --location "$REGION" --schedule "$SOURCE_SCHEDULE" --time-zone "Etc/UTC" --uri="$WORKER_URL/scheduler/registry-watch" --http-method POST --update-headers="Content-Type=application/json" --message-body "$SCHEDULER_PAYLOAD" --oidc-service-account-email="$SCHEDULER_SERVICE_ACCOUNT" --oidc-token-audience="$WORKER_URL"
  else
    gcloud scheduler jobs create http "$SCHEDULER_JOB" --project "$PROJECT_ID" --location "$REGION" --schedule "$SOURCE_SCHEDULE" --time-zone "Etc/UTC" --uri="$WORKER_URL/scheduler/registry-watch" --http-method POST --headers="Content-Type=application/json" --message-body "$SCHEDULER_PAYLOAD" --oidc-service-account-email="$SCHEDULER_SERVICE_ACCOUNT" --oidc-token-audience="$WORKER_URL"
  fi
  SCHEDULER_JOBS+=("$SCHEDULER_JOB")
  SOURCE_INDEX=$((SOURCE_INDEX + 1))
done < <(python3 - <<'PY' "$SOURCES_JSON"
import json, sys
for source in json.loads(sys.argv[1]):
    print(f"{source['source_id']}\t{source['refresh_schedule']}")
PY
)

printf 'Worker URL: %s\nPublic demo URL: %s\nScheduler jobs: %s\n' "$WORKER_URL" "$DEMO_URL" "${SCHEDULER_JOBS[*]}"
echo "Deployment created. Trigger one Scheduler run, verify the Firestore receipt and Cloud Logging, then prove one source-cited owner brief before treating delivery as ready."
