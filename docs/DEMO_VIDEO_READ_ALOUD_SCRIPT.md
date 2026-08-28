# Vice CEO — Read-Aloud Demo Script

**Target run time:** about four minutes, including the brief pauses between sections. Read the words aloud; use bracketed directions only as on-screen cues.

## 0:00–0:25 — Problem

**[Show the hosted reviewer home page.]**

Businesses receive operational signals all day: a regulatory change, a support escalation, a supplier update, or a policy exception. The hard part is not getting another alert. It is knowing what changed, whether it matters, and whether the evidence deserves an operator’s attention.

Vice CEO is a proof-carrying business autonomy system built for that gap. It works in the background, but it never asks a user to blindly trust its recommendation.

## 0:25–0:50 — Product promise

**[Point to the recommendation, evidence rail, and reviewer decision tray.]**

This is the hosted reviewer experience. Before a recommendation can move forward, its evidence, reasoning trail, authority limits, and replay path are available in one place.

The public interface uses named synthetic fixtures, so the entire workflow can be inspected safely. The key idea is simple: the agent must earn the right to progress.

## 0:50–1:35 — Live autonomy

**[Show the live Google Cloud card or Cloud Run and Scheduler proof.]**

This is the reusable operating pattern: a business signal becomes bounded evidence, specialists advise, a scoped warrant gates the next step, and a reviewer can replay the result. The synthetic support escalation on this screen makes that pattern safe to inspect end to end.

Westover EPR is the first live deployment example. Its Registry Change Watch monitors three approved public sources: Oregon, California, and Maryland.

Private Cloud Scheduler jobs use OIDC to invoke a private Cloud Run worker. That worker normalizes visible public content, fingerprints it, and saves source snapshots, event claims, run receipts, and owner-review candidates in Firestore.

This is the deployed worker revision, serving one hundred percent of traffic. The Cloud Run endpoint, Scheduler jobs, and Firestore evidence state are part of the operating system—not a mocked background process.

When a source has not materially changed, Vice CEO stays quiet. When it does change, the system preserves the evidence needed to explain why it matters.

## 1:35–2:00 — Authority boundary

**[Show the portfolio, operations overview, or boundary card.]**

The private operations view exposes approved sources, evidence hashes, queue counts, and authority limits. This same product pattern can support compliance, operations, support, procurement, and other high-stakes business workflows. It does not expose customer records, billing tools, prospect contacts, or commercial action buttons.

One controlled owner-mailbox verification was accepted by the configured internal provider. That proves a bounded owner-brief path, not customer or prospect outreach. Those capabilities do not exist in this runtime.

## 2:00–2:25 — Gemini and ADK

**[Show the Gemini canary or controlled replay label.]**

Gemini 3.5 Flash and Google ADK are used in a narrow, inspectable role. After a material public-source change, they can create an internal brief from a bounded excerpt.

Before that happens, a deterministic prompt-injection gate checks the untrusted public text. If it sees instruction-like content or a credential extraction attempt, the model path stops and the system creates an evidence-linked owner-review fallback instead.

The canary and controlled replay demonstrate the real code path with no customer data, no Firestore write, and no external business effect.

## 2:25–3:10 — Reviewer flow

**[Open the proof bundle, Action Warrant, and replay record.]**

Each recommendation carries a proof bundle, a one-use Action Warrant, and a replay record. Specialists can advise, but they have no direct business tools.

The deterministic gateway consumes a short-lived, one-use warrant before the only registered transition: a synthetic simulation. That approval produces a readable receipt and nothing beyond it—no customer contact, persistence, or external effect.

## 3:10–3:40 — Resilience

**[Show a rejection, fallback, or the test result.]**

The system is designed to fail safely. Unregistered sources are rejected. A used warrant cannot be used again. Prompt injection is stopped before the model boundary. And the release has eighty-six automated tests covering authority, evidence integrity, adversarial probes, evaluation behavior, and the reviewer routes.

## 3:40–4:00 — Close

**[Show the architecture diagram, then return to the reviewer.]**

Vice CEO turns business signals into accountable executive attention. Westover EPR proves the first registry-monitoring deployment, but the product is the reusable system behind it: asynchronous work, evidence-led decisions, and clear authority boundaries.

That is proof-carrying autonomy: useful enough to work in the background, and disciplined enough to be trusted when it asks for attention.
