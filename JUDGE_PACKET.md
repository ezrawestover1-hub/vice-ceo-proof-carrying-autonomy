# Vice CEO — Judge Packet (Working Draft)

**Status:** Local preparation only. This file is not a Devpost project, and it
does not claim that a Cloud Run deployment or a Gemini provider invocation has
occurred.

## Submission positioning

**Title**
Vice CEO: Proof-Carrying Business Autonomy

**One-line summary**
An enterprise-style agentic workflow where every simulated business decision is
bound to inspectable evidence, a narrow one-use warrant, and a replayable
decision trail.

**Recommended category**
Fortified Enterprise Fleet — the code is structured as a four-role Google ADK
specialist fleet with a separate policy/warrant gateway, scoped knowledge
access, audit surfaces, and zero direct business-tool authority.

**Important fit caveat**
This is the strongest architectural match, not a claim that the current
synthetic-only demo connects to production data. Before final entry, show the
Cloud Run deployment proof required by the event and keep this limitation
plainly visible.

## Judge-facing description

Most business agents make a recommendation and leave people to trust a black
box. Vice CEO treats the proof of a decision as part of the decision itself.

The project routes a named synthetic support case through a small Google ADK
specialist fleet. Support Intake can read the bounded fixture; Policy Guard,
Owner Escalation, and the router have no direct business tools. A separate,
server-owned Action Warrant gateway is the only route to the demo transition.
It accepts a signed, short-lived, role-scoped warrant once, then refuses a
replay, a tampered warrant, changed control state, or an unknown input.

The result is not just a generated answer. A reviewer can inspect the evidence
chain, see the rejected alternative, replay the supplied decision record
without rerunning the workflow, verify a closed source-artifact manifest, and
run the adversarial/evaluation suites. The Trust Engine never rises above
`simulation_only`; external effects, customer data, persistent writes, and
production authority remain disabled.

Vice CEO is deliberately honest about its current boundary: it is a local,
synthetic, zero-effect reference runtime. Its value is a production-minded
control plane for future enterprise agents—not a false claim of autonomous
customer, billing, messaging, or administrative actions.

## Why it matters

High-value business work demands more than a fluent model response. Operators
need to know which evidence supported a decision, what authority was granted,
which alternative was considered, and whether a claimed action can be replayed
and audited. Vice CEO demonstrates a compact pattern for making those answers
inspectable before an agent is permitted to progress.

## How AI is used

- Google ADK defines a four-role specialist topology around the locked
  `gemini-3.5-flash` model target.
- Specialists have asymmetric capability: only Support Intake can inspect the
  named synthetic case; none can issue or consume a warrant or perform a
  business action.
- The provider canary is opt-in, accepts no caller-provided prompt, makes zero
  tool calls, logs a hash-only receipt, and does not expand authority even if
  connectivity succeeds.
- The local judge flow remains deterministic and provider-free so every
  reviewed result can be reproduced without customer data or hidden calls.

## Google stack and implementation evidence

| Requirement | Evidence in this repository | Honest current state |
| --- | --- | --- |
| Gemini 3.5+ | `app/model_configuration.py` locks `gemini-3.5-flash`; `app/specialist_agents.py` configures Google ADK Gemini agents. | Configured in source; no provider call verified yet. |
| Google agent framework | `google-adk` is a runtime dependency; `app/agent.py` and `app/specialist_agents.py` define the ADK app/fleet. | Implemented and locally tested around the bounded demo. |
| Google Cloud service | FastAPI container boundary, Dockerfile, and guarded Cloud Run scripts. | Cloud Run-ready, **not yet deployed or proven**. |
| Enterprise safety | Separate warrant gateway, role scoping, kill switch, evidence ledger, adversarial suite, and evaluation suite. | Locally verified against synthetic fixtures only. |

## Key features that work locally

1. **Evidence-bound recommendation** — the fixed synthetic case carries an
   event hash, redacted case record, policy result, and zero-effect receipt.
2. **One-use Action Warrant** — the first authorized simulation is accepted;
   the second use is deterministically denied.
3. **Inspectable alternatives** — the Business Time Machine replays supplied
   evidence and exposes registered alternatives without rerunning an agent.
4. **Fail-closed governance** — unknown fixtures, extra input, invalid routes,
   stale warrants, tampering, and changed controls are denied.
5. **Reviewable proof bundle** — a single bundle links the walkthrough,
   evaluation report, capability ledger, and closed source-manifest hash.
6. **Safety regression coverage** — 56 automated tests cover ingress,
   authority, evidence integrity, evaluator behavior, and visual/demo routes.

## Architecture

![Architecture diagram](ARCHITECTURE.png)

The system receives a bounded synthetic event, validates it, and routes the
case through role-limited ADK specialists. The decision can reach only the
deterministic Action Warrant gateway, which produces a simulated receipt. The
receipt, counterfactuals, proof bundle, and safety/evaluation results remain
read-only review surfaces. A global kill switch or role-scope mismatch blocks
the warrant before the simulation.

Editable source: [ARCHITECTURE.svg](ARCHITECTURE.svg).

## Reproducible testing

Prerequisites: Python 3.11+ and `uv`.

```bash
uv sync --locked --extra dev
uv run python -m unittest discover -s tests -v
uv run python -m app.demo_cli --recording-packet --pretty
uv run python -m app.demo_cli --proof-verification --pretty
```

The latest local verification run passed all **56 tests** and reported
`all_checks_passed: true`. These commands use closed synthetic fixtures only;
they do not start a server, contact a provider, access customer records, or
perform an external action.

## Reviewer route map

| Surface | What it proves | What it does not prove |
| --- | --- | --- |
| `/demo` | A readable, zero-effect walkthrough of the fixed synthetic flow. | A provider call or business action. |
| `/demo/action-warrant-dossier` | Scoped warrant and deterministic second-use denial. | Broad authorization. |
| `/demo/time-machine-dossier` | Evidence replay and registered alternatives. | Real-world outcome prediction. |
| `/demo/proof-bundle` | Linked evaluation, capability, and artifact-integrity evidence. | A remote deployment attestation. |
| `/demo/provider-evidence` | Offline verification of a supplied hash-only canary receipt. | It does not call a provider itself. |
| `/demo/cloud-run-preflight` | Local container and release-input readiness. | That Cloud Run has been deployed. |

## Four-minute video plan

1. **0:00–0:25 — Problem.** Business agents can move quickly, but operators
   often cannot inspect why an action was allowed or replay the decision.
2. **0:25–0:55 — Promise.** Introduce proof-carrying autonomy and the
   synthetic-only boundary: no customer data, no external effects, no
   production authority.
3. **0:55–1:45 — Workflow demo.** Open `/demo`; follow the named fixture from
   validation through specialist routing to the simulated receipt.
4. **1:45–2:25 — Authority demo.** Open the Action Warrant dossier; show that
   it is scoped, short-lived, one-use, and fails closed on its second use.
5. **2:25–2:55 — Replay demo.** Open the Business Time Machine dossier and
   show the selected and rejected alternatives without a re-run.
6. **2:55–3:25 — Proof demo.** Show the proof bundle, local verification
   report, and source-manifest link; state the 56 passing tests.
7. **3:25–3:45 — Cloud proof.** **Pending before recording:** show the real
   Cloud Run service/revision and a health response or equivalent Google Cloud
   Console evidence. Do not narrate this section until it is actually deployed.
8. **3:45–4:00 — Close.** State the value proposition: capable workflows earn
   trust through bounded authority and inspectable proof.

## Required Devpost fields — preparation checklist

- [x] Public repository: <https://github.com/ezrawestover1-hub/vice-ceo-proof-carrying-autonomy>
- [x] Reproducible local testing instructions in `README.md`
- [x] Architecture diagram: `ARCHITECTURE.png` (upload directly to Devpost)
- [x] Google SDK answer: **Agent Development Kit (ADK)**
- [x] Google AI models answer: **Gemini 3.5 Flash**
- [ ] Select **Individuals**, **Team of individuals**, or **Organization**
- [ ] Supply the submitter's country of residence
- [ ] Supply the truthful project-start date (MM-DD-YY)
- [ ] Confirm the category selection in the live form
- [ ] Deploy the bounded container to Cloud Run and capture real deployment
  evidence for the video; no deployment should be claimed before then
- [ ] Record and host the approximately four-minute demo video
- [ ] Capture 3–5 clean screenshots of the running local reviewer flow
- [ ] Decide whether to publish optional build-story/social bonus content

## Links for the future form

- **Public repository:** https://github.com/ezrawestover1-hub/vice-ceo-proof-carrying-autonomy
- **Hosted project:** _Not available — intentionally leave blank until a real
  deployment exists._
- **Demo video:** _Not recorded yet._
- **Architecture upload:** `ARCHITECTURE.png`

## How Codex was used

Codex helped recover and separate the hackathon runtime from the private
Westover EPR application, refine the reviewer interface, implement and verify
the proof-carrying workflow, run the automated test suite, create the public
repository package and architecture asset, and assemble this honest
judge-facing packet. The project itself remains the evidence: no claim of an
external action or deployment is substituted for local proof.

## Known limitations

- The current runtime processes named synthetic fixtures only.
- It has no customer-data connector, billing/messaging executor, background
  scheduler, or real business authority.
- The Cloud Run configuration is deployment-ready but has not been deployed or
  independently verified in Google Cloud.
- The optional Gemini provider canary is disabled by default and has not been
  used as evidence in the local demo.
- The Devpost project page, final personal form fields, screenshots, and video
  remain intentionally uncreated or unfilled.
