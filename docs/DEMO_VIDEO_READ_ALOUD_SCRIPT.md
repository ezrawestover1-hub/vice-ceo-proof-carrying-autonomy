# Vice CEO — Read-Aloud Demo Script

**Run time:** about four minutes at a calm, conversational pace.

**How to use it:** read the words aloud. Follow the bracketed screen cues, but do not read the brackets. Pause briefly after each bold heading.

## 0:00–0:25 — Open with the problem

**[Show the hosted reviewer home page.]**

Every day, EPR requirements and producer-responsibility information change in public registries. The problem is not getting another alert. The problem is knowing what changed, whether it matters, and whether the evidence is strong enough to deserve an operator’s time.

Vice CEO is my answer to that problem: a proof-carrying business autonomy system. It works in the background, but it does not ask anyone to blindly trust its recommendation.

## 0:25–0:50 — Explain the product promise

**[Point to the recommendation, evidence rail, and reviewer decision tray.]**

Here is the reviewer experience. Before a recommendation can move forward, its evidence, reasoning trail, authority limits, and replay path are available in one place.

This public interface uses named synthetic fixtures. That lets a judge inspect the full workflow safely, without customer data or a hidden production action. The key idea is simple: the agent must earn the right to progress.

## 0:50–1:35 — Prove it runs in the background

**[Show the Cloud Run / Scheduler evidence screen or the live Google Cloud card in the finished video.]**

Behind the reviewer surface is the deployed Registry Change Watch.

It monitors three reviewed public EPR sources: Oregon, California, and Maryland. Private Cloud Scheduler jobs invoke a private Cloud Run worker using OIDC. The worker normalizes visible public content, fingerprints it, and saves source snapshots, event claims, run receipts, and owner-review candidates in Firestore.

This is the deployed worker revision, with one hundred percent of traffic. The Cloud Run endpoint, Scheduler jobs, and Firestore evidence state are all part of the operating system—not a mocked background process.

When a source has not materially changed, Vice CEO stays quiet. When it does change, the system preserves the evidence needed to explain why an operator should care.

## 1:35–2:00 — Show the authority boundary

**[Show the source portfolio, operation overview, or boundary card.]**

The private operations view exposes approved sources, metadata, evidence hashes, queue counts, and authority limits. It does not expose customer records, billing tools, prospect contacts, or a commercial action button.

One controlled owner-mailbox verification was accepted by the configured internal provider. That proves the bounded owner-brief delivery path, not customer outreach or prospect messaging. Those capabilities do not exist in this runtime.

## 2:00–2:25 — Explain Gemini and ADK

**[Show the Gemini canary or the controlled replay label.]**

Gemini 3.5 Flash and Google ADK are used in a narrow, inspectable role.

After a material public-source change, the system can create an internal brief from a bounded excerpt. But first, a deterministic prompt-injection gate checks the untrusted public text. If it sees instruction-like content or a credential-extraction attempt, the model path stops and the system creates an evidence-linked owner-review fallback instead.

The recorded Gemini canary and controlled replay demonstrate the real code path with no customer data, no Firestore write, and no external business effect.

## 2:25–3:10 — Demonstrate the reviewer flow

**[Open the proof bundle, Action Warrant, and replay record.]**

Back in the reviewer workspace, each recommendation carries a proof bundle, a one-use Action Warrant, and a replay record.

Specialists can advise, but they do not have direct business tools. The deterministic gateway consumes a short-lived, one-use warrant before the only registered transition: a synthetic simulation.

That approval is deliberately bounded. It produces a readable simulation receipt and nothing beyond it. No customer contact, persistence, or external effect occurs from this public demo.

## 3:10–3:40 — Establish resilience

**[Show the prompt-injection fallback, unregistered-source rejection, or test result.]**

The system is designed to fail safely. Unregistered sources are rejected. A used warrant cannot be used again. Prompt injection is stopped before the model boundary. And the release has eighty-six automated tests covering authority, evidence integrity, adversarial probes, evaluation behavior, and the reviewer routes.

## 3:40–4:00 — Close on value

**[Show the architecture diagram, then return to the hosted reviewer.]**

Vice CEO turns quiet registry monitoring into accountable executive attention.

It runs asynchronously, explains a change with evidence, and surfaces a real decision only when one is warranted—while keeping customer data, commercial messaging, and unbounded agent authority out of the system by design.

That is proof-carrying autonomy: useful enough to work in the background, and disciplined enough to be trusted when it asks for attention.
