# Dev log

Write three lines every day: what ran, what broke, next step.

- 2026-10-11: PayPal sandbox Payouts verified end to end with US sandbox accounts (Rwanda sandbox accounts were denied).
- 2026-10-11: Layer 1 verified live (INV-001 paid in sandbox, INV-003 needs approval, INV-004 blocked). Todo for layer 4 chat: rule based matcher misses "pay invoice 4" (regex only accepts "inv"), cannot filter list by status or "pay all pending". LLM mode already handles these through list_invoices and repeated submit_payment_request. Fixes: accept "invoice" in the regex, add optional status filter to list_invoices.
- 2026-10-11: Possible layer 4 item: invoices only enter the db through backend/seed.py (it wipes all tables). Add POST /invoices (supplier, amount, description, payee email) behind login so demo data can grow without a reseed. Run the injection scan on intake. Not in the 30 day plan, so optional.
- 2026-10-11: Layer 2 built: signed policy (ECDSA P-256, signed in the browser), verifier inside execute_payout, signed approvals with 24 hour expiry, tamper helpers (dev only), frontend with all 8 pages. Browser run on fake PayPal covered sign policy, pay, approve, replay, tamper. Still to do before v0.2-trust: live run on real sandbox and Postgres, visual pass at 1024px, tag.
- 2026-10-12: Layer 3 built (`v0.3-detection`): duplicate invoice (within 1%), amount outlier (median), new payee email, round amount (context only), more injection patterns on normalised text across description, number and supplier name. Reasons are now `{code, level, message}` everywhere (agreed with Alain). 56 backend tests pass, frontend build passes. LLM classifier and thresholds in the signed policy left out. Next: PayPal webhook, VPS deploy.
