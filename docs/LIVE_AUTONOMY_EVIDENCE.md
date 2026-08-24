# Live Registry Change Watch Evidence

**Captured:** 2026-08-24 UTC  
**Purpose:** a concise, reviewable ledger for the private operational layer.
It is not a claim that the public reviewer page can access this worker, and it
does not grant any new business authority.

## What ran

| Component | Verified state |
| --- | --- |
| Private worker | Cloud Run `vice-ceo-registry-worker-00022-c8w`, `us-central1`, private ingress; source metadata agrees with the enabled 08:31 / 08:36 / 08:41 UTC Scheduler jobs |
| Background trigger | Three enabled private OIDC Scheduler jobs: Oregon `08:31 UTC`, California `08:36 UTC`, Maryland `08:41 UTC` |
| Sources | Reviewed official Oregon DEQ, CalRecycle SB 54, and Maryland Department of the Environment public EPR program pages |
| Durable state | Firestore source snapshot, event claim, run receipt, and owner-review action-queue collections |
| Owner review | Private Cloud Run operations overview, inbox, and JSON action queue live behind service authentication; no public-demo exposure |
| Public reviewer | Separate fixture-only Cloud Run `vice-ceo-review-demo-00015-tv9` at [`/demo`](https://vice-ceo-review-demo-77u4kmu2ba-uc.a.run.app/demo); its synthetic approval returns a readable receipt and warrant with zero external effect |

## Observed scheduler receipts

| UTC run | Run ID | Result | What it proves |
| --- | --- | --- | --- |
| 2026-08-24 05:18:08 | `registry_run_37683f3c7969ba92a8ca` | `baseline_captured` / `source_normalization_rebaselined` | The private OIDC schedule reached Cloud Run, fetched the approved public source, and persisted a new stable visible-content baseline. No brief or delivery was created. |
| 2026-08-24 05:18:53 | `registry_run_7135d8efce632e98ce66` | `no_change` / `source_evidence_hash_unchanged` | A distinct scheduled event read the same evidence hash and stayed quiet. |
| 2026-08-24 05:43:16 | `registry_run_e98249943f48424c66af` | `baseline_captured` / `first_source_snapshot_recorded` | An explicit invocation of the enabled California Scheduler job reached the private worker and persisted CalRecycle's first source baseline. No brief or delivery was created. |
| 2026-08-24 05:43:17 | `registry_run_50eec5ce39c50619832f` | `baseline_captured` / `first_source_snapshot_recorded` | An explicit invocation of the enabled Maryland Scheduler job reached the private worker and persisted Maryland's first source baseline. No brief or delivery was created. |
| 2026-08-24 06:01–06:02 | `registry_run_a7da3312d831b5e256fe` (OR), `registry_run_f330efb468ca0e896f2c` (CA), `registry_run_9f6548dd4d87569d5eff` (MD) | `no_change` / `source_evidence_hash_unchanged` | Each portfolio source fetched unchanged visible content and refreshed its private segment-hash comparison baseline (Oregon 40 segments, California 32, Maryland 24). No Gemini brief, owner action, or delivery was created. |

The two Oregon receipts use the normalized visible-content SHA-256
`e5da9c7d8eab3bdb7e430d74fecc6a7e440e1559c9686fbace796918ff221f72`.
The watcher intentionally ignores volatile HTML script/style scaffolding. This
prevents a request token or generated timestamp from becoming a false EPR alert.

The private operations overview was also accessed through the authenticated
Cloud Run proxy after revision `00022-c8w` became ready. It reported the three
approved sources, zero pending owner decisions, the
`registry_source_prompt_injection_gate_v1` safety boundary, and `false` for
external business actions. This verifies the live private read surface; it
does not create an owner decision or a downstream business effect.

## Gemini connectivity evidence

The private worker also recorded one bounded Vertex/Gemini canary receipt:

- receipt: `provider_canary_receipt_5d1c3c7023f04e7d8acdde6a00586dcf`;
- model: `gemini-3.5-flash`;
- outcome: completed, with zero tool calls;
- customer data: false;
- persistent business write: false; and
- external business effect: false.

The scheduled registry worker now has bounded Gemini/ADK briefing enabled for
a material change. It receives only the ephemeral changed public-text excerpt,
never customer data, and cannot send an external message. Before the model
boundary, a deterministic prompt-injection gate rejects instruction-like or
credential-exfiltration content and creates a hash-linked owner-review fallback
instead. No production source change has yet invoked that briefing path; the
canary remains the completed provider-connectivity proof.

On 2026-08-24, the explicit controlled replay command also completed the exact
changed-source → Gemini/ADK → owner-action-candidate code path locally. It used
two fixed non-production fixture revisions and produced
`registry_brief_fde8d07fd3c759fbbcfb` with model mode `gemini_3_5_flash_adk`,
two changed segments, and candidate `registry_action_16a8af7156576501ade6` in
`awaiting_owner_review`. The resulting receipt reports zero customer mutation,
zero external business effect, and `not_configured` internal delivery. It made
no Firestore write or official-source fetch, so it is evidence of the bounded
code path—not a claim that an EPR registry changed.

## Deliberate limits

- The operational worker fetches only explicitly reviewed **public** sources.
- It writes only its own evidence state in Firestore; it cannot alter Westover
  EPR customer, billing, support, or compliance records.
- The private operations overview shows source metadata, evidence hashes, queue
  counts, and authority boundaries—not raw fetched page bodies or customer data.
- No owner briefing email has been sent. That channel needs a dedicated Resend
  Secret Manager credential, verified internal sender, and allowlisted owner
  recipient.
- It cannot determine legal obligations or send prospect outreach.
- The public `/demo` remains a reproducible synthetic reviewer experience and
  cannot receive Registry Change Watch events.

## Reviewer replay path

1. Inspect [the reviewed source portfolio](../config/registry-sources.epr-portfolio.json).
2. Inspect the strict event, source fetch, Firestore, Gemini, and delivery
   boundaries in [`app/registry_watch.py`](../app/registry_watch.py).
3. Run the 85-test suite and open the public reviewer flow.
4. In the video, show the Cloud Scheduler job, Cloud Run revision/log, and the
   Firestore receipts above. Keep the public and private planes distinct.
