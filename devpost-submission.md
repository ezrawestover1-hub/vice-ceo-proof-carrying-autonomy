# Vice CEO: Proof-Carrying Business Autonomy

## One-line Summary

Vice CEO is a behind-the-scenes business operator that prepares routine customer communication and approved follow-through, carries the evidence behind every decision, and brings a person in only when judgment is actually needed.

## Problem

Small business teams lose time to work that is individually simple but collectively relentless: support questions, sales follow-ups, policy lookups, changing public program information, and the handoff between an alert and the next useful action. Typical AI tools can generate a reply, but they leave the business to reconstruct why it acted, whether it had authority, and what happened afterward.

## Solution

Vice CEO turns a bounded business signal into prepared, inspectable work. It connects the source, applicable policy, proposed action, authority boundary, and delivery state in one replayable receipt. Routine customer-service responses and consent-aware outreach follow-ups are prepared in the background; exceptions such as a refund request return as a focused human decision.

Westover EPR is the example deployment. Its private Registry Change Watch observes an approved public-source portfolio, preserves hash-linked evidence in Firestore, detects material changes, and prepares an owner-facing operational brief. The public reviewer app uses closed synthetic fixtures so judges can inspect the entire workflow without customer data or external business effects.

## Why This Matters

Autonomy is useful only when a business can understand and control it. Vice CEO removes repetitive coordination work while making each step inspectable: what triggered it, what policy applied, which authority was granted, what alternative was rejected, and whether anything was delivered. That lets a business begin with preparation, review the evidence, and expand authority only for the workflows it explicitly approves.

## How We Used AI

- A four-role Google Agent Development Kit specialist fleet is configured around the locked `gemini-3.5-flash` target.
- The specialists are capability-limited: Support Intake can read only a named synthetic case; the policy, escalation, and routing roles have no direct business-action tools.
- A separately deployed, fixed-prompt Vertex/Gemini connectivity canary produced a hash-only Cloud Logging receipt with no customer data, tool calls, persistent business writes, or external business effect.
- The private Registry Change Watch uses bounded Gemini briefs only after an approved public source materially changes. The local judge flow stays deterministic and provider-free so it is reproducible.

## How We Used Codex

Codex helped separate the hackathon runtime from the private Westover EPR application, implement and test the bounded workflow, refine the reviewer interface and demo, verify the evidence boundaries, and assemble the submission materials. The result explicitly distinguishes local synthetic proof, deployed infrastructure evidence, provider connectivity evidence, and real business authority instead of treating them as interchangeable.

## Key Features

1. **Prepared customer work** — policy-linked customer-service replies and consent-aware outreach follow-ups, each with a zero-effect public-demo receipt.
2. **Human judgment escalation** — exceptions are surfaced with the relevant evidence instead of being silently actioned.
3. **Proof-carrying decisions** — source, policy, decision, authority, and delivery state stay linked and inspectable.
4. **One-use Action Warrant** — a signed, short-lived, role-scoped warrant authorizes one synthetic transition and deterministically rejects a replay or tampering attempt.
5. **Background Registry Change Watch** — a private Cloud Scheduler and Cloud Run worker monitors an approved public EPR source portfolio, deduplicates runs, and stores hash-linked Firestore evidence.
6. **Fail-closed controls** — unknown inputs, stale or replayed warrants, scope violations, changed controls, and untrusted source content are rejected or escalated.
7. **Reproducible reviewer proof** — a public synthetic walkthrough, proof bundle, evidence replay, and automated adversarial/evaluation checks let reviewers inspect the implementation without credentials.

## Architecture

The public Cloud Run reviewer receives only a named synthetic event and routes it through role-limited ADK specialists. The separate private operational worker accepts only Cloud Scheduler OIDC calls, watches an approved public source allowlist, stores content fingerprints and run state in Firestore, and prepares a bounded owner-review brief only on material change. A server-owned Action Warrant gateway sits outside the specialist fleet; no specialist can grant itself authority or directly send business communication.

![Vice CEO architecture](ARCHITECTURE.png)

Upload [`ARCHITECTURE.png`](ARCHITECTURE.png) to the Devpost Architecture Diagram field. The editable source is [`ARCHITECTURE.svg`](ARCHITECTURE.svg).

## Testing Instructions

Prerequisites: Python 3.11+ and `uv`.

```bash
uv sync --locked --extra dev
uv run python -m unittest discover -s tests -v
uv run python -m app.demo_cli --recording-packet --pretty
uv run python -m app.demo_cli --proof-verification --pretty
```

The checks use closed synthetic fixtures only. They do not call a provider, start a listener, access customer records, or perform an external business action. The latest verified local run passed 86 automated tests.

## Public Demo Link

https://vice-ceo-review-demo-77u4kmu2ba-uc.a.run.app/demo

The hosted reviewer experience is intentionally synthetic-only. It demonstrates prepared work and evidence receipts but does not send customer or prospect messages.

## Public Repository Link

https://github.com/ezrawestover1-hub/vice-ceo-proof-carrying-autonomy

The repository is public and includes an MIT license, spin-up instructions, the architecture diagram, and a public-release checklist.

## Demo Video

**Final file ready to upload:** `artifacts/demo-video/ViceCEO-AllThingsAgentic-SubmissionCut-Final.mp4`

The 2:07, 1920×1080 showcase demonstrates the product flow, customer-work and outreach preparation, owner escalation, evidence receipts, authority boundaries, and the public Cloud Run URL. Upload it as a **public** YouTube or Vimeo video, then paste the resulting URL here and into Devpost.

## Screenshot Shot List

1. **Work queue:** prepared password-reset response alongside source policy and customer context.
2. **Outreach:** consent-aware follow-up with stop-on-reply/unsubscribe logic and a prepared receipt.
3. **Exception handoff:** refund request marked for human decision rather than automated handling.
4. **Proof:** action receipt/evidence view showing source, policy, decision, and delivery boundary.
5. **Google Cloud proof:** the public `.run.app` URL or Cloud Run dashboard alongside the running reviewer experience.

## Submission Readiness Notes

- [x] Registered for All Things Agentic Hackathon.
- [x] Draft positioning: **Fortified Enterprise Fleet**.
- [x] Public repository link and MIT license.
- [x] Reproducible README/testing instructions.
- [x] Architecture diagram ready for direct upload.
- [x] Hosted Cloud Run reviewer URL.
- [x] Final narrated 1080p demo-video file prepared locally.
- [ ] Host the final video publicly on YouTube or Vimeo and paste the URL.
- [ ] Capture and upload 3–5 screenshots from the working reviewer experience.
- [ ] Create the Devpost project and paste this description.
- [ ] Complete the personal and project-start fields below truthfully.
- [ ] Open the repo, hosted demo, and video in a logged-out browser before submitting.

## Known Limitations

- The public reviewer runs named synthetic fixtures only; its receipts explicitly record zero external effect.
- The private Registry Change Watch reads approved public sources and writes only its own Firestore evidence state. It has no customer-record, billing, prospect-messaging, or legal-decision authority.
- Gemini connectivity is proven only by a narrow no-tool canary. No material public-source change has yet produced a live Gemini registry brief.
- The project contains a separately configured business-email adapter, but the public demo never sends customer or prospect email.

## TODO Official Form Fields

Use these answers only where they are personally and factually accurate:

| Devpost field | Prepared answer / action |
| --- | --- |
| Submitter Type | **Individuals** (confirm this is how you are entering). |
| Submitter country of residence | **United States** (confirm before saving). |
| Category | **Fortified Enterprise Fleet**. |
| Organization name | Leave blank/not applicable if entering as an individual. Do not opt into Startup Excellence unless Westover is incorporated and you have authority to enter for it. |
| Project start date | `08-18-26` **only if that is the truthful project start date**. |
| Code repo | `https://github.com/ezrawestover1-hub/vice-ceo-proof-carrying-autonomy` |
| Reproducible testing instructions | **Yes**. |
| Hosted project URL | `https://vice-ceo-review-demo-77u4kmu2ba-uc.a.run.app/demo` |
| Google SDK | **Agent Development Kit (ADK)**. |
| Google Cloud services | **Cloud Run** and **Firestore**. |
| Architecture diagram | Upload `ARCHITECTURE.png`; do not put this answer in a text field. |
| Google AI models | **Gemini 3.5 Flash**. |
| Video | Paste the public YouTube/Vimeo URL after upload. |
| Optional bonus content/social | Leave blank unless a qualifying public build story or social post exists. |

