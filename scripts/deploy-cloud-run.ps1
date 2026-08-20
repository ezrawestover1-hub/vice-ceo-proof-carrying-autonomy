[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern("^[a-z][a-z0-9-]{4,62}$")]
  [string]$ProjectId,

  [Parameter(Mandatory = $true)]
  [ValidatePattern("^[a-z]+-[a-z0-9]+[0-9]$")]
  [string]$Region,

  [Parameter(Mandatory = $true)]
  [ValidatePattern("^[a-z]([-a-z0-9]*[a-z0-9])?$")]
  [string]$ServiceName,

  [Parameter(Mandatory = $true)]
  [ValidatePattern("^[^@\s]+@[^@\s]+\.iam\.gserviceaccount\.com$")]
  [string]$ServiceAccount,

  [Parameter(Mandatory = $true)]
  [ValidatePattern("^[0-9a-fA-F]{7,40}$")]
  [string]$Revision,

  [switch]$Execute
)

$ErrorActionPreference = "Stop"
$runtimeRoot = Split-Path -Parent $PSScriptRoot

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  throw "git_cli_required_for_revision_pinning"
}

Push-Location $runtimeRoot
try {
  $checkedOutRevision = (git rev-parse --short=40 HEAD).Trim().ToLowerInvariant()
} finally {
  Pop-Location
}
$expectedRevision = $Revision.Trim().ToLowerInvariant()
if (-not ($checkedOutRevision.StartsWith($expectedRevision) -or $expectedRevision.StartsWith($checkedOutRevision))) {
  throw "checked_out_revision_does_not_match_requested_revision"
}

if (-not $Execute) {
  Write-Host "Plan only. No Cloud Run deployment will occur without -Execute."
  Write-Host "Project: $ProjectId"
  Write-Host "Region: $Region"
  Write-Host "Service: $ServiceName"
  Write-Host "Service account: $ServiceAccount"
  Write-Host "Pinned revision: $checkedOutRevision"
  Write-Host "Runtime: synthetic-only, in-memory claims, no connector flags."
  exit 0
}

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
  throw "gcloud_cli_required"
}

Push-Location $runtimeRoot
try {
  gcloud run deploy $ServiceName `
    --source . `
    --project $ProjectId `
    --region $Region `
    --service-account $ServiceAccount `
    --no-allow-unauthenticated `
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$ProjectId,GOOGLE_CLOUD_LOCATION=$Region,GOOGLE_GENAI_USE_VERTEXAI=TRUE,VICE_CEO_CLAIM_STORE=in_memory,VICE_CEO_PROVIDER_CANARY_ENABLED=false" `
    --labels "app=vice-ceo-hackathon-runtime,runtime=synthetic-only,revision=$checkedOutRevision"
  if ($LASTEXITCODE -ne 0) {
    throw "cloud_run_deploy_failed"
  }
} finally {
  Pop-Location
}

$readyRevision = (gcloud run services describe $ServiceName --project $ProjectId --region $Region --format="value(status.latestReadyRevisionName)").Trim()
if (-not $readyRevision) {
  throw "cloud_run_ready_revision_unavailable"
}

Write-Host "Deployment command completed. Ready Cloud Run revision: $readyRevision"
Write-Host "Verify through an authenticated local proxy before any public-access decision."
