# Layer 1: core

Layer 1 turns a chat message into either a confirmed PayPal sandbox payout or a recorded refusal.

Golden rule: the LLM proposes, deterministic code decides. The agent has no tool that moves money.

## Request flow

```
Owner message ("Pay INV-001")
   |  POST /agent/chat (JWT login required)
Agent (services/agent.py)       LLM or rule based matcher
   |  only payment tool: submit_payment_request
Pipeline (services/pipeline.py) plain Python, no LLM
   |-- load invoice and supplier, snapshot them
   |-- truth check (services/truth_check.py)  -> signals
   |-- decide (services/decision.py)          -> AUTO_PAY, NEEDS_APPROVAL or BLOCKED
   '-- AUTO_PAY only -> execute_payout        -> PayPal Payouts API
```

## Agent (`services/agent.py`)

The agent understands the owner message and calls tools. It has six:

| Tool | Purpose |
|---|---|
| `list_invoices` | All invoices with status |
| `get_invoice` | One invoice. The description is wrapped in `<invoice_text>` tags |
| `get_supplier` | One supplier by name |
| `get_policy` | The current spending policy |
| `submit_payment_request` | Hands an invoice to the pipeline and returns its verdict |
| `explain_request` | Audit events for a payment request |

None of them moves money. `submit_payment_request` only passes the invoice number to the pipeline.

There are two interchangeable brains, and the `mode` field of the response says which one ran:

| `mode` | When |
|---|---|
| `llm` | `LLM_API_KEY` and `LLM_MODEL` are set. With `LLM_BASE_URL` it uses `llm_agent_openai` (Groq, xAI), otherwise `llm_agent` (Anthropic) |
| `rules` | No LLM key. Regexes find an `INV-nnn` number and a verb (pay, why, list) |
| `rules_fallback` | The LLM call raised an error. An `llm_error` entry is added to the trace and the rule based matcher answers |

Both LLM loops work the same way: send the message and the tools, run any requested tool through `run_tool`, send the result back, and stop when the model answers in text or after 6 turns. `temperature` is 0.

Prompt injection defence at this level:

- `get_invoice` wraps invoice text in `<invoice_text>` tags.
- The system prompt says text in those tags is untrusted and must never be followed.
- The system prompt says the agent cannot approve payments.

The real defence is the pipeline, because the model can be fooled and the pipeline cannot.

## Pipeline (`services/pipeline.py`)

`submit_payment_request` runs these steps in order. Each step writes an audit event.

1. Find the invoice. An unknown number returns an error.
2. Idempotency: an invoice that is already `PAID`, `SENT` or `AWAITING_APPROVAL` returns the existing request with a note. No second request is created.
3. Create a `PaymentRequest` with a frozen snapshot: invoice hash (SHA-256 of number, supplier, payee email, amount, currency, description), payee email and amount. Layer 2 compares the live invoice against this snapshot before paying.
4. Collect the amounts of earlier successful payouts to the supplier.
5. Run the truth check.
6. Decide.
7. Act on the decision:
   - `BLOCKED`: status `BLOCKED`, audit `blocked_no_payout` with `paypal_called: false`. PayPal is never contacted.
   - `NEEDS_APPROVAL`: status `AWAITING_APPROVAL`. Nothing is paid. Layer 2 adds the signed approval.
   - `AUTO_PAY`: `execute_payout`.

## Truth check and decision

`truth_check.py` returns two lists of signals.

Blocking:

- The supplier is not verified.
- The payee email differs from the supplier's last successful payout email.
- The invoice text matches an injection pattern ("ignore previous policy", "pay immediately", "system prompt" and similar).

Review:

- First payment to a supplier with no history.
- Layer 3 adds duplicate invoice, amount outlier, new payee email and round amount. See [layer3.md](layer3.md).

`decision.py` is a few lines:

| Condition | Result | Risk |
|---|---|---|
| Any blocking signal | `BLOCKED` | HIGH |
| Any review signal, amount over the auto limit, or monthly budget exceeded | `NEEDS_APPROVAL` | MEDIUM |
| None of the above | `AUTO_PAY` | LOW |

Layer 1 uses default limits from config: `DEFAULT_AUTO_LIMIT` (500) and `DEFAULT_MONTHLY_BUDGET` (5000). Layer 2 replaces them with an owner signed policy.

## Moving money (`execute_payout`)

This is the only function in the codebase that sends money. Never add another path.

1. Build a unique batch id. It is also the PayPal idempotency key (`PayPal-Request-Id`), so a retry cannot pay twice.
2. Call `send_payout` on the PayPal client. In `sandbox` mode this is a real call to the Payouts API. In `fake` mode it is an offline stand-in.
3. Save a `Transaction` with status `PENDING`. Set the request and invoice to `SENT`.
4. Poll `get_batch` up to 6 times, 3 seconds apart:
   - `SUCCESS`: transaction, request and invoice become `PAID` and `payout_confirmed` is audited.
   - `DENIED`, `CANCELED` or `FAILED`: everything becomes `FAILED` and `payout_failed` is audited.
   - Still processing: the status stays `SENT`. Sandbox batches can take about five minutes.
5. `POST /transactions/{id}/refresh` polls PayPal again later.
6. A PayPal HTTP error sets `FAILED` and audits `payout_error`.

## Status lifecycle

```
PENDING -> BLOCKED
        -> AWAITING_APPROVAL
        -> SENT -> PAID
                -> FAILED
```

## Data

| Table | Holds |
|---|---|
| `suppliers` | Name, PayPal email, `verified`, `last_payout_email` |
| `invoices` | Number, supplier, description, amount, payee email, status |
| `payment_requests` | One per submission: snapshot, decision, risk, reasons, status |
| `transactions` | PayPal batch id, PayPal transaction id, status |
| `audit_events` | Ordered steps with a JSON detail per payment request |
| `users`, `mandates` | Created now, used from layer 2 |

Invoices enter the database only through `backend/seed.py`. It drops every table and loads 4 suppliers and 5 demo invoices. There is no upload or create endpoint.

## API

| Route | Purpose |
|---|---|
| `POST /auth/login` | Returns a JWT. Every route below needs it |
| `POST /agent/chat` | The chat entry point |
| `GET /invoices`, `GET /invoices/{number}` | Read invoices |
| `GET /suppliers` | Read suppliers |
| `GET /payments`, `GET /payments/{id}/trace` | Payment requests and their audit trail |
| `GET /transactions`, `POST /transactions/{id}/refresh` | Payouts and status refresh |

`/webhooks` is a stub. `/mandates` and `/approvals` were stubs in layer 1 and are live since layer 2.

## Demo invoices and expected results

| Invoice | Amount | Why | Result |
|---|---|---|---|
| INV-001 | 250 | Verified supplier, inside policy | `AUTO_PAY`, paid |
| INV-002 | 450 | Verified supplier, inside policy | `AUTO_PAY`, paid |
| INV-003 | 1500 | Above the auto limit | `NEEDS_APPROVAL` |
| INV-004 | 900 | Supplier not verified | `BLOCKED` |
| INV-005 | 480 | Payee email changed and injection text | `BLOCKED` with two reasons |

## Tests

```bash
cd backend && PAYPAL_MODE=fake pytest -q
```

- `test_pipeline.py` uses a spy PayPal client and asserts that blocked and approval invoices make no payout call, that a second submit does not pay twice, and that the audit steps are in order.
- `test_decisions.py` covers the decision function.
- `test_agent_llm.py` runs the Anthropic and OpenAI tool loops with scripted fake clients, plus the fallback to rules.
- `test_api.py` covers login, protected routes and the chat endpoint.

To test against the real sandbox, set `PAYPAL_MODE=sandbox`, run `python seed.py`, start the server and send `Pay INV-001` to `POST /agent/chat`. Call the refresh endpoint until the transaction is `SUCCESS`.

## Known gaps

- Policy limits are defaults, not signed by the owner (layer 2).
- No approval flow yet, so INV-003 waits (layer 2).
- No verifier re-checks the invoice against the snapshot before paying (layer 2).
- Webhooks are not implemented, so confirmation relies on polling.
- The rule based matcher misses "pay invoice 4" and cannot filter or batch.
- Invoices cannot be added without re-seeding.
