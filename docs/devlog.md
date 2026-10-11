# Dev log

Write three lines every day: what ran, what broke, next step.

- 2026-10-11: PayPal sandbox Payouts verified end to end with US sandbox accounts (Rwanda sandbox accounts were denied).
- 2026-10-11: Layer 1 verified live (INV-001 paid in sandbox, INV-003 needs approval, INV-004 blocked). Todo for layer 4 chat: rule based matcher misses "pay invoice 4" (regex only accepts "inv"), cannot filter list by status or "pay all pending". LLM mode already handles these through list_invoices and repeated submit_payment_request. Fixes: accept "invoice" in the regex, add optional status filter to list_invoices.
- 2026-10-11: Possible layer 4 item: invoices only enter the db through backend/seed.py (it wipes all tables). Add POST /invoices (supplier, amount, description, payee email) behind login so demo data can grow without a reseed. Run the injection scan on intake. Not in the 30 day plan, so optional.
