#!/usr/bin/env bash
# Read-only verifier for a locally proxied private Cloud Run demo service.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/verify-cloud-run.sh --service-url http://127.0.0.1:18080 [--require-health-route]
EOF
}

SERVICE_URL=""
REQUIRE_HEALTH=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --service-url) SERVICE_URL="${2:?service URL required}"; shift 2 ;;
    --require-health-route) REQUIRE_HEALTH=true; shift ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ "$SERVICE_URL" =~ ^https?://[^[:space:]]+$ ]] || { echo "invalid_service_url" >&2; exit 2; }
command -v curl >/dev/null || { echo "curl_required" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3_required" >&2; exit 1; }

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
for surface in judge-flow proof-bundle action-warrant-dossier time-machine-dossier recording-packet agent-topology; do
  curl --fail --silent --show-error "$SERVICE_URL/demo/$surface" >"$TMP_DIR/$surface.json"
done

HEALTH_VERIFICATION="unavailable_non_blocking"
HEALTH_STATUS=""
if curl --fail --silent --show-error "$SERVICE_URL/healthz" >"$TMP_DIR/healthz.json"; then
  read -r HEALTH_STATUS HEALTH_VERIFICATION < <(python3 - "$TMP_DIR/healthz.json" <<'PY'
import json, sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
if payload.get("status") != "ok" or payload.get("synthetic_only") is not True or payload.get("external_actions_enabled") is not False:
    raise SystemExit("cloud_run_health_boundary_verification_failed")
print("ok passed")
PY
)
elif [[ "$REQUIRE_HEALTH" == true ]]; then
  echo "cloud_run_health_boundary_verification_failed" >&2
  exit 1
fi

python3 - "$TMP_DIR" "$SERVICE_URL" "$HEALTH_STATUS" "$HEALTH_VERIFICATION" <<'PY'
import json, pathlib, sys

root = pathlib.Path(sys.argv[1])
payloads = {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in root.glob("*.json")}
judge = payloads["judge-flow"]
proof = payloads["proof-bundle"]
warrant = payloads["action-warrant-dossier"]
timeline = payloads["time-machine-dossier"]
packet = payloads["recording-packet"]
topology = payloads["agent-topology"]

valid = (
    judge.get("synthetic_only") is True
    and judge.get("external_actions_enabled") is False
    and judge["demo"].get("external_effect") is False
    and proof["proof_bundle"].get("all_local_proof_checks_passed") is True
    and proof["proof_bundle"].get("production_authority") is False
    and warrant["action_warrant_dossier"].get("first_use_state") == "simulated"
    and warrant["action_warrant_dossier"].get("second_use_reason_code") == "action_warrant_already_consumed"
    and timeline["time_machine_dossier"].get("replay_status") == "replayed_from_supplied_synthetic_evidence"
    and packet["recording_packet"].get("provider_call_required") is False
    and topology["agent_topology"].get("direct_business_tool_count") == 0
)
if not valid:
    raise SystemExit("cloud_run_hackathon_proof_verification_failed")

print(json.dumps({
    "service_url": sys.argv[2],
    "health_status": sys.argv[3] or None,
    "health_verification": sys.argv[4],
    "synthetic_only": judge["synthetic_only"],
    "external_actions_enabled": judge["external_actions_enabled"],
    "judge_demo_external_effect": judge["demo"]["external_effect"],
    "proof_bundle_verified": proof["proof_bundle"]["all_local_proof_checks_passed"],
    "warrant_second_use_reason": warrant["action_warrant_dossier"]["second_use_reason_code"],
    "time_machine_replay_status": timeline["time_machine_dossier"]["replay_status"],
    "recording_packet_duration_seconds": packet["recording_packet"]["target_duration_seconds"],
    "direct_business_tool_count": topology["agent_topology"]["direct_business_tool_count"],
    "verification": "all_demo_proof_surfaces_passed",
}, sort_keys=True))
PY
