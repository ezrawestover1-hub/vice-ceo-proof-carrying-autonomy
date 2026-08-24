# Registry Change Watch

## Purpose

Registry Change Watch is Vice CEO's first autonomous, behind-the-scenes job.
It is deliberately narrow: when a pre-registered public EPR source changes,
the worker preserves a hash-linked source snapshot, prepares a bounded
operational brief, and sends an owner-facing briefing through a separately
configured internal channel.

On a material change, it also writes an evidence-linked `prepare_internal_impact_memo`
candidate into a private owner-review queue. This candidate is not external
outreach and cannot mutate a Westover customer record; it gives the owner a
durable decision item even if the separate briefing channel is disabled or
temporarily unavailable.

It does not decide legal obligations, write Westover EPR customer records, or
send an external prospect message. Any later outreach workflow consumes a
reviewable candidate; it does not receive delivery authority from this worker.

## Current local implementation

The runtime contains:

- strict `registry.watch.requested` event and Pub/Sub envelope contracts;
- registered-source enforcement, so events cannot supply a URL or source body;
- source version and SHA-256 evidence capture with no raw source text in run
  receipts;
- hash-only source-content segment comparison that isolates newly observed
  public text ephemerally for a bounded brief, without persisting the excerpt;
- visible-content normalization for HTML sources, excluding script and style
  scaffolding so a volatile request token cannot create a false change alert;
- baseline, no-change, changed, and duplicate terminal states;
- a durable owner-review action candidate for every changed source, linked to
  the brief and its evidence hash;
- a private, Cloud Run IAM-protected owner inbox at
  `/owner/registry-actions/inbox`, with a JSON queue at
  `/owner/registry-actions`;
- owner-only `acknowledge` or `archive` transitions that persist a review
  outcome without invoking a business action, customer-record change, or
  external message;
- an explicit rebaseline when content normalization is upgraded, avoiding a
  fake change brief during a watcher migration;
- an in-memory local store plus a Firestore state adapter;
- a deterministic factual brief generator that does not make a regulatory
  conclusion;
- a disabled-by-default owner-facing delivery adapter and a recording test
  adapter; and
- reviewed deployment adapters for HTTPS public-source retrieval, Google ADK
  Gemini brief generation, Firestore state, and allowlisted SMTP owner delivery;
- `/demo/registry-watch` plus focused unit and HTTP tests.

The local demo uses only `Demo Packaging Registry` fixture revisions. It does
not establish real Scheduler, Pub/Sub, Firestore, Gemini, source-fetch, or
mail-delivery evidence.

## Runtime configuration

The default `VICE_CEO_REGISTRY_WATCH_MODE=fixture` keeps the service on the
closed local demo. To select the configured worker, set
`VICE_CEO_REGISTRY_WATCH_MODE=configured` and provide:

```text
VICE_CEO_REGISTRY_SOURCES_JSON=[{"source_id":"...","display_name":"...","canonical_url":"https://...","jurisdiction":"...","source_owner":"...","refresh_schedule":"0 9 * * *","operational_focus":"..."}]
VICE_CEO_REGISTRY_WATCH_STORE=firestore
VICE_CEO_REGISTRY_BRIEF_GENERATOR=gemini
VICE_CEO_REGISTRY_GEMINI_ENABLED=true
VICE_CEO_INTERNAL_BRIEF_DELIVERY=smtp
VICE_CEO_INTERNAL_BRIEF_DELIVERY_ENABLED=true
VICE_CEO_INTERNAL_SMTP_HOST=...
VICE_CEO_INTERNAL_SMTP_PORT=465
VICE_CEO_INTERNAL_BRIEF_FROM=...
VICE_CEO_INTERNAL_BRIEF_TO=...
VICE_CEO_INTERNAL_SMTP_USERNAME=...
VICE_CEO_INTERNAL_SMTP_PASSWORD=...  # Secret Manager only
# Or use Westover's existing provider family through a separate internal-only
# sender credential. This never enables commercial outreach.
VICE_CEO_INTERNAL_BRIEF_DELIVERY=resend
VICE_CEO_INTERNAL_RESEND_DELIVERY_ENABLED=true
VICE_CEO_INTERNAL_RESEND_API_KEY=re_...  # Secret Manager only
```

The worker refuses an unreviewed source list, an unregistered event source, an
unapproved Gemini generator, and an enabled SMTP mode missing its required
settings. The source JSON contains public URLs only; credentials must never be
committed or passed in source configuration.

### Owner briefing activation

The deploy script accepts `--resend-secret`, `--brief-from`, and `--brief-to`
only as one complete set. The secret must already exist in Google Secret
Manager; the script grants the private worker access to that one secret and
binds it into the revision without exposing the value. The sender must be a
dedicated verified internal briefing sender, and the recipient must be the
allowlisted Westover owner mailbox. Do not reuse a transactional-support or
commercial-outreach credential for this channel.

On an executing deployment, the script also fails before it changes worker
access if the named secret is missing or has no enabled Secret Manager version.
That makes the delivery activation dependency explicit instead of leaving a
partially configured worker after a late provider-credential failure.

`--gemini-briefs` is separately explicit. It enables Gemini only to produce a
bounded, cited briefing after the watcher detects a materially changed public
source; it does not enable delivery by itself.

### Controlled changed-source replay

`python -m app.registry_change_replay --confirm-controlled-replay` is a video
and regression-proof tool, not an operating source. It additionally requires
`VICE_CEO_CONTROLLED_REPLAY_ENABLED=true` and Vertex configuration. It drives
the same changed-source, Gemini/ADK, and owner-queue code path with two fixed
non-production fixture revisions. It never fetches an official registry,
writes Firestore, reads customer data, or attempts owner delivery. Any video
must label it a controlled replay rather than a live public-source change.

## Deployment contract

Before a live registry-watch deployment, configure an isolated Google Cloud
project with these components:

1. **Cloud Scheduler** invokes the private worker once per approved source and
   interval with its dedicated OIDC identity.
2. **Cloud Run** verifies Scheduler identity before it processes the locked
   event body. The read-only reviewer page remains separately accessible.
3. **Firestore** is selected for registry-watch run state and idempotency. A
   container restart must not repeat a previously claimed event.
4. **Gemini 3.5 Flash through Google ADK** replaces the deterministic brief
   generator only after the provider canary has recorded a successful receipt.
   Gemini receives the captured approved source material and must return a
   schema-constrained, cited operational summary. It cannot issue a legal
   conclusion or select an external recipient.
5. **Internal delivery** sends only to an explicitly configured, allowlisted
   Westover owner mailbox. Its receipt records hashes and a provider reference,
   never mailbox credentials or source body content.

The supported deployment path sends the private OIDC-authenticated request to
`/scheduler/registry-watch`. The body is source- and schema-locked, while Cloud
Scheduler's job and schedule-time headers produce the event identity. Pub/Sub
ingress remains available for a future fan-out architecture, but is not needed
for the operating watcher. Neither path is a public webhook or grants
external-message authority.

### Private owner review

The same private Cloud Run service exposes the owner-review queue at
`/owner/registry-actions/inbox`. Cloud Run IAM remains the access boundary; the
public reviewer service sets `VICE_CEO_PUBLIC_DEMO_ONLY=true` and returns 404
for all owner-review routes. Queue entries include only the evidence hash,
official public-source citation, bounded change summary, and recommended
internal next step. They never persist raw source text or customer records.

An owner can record either `acknowledge` or `archive`. That transition only
changes the durable action-queue record from `awaiting_owner_review`; it cannot
send email, contact a prospect, alter a customer record, or determine a legal
obligation. Delivery remains a separately configured internal-only capability.

On a macOS operator machine with `gcloud` authenticated, open the private
inbox with `scripts/open-owner-review.sh`. It starts a local authenticated
Cloud Run proxy, opens `http://127.0.0.1:8765/owner/registry-actions/inbox`,
and shuts the proxy down on exit. Use `--no-open` if you want to copy the local
URL into another browser profile. The script does not create an action,
acknowledge an action, or send a message.

The first production-like run needs these proof points:

- Cloud Run revision and authenticated endpoint response;
- Cloud Scheduler invocation and private Cloud Run 2xx log;
- Firestore run state showing a baseline then a changed source;
- provider canary receipt for `gemini-3.5-flash`;
- one source-cited brief with no legal conclusion;
- one internal delivery receipt;
- a duplicate event that returns the prior run without another delivery; and
- an invalid/unregistered source request rejected before fetch or delivery.

## Source onboarding

Each real source must be added through reviewed configuration, not incoming
events. Record its canonical HTTPS URL, jurisdiction, display name,
`source_owner`, `refresh_schedule`, and `operational_focus`. Preserve the
previous and current evidence hashes so a reviewer can inspect why a change
was reported. `refresh_schedule` is used to create one private Scheduler job
per approved source. `operational_focus` appears in the bounded owner brief so
the change is framed as a specific Westover review task—not as a legal
conclusion.

Do not send the source body, customer data, contact records, or unreviewed
prompt text to an external tool. The registry watcher produces an internal
brief and an evidence-backed outreach candidate only.

### First reviewed operating source: Oregon DEQ

`config/registry-sources.oregon-deq.json` names the public Oregon Department
of Environmental Quality **Producers of Covered Products** page as the first
operating source. It is an official state page for Oregon's Recycling
Modernization Act producer obligations and program updates. The initial worker
uses a daily-or-slower schedule, deterministic internal briefs, Firestore
evidence state, and disabled email delivery.

This source is a compliance-update surface, not a claim that Westover has a
complete producer-member registry or that the worker can determine a company's
legal status. Any use of a change for an external message still requires a
separate approved outreach policy and recipient authority.

### Reviewed public EPR portfolio

`config/registry-sources.epr-portfolio.json` contains three official public
program surfaces that are tested with the worker's bounded HTTPS fetcher:

| Jurisdiction | Source | What Vice CEO watches |
| --- | --- | --- |
| US-OR | Oregon DEQ Producers of Covered Products | Producer obligations and Recycling Modernization Act updates |
| US-CA | CalRecycle SB 54 Packaging EPR | Program news and producer guidance |
| US-MD | Maryland Producer Responsibility | Packaging and paper program updates plus published producer materials |

This is a deliberately curated watchlist, not a claim that these pages are a
complete registry of regulated businesses. Each source uses a staggered daily
private schedule, retains separate evidence history, and produces an internal
review recommendation only when its visible public content changes.
