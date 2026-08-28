# Vice CEO business actions

Vice CEO has two execution lanes that are intentionally separate from the EPR registry watcher:

1. **Routine customer service.** A reply can be sent only for a known low-risk intent, a valid customer email, and a linked inbound message. New, sensitive, financial, legal, or account-changing requests must be escalated.
2. **Approved outreach follow-up.** A message can be sent only from a named campaign, to a contact with a consent record who is not suppressed. A stable idempotency key stops the same action being sent twice.

Both lanes create an action receipt containing the action type, source reference, provider result, and idempotency key. The public `/demo/business-actions` endpoint always uses fixed `.invalid` recipients and a recording delivery adapter. It cannot send email.

## Private Westover runtime

The private worker may enable the Resend delivery adapter only when all of the following are configured outside source control:

- `VICE_CEO_BUSINESS_ACTIONS_ENABLED=true`
- `VICE_CEO_BUSINESS_EMAIL_DELIVERY=resend`
- `VICE_CEO_BUSINESS_RESEND_API_KEY` from Secret Manager
- `VICE_CEO_BUSINESS_EMAIL_FROM=support@westoverepr.com` (or another verified sender)
- `VICE_CEO_BUSINESS_NAME=Westover EPR`

The separate registry-watch delivery setting remains owner-briefing-only. It does not grant customer-service or prospect-outreach authority. Before enabling the business lane, connect the real inbound inbox/contact source, record approved response policies and campaigns, and send a controlled owner-address verification through the private worker.

When the private Cloud Run worker is deployed with those variables, its
IAM-protected execution endpoints are:

- `POST /internal/business-actions/customer-replies`
- `POST /internal/business-actions/outreach-follow-ups`

They are deliberately unavailable on the public reviewer deployment. An inbox
or CRM integration calls the private endpoint with a source-linked support case
or an approved, consented campaign contact; Vice CEO then dispatches through
Resend and returns a provider receipt. No browser visitor can supply a real
recipient to the public demo.
