[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern("^https?://[^\s]+$")]
  [string]$ServiceUrl,

  [switch]$RequireHealthRoute
)

$ErrorActionPreference = "Stop"

$judge = Invoke-RestMethod -Uri "$ServiceUrl/demo/judge-flow" -TimeoutSec 15
if ($judge.demo.external_effect -ne $false -or $judge.synthetic_only -ne $true) {
  throw "cloud_run_judge_boundary_verification_failed"
}

$proofBundle = Invoke-RestMethod -Uri "$ServiceUrl/demo/proof-bundle" -TimeoutSec 15
$warrant = Invoke-RestMethod -Uri "$ServiceUrl/demo/action-warrant-dossier" -TimeoutSec 15
$timeMachine = Invoke-RestMethod -Uri "$ServiceUrl/demo/time-machine-dossier" -TimeoutSec 15
$recordingPacket = Invoke-RestMethod -Uri "$ServiceUrl/demo/recording-packet" -TimeoutSec 15
$topology = Invoke-RestMethod -Uri "$ServiceUrl/demo/agent-topology" -TimeoutSec 15

if (
  $proofBundle.proof_bundle.all_local_proof_checks_passed -ne $true -or
  $proofBundle.proof_bundle.production_authority -ne $false -or
  $warrant.action_warrant_dossier.first_use_state -ne "simulated" -or
  $warrant.action_warrant_dossier.second_use_reason_code -ne "action_warrant_already_consumed" -or
  $timeMachine.time_machine_dossier.replay_status -ne "replayed_from_supplied_synthetic_evidence" -or
  $recordingPacket.recording_packet.provider_call_required -ne $false -or
  $topology.agent_topology.direct_business_tool_count -ne 0
) {
  throw "cloud_run_hackathon_proof_verification_failed"
}

$healthStatus = $null
$healthVerification = "not_requested"
try {
  $health = Invoke-RestMethod -Uri "$ServiceUrl/healthz" -TimeoutSec 15
  if ($health.status -ne "ok" -or $health.synthetic_only -ne $true -or $health.external_actions_enabled -ne $false) {
    throw "cloud_run_health_boundary_verification_failed"
  }

  $healthStatus = $health.status
  $healthVerification = "passed"
} catch {
  if ($RequireHealthRoute) {
    throw "cloud_run_health_boundary_verification_failed"
  }

  # The judge flow is the authoritative app-level smoke check. Keep a
  # non-blocking health result visible because private Cloud Run front doors
  # can reject a direct /healthz probe before it reaches the container.
  $healthVerification = "unavailable_non_blocking"
}

[pscustomobject]@{
  service_url = $ServiceUrl
  health_status = $healthStatus
  health_verification = $healthVerification
  synthetic_only = $judge.synthetic_only
  external_actions_enabled = $judge.external_actions_enabled
  judge_demo_external_effect = $judge.demo.external_effect
  proof_bundle_verified = $proofBundle.proof_bundle.all_local_proof_checks_passed
  warrant_second_use_reason = $warrant.action_warrant_dossier.second_use_reason_code
  time_machine_replay_status = $timeMachine.time_machine_dossier.replay_status
  recording_packet_duration_seconds = $recordingPacket.recording_packet.target_duration_seconds
  direct_business_tool_count = $topology.agent_topology.direct_business_tool_count
  verification = "all_demo_proof_surfaces_passed"
} | ConvertTo-Json -Depth 4
