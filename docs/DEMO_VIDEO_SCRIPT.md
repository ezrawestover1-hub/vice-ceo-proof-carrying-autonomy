# Vice CEO — Four-Minute Judge Demo

**Purpose:** a single take that proves operational utility, architecture, and
production-minded evidence boundaries for the All Things Agentic Hackathon.

**Recording rule:** show the actual hosted reviewer and actual Google Cloud
surfaces. Never show credentials, recipient addresses, raw email content, or
customer data. The controlled Registry Change Watch replay remains visibly
labeled as non-production fixture evidence.

For a natural human narration, use
[the read-aloud script](DEMO_VIDEO_READ_ALOUD_SCRIPT.md).

## Capture timeline

| Time | Screen | Proof point |
| --- | --- | --- |
| 0:00–0:25 | Hosted `/demo` reviewer | The problem and proof-carrying promise |
| 0:25–0:50 | Evidence rail and five-act flow | Evidence, warrant, and replay—not a chatbot |
| 0:50–1:35 | Cloud Run and Scheduler console | The watcher runs asynchronously on Google Cloud |
| 1:35–2:00 | Private operations overview / portfolio evidence | Approved public sources, durable state, owner review |
| 2:00–2:25 | Gemini canary and controlled replay evidence | Gemini + ADK act on bounded public excerpts only |
| 2:25–3:10 | Hosted reviewer decision and warrant views | A usable decision surface with no business-tool authority |
| 3:10–3:40 | Test result and prompt-injection boundary | Resilience and reproducibility |
| 3:40–4:00 | Architecture diagram and closing reviewer view | Clear value proposition and safe operating boundary |

## Narration

Every day, EPR programs and producer-responsibility requirements change in
public registries. For an operator, the hard part is not finding another alert.
It is deciding what changed, whether it matters, and whether the evidence is
strong enough to deserve attention. Vice CEO is a proof-carrying business
autonomy system built for that gap.

This is the hosted reviewer experience. It does not ask a user to trust a
black-box recommendation. Before a proposed action is even reviewable, the
system puts its evidence, reasoning, authority limits, and replay path in one
place. The public interface uses named synthetic fixtures so that anyone can
inspect the contract safely.

The five-act flow makes the design concrete. A bounded operational signal
becomes evidence. ADK specialists advise but do not receive business tools. A
short-lived, one-use Action Warrant gates the only permitted simulated
transition. The result can be replayed and challenged, and adversarial tests
verify that the boundary stays intact. This is not a chatbot that drafts a
paragraph. It is a workflow where an agent must earn the right to progress.

Behind that reviewer surface is the deployed Registry Change Watch. Three
reviewed public EPR sources—Oregon, California, and Maryland—are invoked by
private Cloud Scheduler jobs. Those jobs use OIDC to call a private Cloud Run
worker. The worker normalizes visible public content, fingerprints it, and
stores source snapshots, event claims, receipts, and owner-review candidates in
Firestore. When a source has not materially changed, it stays quiet. When it
does change, the system preserves the evidence required to explain why an
operator should care.

The private operations surface shows the approved source portfolio, source
metadata, evidence hashes, queue counts, and authority boundaries. It does not
show raw customer records, billing tools, prospect contacts, or a way for a
model to take a commercial action. A controlled owner-mailbox verification was
accepted through the separately configured internal channel, but no customer
or prospect messaging capability exists here.

Gemini 3.5 Flash and Google ADK are used in a narrow, inspectable role. A
material public-source change can produce an internal brief only after a
deterministic prompt-injection gate evaluates the untrusted public excerpt. If
the excerpt looks instruction-like or attempts credential extraction, the
model path is stopped and the system creates an evidence-linked fallback for
owner review. The recorded Gemini canary and controlled replay demonstrate the
real code path with no customer data, no Firestore write, and no external
business effect.

Back in the reviewer workspace, every recommendation carries its proof bundle,
Action Warrant, and replay record. The synthetic approval is deliberately
bounded: it creates a readable simulation receipt and nothing beyond it. The
same release includes a registered-source rejection, one-use warrant denial,
and an eighty-six-test suite covering authority, evidence integrity,
evaluation, adversarial probes, and visual routes.

Vice CEO turns quiet registry monitoring into accountable executive attention.
It runs in the background, explains changes with evidence, and surfaces a
decision only when one is warranted—while keeping customer data, commercial
messaging, and unbounded agent authority out of the system by design.
