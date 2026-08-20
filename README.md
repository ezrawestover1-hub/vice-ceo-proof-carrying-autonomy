# Vice CEO Hackathon Runtime

This is the intentionally separate, least-privilege Google Cloud runtime for
the **Vice CEO: Proof-Carrying Business Autonomy** hackathon submission.

It is new hackathon source. Westover EPR remains the authoritative system for
customer, billing, outreach, support, and compliance records. This runtime
only uses synthetic fixtures in Sprint 1 and has no credentials or connector
for Resend, Stripe, Supabase service role, email delivery, refunds, billing
changes, or customer-record mutation.

## Public submission package

This directory is designed to be released as its **own public repository** for
the hackathon. It is intentionally separate from the private Westover EPR
application. The standalone package includes:

- [MIT License](LICENSE), applying to this runtime when published separately;
- [architecture diagram](ARCHITECTURE.png) for Devpost, with the editable
  [SVG source](ARCHITECTURE.svg); and
- [public-release checklist](PUBLIC_REPOSITORY_CHECKLIST.md), which lists the
  allowed source set and explicitly excludes parent-repository material,
  credentials, customer data, and deployment configuration.
- [judge packet](JUDGE_PACKET.md), which collects the evidence-backed project
  story, video plan, and explicit pre-submission gaps without claiming a live
  deployment.

The runtime remains synthetic-only even when published. It must not be
presented as a deployed Westover EPR service or as proof of real provider,
customer, financial, messaging, or administrative actions.

## Sprint 1 through 19 capability

- Google ADK root agent locked to the documented, stable
  `gemini-3.5-flash` Gemini target for this submission runtime.
- Cloud Run-ready health service.
- A synthetic-event endpoint that accepts only named demo fixtures.
- Strict Pub/Sub-shaped event decoding, event hashes, case-file records, and
  in-memory duplicate protection for synthetic replay.
- A deterministic policy simulation that can only allow simulated preparation.
- A read-only synthetic-case tool available to the ADK agent.
- A server-owned Action Warrant gateway for the one registered simulated tool.
- One-use, signed, short-lived warrant checks and global/capability stops.
- A tenant-scoped idempotency-store contract with an explicit Firestore adapter.
- A four-role Google ADK specialist fleet with redacted, route-validated handoffs.
- A callable synthetic-support loop that emits redacted, zero-effect outcome receipts.
- A deterministic Operational Twin that compares only registered synthetic options.
- An evidence-bound Trust Engine that can earn only simulation-only status.
- A read-only Business Time Machine that replays supplied synthetic evidence.
- Versioned, role-scoped approved knowledge references for synthetic playbooks.
- An offline adversarial safety suite for ingress, warrants, role scope, kill-switch races,
  and attempted production self-authorization.
- A versioned synthetic evaluation suite covering support, outreach, refunds, escalation,
  privacy, knowledge access, and tool authorization.
- A five-act, replayable judge-demo route at `/demo/judge-flow`.
- A source-backed submission-evidence route at `/demo/submission-evidence` and
  a reviewer-ready demo kit.
- Fixed recording fixtures and an offline one-command verification report.
- A release-readiness report that distinguishes local verification from commit,
  deployment, and provider evidence.
- A polished, dependency-free visual demo console at `/demo`.
- An explicit reviewer decision gate that can only approve or decline the fixed
  synthetic support simulation; it verifies no identity and grants no real-world authority.
- In-process HTTP smoke coverage for the health, demo, evidence, readiness,
  and synthetic-ingress routes.
- A closed source-artifact integrity manifest at `/demo/artifact-integrity`.
- An opt-in, fixed-prompt Vertex canary at `/demo/provider-canary`, disabled by
  default and isolated from all customer context and tools.
- No production data or external business effects.

## Provider canary boundary

`GET /demo/provider-canary` discloses the fixed-prompt canary status without
calling Gemini. `POST /demo/provider-canary` accepts no caller-provided prompt
and remains denied unless `VICE_CEO_PROVIDER_CANARY_ENABLED=true` is explicitly
set for the deployed revision. It uses an isolated no-tool ADK agent and marks
the in-memory canary terminal after either a provider result or provider error;
there is no automatic retry. A successful canary is provider connectivity
evidence only, not authority to use Westover EPR data or tools.

Each claimed provider attempt writes one structured Cloud Run receipt to
standard output. Cloud Logging retains it according to the project's configured
retention policy. The receipt carries only hashes, the model identifier, bounded
counts, safe reason codes, and no raw prompt or model response. Query it with:

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND jsonPayload.event="vice_ceo_provider_canary_receipt"' \
  --project=YOUR_PROJECT_ID --limit=10
```

To verify one exported receipt offline without querying Google Cloud or calling
Gemini again, save a single Cloud Logging JSON entry locally and run:

```bash
python -m app.provider_evidence_cli receipt.json --pretty
```

The verifier rejects unexpected fields, a different model or prompt hash,
missing timestamps, raw-output fields, nonzero tool calls, customer data, and
any claimed business effect. A verified receipt is connectivity evidence only;
it never grants production authority.

The private demo exposes the same no-fetch/no-call check at
`POST /demo/provider-evidence`. Submit one exported Cloud Logging entry as the
request body; it returns only the bounded evidence projection or a stable
rejection reason. This route neither reads Cloud Logging nor contacts Gemini.

`GET /demo/capability-boundaries` supplies the matching read-only capability
ledger used by the visual demo. It explicitly records that no messaging,
billing, customer-record, or administrative executor is present in this
hackathon runtime.

For a single reviewer packet, use `GET /demo/proof-bundle`. It cross-links the
five-act walkthrough, local evaluation report, capability ledger, and closed
source-manifest hash without starting an agent, calling Gemini, or fetching a
provider log.

`GET /demo/action-warrant-dossier` gives reviewers the redacted, signed
one-use warrant trail behind the simulation. It reports only hashes and
bounded metadata; its second-use result is a deterministic denial.

`GET /demo/time-machine-dossier` exposes the corresponding read-only replay
timeline and registered alternatives. It does not predict a real-world
business outcome or rerun a provider.

For the judge video, `GET /demo/recording-packet` (or
`python -m app.demo_cli --recording-packet --pretty`) renders a fixed
110-second narration and endpoint sequence. It is intentionally based on the
same local proof surfaces, needs no customer data, and does not call Gemini.

`GET /demo/agent-topology` makes the Google ADK architecture inspectable: only
Support Intake has the synthetic read capability, every specialist has zero
direct business tools, and the deterministic gateway sits outside the fleet.

`GET /demo/model-configuration` records the locked `gemini-3.5-flash` target
and explicitly distinguishes local configuration from a provider call or Cloud
Run deployment. Unsupported `VICE_CEO_GEMINI_MODEL` overrides fail during
startup instead of silently weakening the submission's model requirement.

`GET /demo/cloud-run-preflight` and `python -m app.cloud_run_preflight --pretty`
check the local container, manifest, model, proof, authority, connector, and
deployment-script boundaries. They do not invoke `gcloud`, select a project,
or create a cloud resource.

The agent can read the named synthetic fixture, but cannot prepare a transition
or issue/consume an Action Warrant. The deterministic gateway can prepare a
simulation only after it validates a warrant. Both duplicate claims and warrant
claims default to local memory. Firestore storage is available only when a
future Cloud Run deployment explicitly configures `VICE_CEO_CLAIM_STORE=firestore`.

The specialist fleet is deliberately asymmetric: Support Intake can read the
synthetic case; Policy Guard, Owner Escalation, and the router have no tools.
No specialist can issue or consume a warrant, so every simulated action still
passes through the deterministic gateway.

The support loop is a demo function, not a scheduler or background worker. Its
outcome receipt explicitly records that no external effect occurred and that no
real business outcome was measured.

The Operational Twin compares a synthetic `triaged` path with a synthetic
`resolution_prepared` path. It does not predict revenue, churn, satisfaction,
or compliance, and its recommendation still requires a separate Action Warrant
before even a simulation can occur.

The Trust Engine treats receipts as evidence—not proof of broad intelligence.
It caps authorization at `simulation_only`, cannot enable production, and
suspends trust when a receipt claims an unexpected write or external effect.

The Business Time Machine lets a reviewer inspect the event-to-receipt chain
and see why a registered alternative was selected, not selected, or unavailable.
It never reruns the workflow or causes a new effect.

Knowledge packs are retrieved by exact ID and version and only by their
authorized specialist. They are synthetic demo playbooks, not legal or
regulatory sources, and cannot authorize a business action.

The adversarial suite is an offline deterministic check. It records stable
reason codes only, retains none of the hostile input, and proves no production
authority or external effect.

The evaluation suite scores registered synthetic cases only. Its score is an
auditable control-plane regression signal, not a claim that the runtime has
been tested against real customer, financial, provider, or regulatory data.

The judge-demo route composes the synthetic evidence into a reviewer-friendly
story. It is read-only and always reports that external actions are disabled.

The submission-evidence route exposes exact component versions and reviewer
claims. It deliberately distinguishes source-backed implementation from any
unverified live deployment or production outcome.

For a recording-ready local summary, run `python -m app.demo_cli --pretty`
from this runtime directory. It composes fixtures and proof records only; it
does not start an agent, a server, or any connector.

`/demo/release-readiness` is similarly read-only. It can say the checked source
is ready for a user-reviewed commit, but never claims that source is pushed,
deployed, provider-connected, or production-authorized.

For a reviewer-friendly entry point, open `/demo`. It renders the same fixed
synthetic evidence as the structured demo routes without client analytics,
external assets, or an action control.

After installing runtime dependencies, run `python -m unittest tests.test_http_routes`
to exercise each demo route in process. This does not start a listener or call
a remote service.

`/demo/artifact-integrity` hashes only the checked local source set behind the
demo. It is useful review evidence, but does not establish a remote build or
deployment attestation.

## Local prerequisites

- Python 3.11 or newer
- `uv` or `pip`

## Offline reviewer path

The reviewer demo is intentionally credential-free. It does not need Google
Cloud application-default credentials, a Gemini invocation, an ADK agent run,
or a running HTTP server. From this directory, run:

```powershell
uv sync --locked --extra dev
uv run python -m unittest discover -s tests -v
uv run python -m app.demo_cli --recording-packet --pretty
uv run python -m app.demo_cli --pretty
uv run python -m app.demo_cli --proof-verification --pretty
```

The recording packet is the fixed 110-second reviewer sequence. The standard
demo report returns `all_verified: true` only when the judge flow, adversarial
suite, evaluation suite, and source-backed evidence manifest agree. The proof
verification report cross-checks the linked local artifacts. Each command
uses only closed synthetic fixtures and reports zero external effect and no
production authority.

## Optional Vertex connectivity path

Google Cloud application-default credentials are needed only for a separately
authorized Vertex AI connectivity check. That check is not part of the
offline reviewer path, does not prove production authority, and must not be
run against Westover EPR customer data.

Set the following only in a local `.env` file or Cloud Run configuration. Do
not commit credentials.

```text
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-east1
GOOGLE_GENAI_USE_VERTEXAI=TRUE
VICE_CEO_GEMINI_MODEL=gemini-3.5-flash
# Keep this unset or set it to in_memory for local tests.
VICE_CEO_CLAIM_STORE=in_memory
```

## Deployment boundary

The provided Dockerfile is a Cloud Run container boundary, not a deployment.
Do not deploy, attach Pub/Sub, grant service-account access, or enable any
production connector until later sprints have wired the Firestore adapter,
outcome receipts, and a separately approved deployment plan.

## Guarded Cloud Run handoff

`scripts/deploy-cloud-run.ps1` prints a plan by default. It requires an
explicit `-Execute` switch plus a project, region, service, and service-account
identifier plus the pinned Git revision before it calls Cloud Run. The handoff stays synthetic-only and uses
in-memory claims; it attaches no outbound business connector. See
`docs/AI_VICE_CEO_HACKATHON_SPRINT_20_CLOUD_RUN_HANDOFF.md` before use.
Cloud Shell users can use the equivalent `scripts/deploy-cloud-run.sh` and
`scripts/verify-cloud-run.sh` scripts with the same plan-first boundaries.

For a private deployment, use `gcloud run services proxy` and verify
`/demo/judge-flow` through `scripts/verify-cloud-run.ps1`. That route is the
authoritative runtime smoke check: it must show synthetic-only execution with
no external effect. `/healthz` remains a supplemental diagnostic because a
private Cloud Run front door can reject that direct path before it reaches the
container.
