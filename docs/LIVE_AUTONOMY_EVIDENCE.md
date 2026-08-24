# Live Registry Change Watch Evidence

**Captured:** 2026-08-24 UTC  
**Purpose:** a concise, reviewable ledger for the private operational layer.
It is not a claim that the public reviewer page can access this worker, and it
does not grant any new business authority.

## What ran

| Component | Verified state |
| --- | --- |
| Private worker | Cloud Run `vice-ceo-registry-worker-00008-qv8`, `us-central1`, private ingress |
| Background trigger | Cloud Scheduler `vice-ceo-registry-watch-direct-daily`, daily at `08:30 UTC`, private OIDC target |
| Source | Oregon DEQ *Producers of Covered Products* public page, locked in reviewed configuration |
| Durable state | Firestore source snapshot, event claim, and run receipt collections |
| Public reviewer | Separate fixture-only Cloud Run service at [`/demo`](https://vice-ceo-review-demo-77u4kmu2ba-uc.a.run.app/demo) |

## Observed scheduler receipts

| UTC run | Run ID | Result | What it proves |
| --- | --- | --- | --- |
| 2026-08-24 05:18:08 | `registry_run_37683f3c7969ba92a8ca` | `baseline_captured` / `source_normalization_rebaselined` | The private OIDC schedule reached Cloud Run, fetched the approved public source, and persisted a new stable visible-content baseline. No brief or delivery was created. |
| 2026-08-24 05:18:53 | `registry_run_7135d8efce632e98ce66` | `no_change` / `source_evidence_hash_unchanged` | A distinct scheduled event read the same evidence hash and stayed quiet. |

Both receipts use the normalized visible-content SHA-256
`e5da9c7d8eab3bdb7e430d74fecc6a7e440e1559c9686fbace796918ff221f72`.
The watcher intentionally ignores volatile HTML script/style scaffolding. This
prevents a request token or generated timestamp from becoming a false EPR alert.

## Gemini connectivity evidence

The private worker also recorded one bounded Vertex/Gemini canary receipt:

- receipt: `provider_canary_receipt_5d1c3c7023f04e7d8acdde6a00586dcf`;
- model: `gemini-3.5-flash`;
- outcome: completed, with zero tool calls;
- customer data: false;
- persistent business write: false; and
- external business effect: false.

The scheduled registry worker keeps Gemini briefing disabled by default. The
canary proves connectivity only; it does not prove authority to use customer
data or send an external message.

## Deliberate limits

- The operational worker fetches only explicitly reviewed **public** sources.
- It writes only its own evidence state in Firestore; it cannot alter Westover
  EPR customer, billing, support, or compliance records.
- No owner briefing email has been sent. That channel needs a dedicated Resend
  Secret Manager credential, verified internal sender, and allowlisted owner
  recipient.
- It cannot determine legal obligations or send prospect outreach.
- The public `/demo` remains a reproducible synthetic reviewer experience and
  cannot receive Registry Change Watch events.

## Reviewer replay path

1. Inspect [the source configuration](../config/registry-sources.oregon-deq.json).
2. Inspect the strict event, source fetch, Firestore, Gemini, and delivery
   boundaries in [`app/registry_watch.py`](../app/registry_watch.py).
3. Run the 75-test suite and open the public reviewer flow.
4. In the video, show the Cloud Scheduler job, Cloud Run revision/log, and the
   Firestore receipts above. Keep the public and private planes distinct.

