# Layer 2: trust

Layer 1 protects against a fooled model. Layer 2 protects against everything around the model: a spending policy nobody signed, an approval nobody gave, and an invoice edited after it was checked.

Rule: the owner signs, the server verifies, and no payment leaves without passing the verifier. The private key never leaves the browser.

## What is signed, by whom

| Item | Signed by | Contains | Checked |
|---|---|---|---|
| Policy (mandate) | Owner, in the browser | Rules, policy text, user id, a nonce | Before every payout |
| Cart (approval) | Owner, when clicking Approve | Policy id, invoice number, invoice hash, payee, amount, currency, request id, expiry | Right before the payout |
| Auto paid request | Not signed one by one | Same facts, bound to the signed policy | The verifier checks it fits inside the signed rules |

This is an AP2 inspired simplification, not a full implementation of the protocol. Small routine payments are authorized by the signed policy. Payments above the limit need the owner's signature on the exact cart.

## Signing, step by step

The server builds the exact string, the browser signs those bytes unchanged, and the server verifies against the stored string. Nothing is serialized twice, so there are no cross language formatting problems.

1. **Key.** On login the browser creates an ECDSA P-256 key pair with `extractable: false` and keeps it in IndexedDB (`frontend/src/lib/crypto.ts`). It sends the public key (base64 SPKI) to `POST /auth/register-key`. Registering a different key deactivates the active policy, because its signature no longer matches. Replacing a key the server already has requires the account password, so a stolen login token cannot swap in an attacker's key.
2. **Prepare.** `POST /mandates/prepare` with the policy text and rules. The server validates them, stores an inactive mandate and returns `{ mandate_id, payload }`. The payload contains a fresh nonce.
3. **Sign.** The browser signs the payload. WebCrypto returns a raw 64 byte `r||s` signature.
4. **Activate.** `POST /mandates/{id}/sign`. The server converts raw to DER (`encode_dss_signature`), verifies, activates this mandate and deactivates older ones. It audits `mandate_activated`.

Rules and expiry are always read from the signed payload (`signed_rules`), never from the editable `rules` column. Editing the column in the database changes nothing.

## The verifier (`services/verifier.py`)

It runs inside `execute_payout`, so no caller can skip it. `execute_payout` is still the only function that moves money. Any failure means PayPal is not called, the request and invoice become `BLOCKED`, and `verifier_failed` is audited with the reasons.

| Check | Failure text |
|---|---|
| An active policy exists | No active signed policy |
| The policy signature is valid | Policy signature invalid |
| The policy has not expired | Policy expired |
| Live invoice hash equals the snapshot | Invoice changed after evaluation |
| Live payee equals the snapshot | Payee changed after evaluation |
| Live amount equals the snapshot | Amount changed after evaluation |
| Currency allowed by the policy | Currency not allowed by policy |
| Cart matches the invoice (approvals) | Cart no longer matches the invoice |
| Cart not past its expiry (approvals) | Approval expired |
| Owner signature on the cart (approvals) | Approval signature invalid |
| Month spend plus amount within budget | Monthly budget exceeded |
| No payout exists for this request | This request was already paid |

When the verifier refuses, the request's decision becomes `BLOCKED` with risk `HIGH`. The audit trail keeps the original `decision_made` event.

## Approvals

When the rules say `NEEDS_APPROVAL`, the pipeline builds a cart from the frozen snapshot, with an expiry 24 hours ahead, and audits `approval_requested`. Without an active policy no cart is built, so the approval cannot be executed.

| Endpoint | Behavior |
|---|---|
| `GET /approvals` | Requests awaiting approval, with the cart string to sign |
| `POST /approvals/{id}/approve` | Body `{ signature }`. 400 if invalid (the request stays open), 409 if expired or not awaiting. Otherwise audits `approved` and runs the verifier and payout |
| `POST /approvals/{id}/reject` | Body `{ reason? }`. Sets `REJECTED`, audits `rejected`, pays nothing |

An expired approval returns 409, sets the request to `EXPIRED` and the invoice back to `PENDING`, so the invoice can be submitted again. Signing a new policy invalidates open approvals, because the cart contains the policy id. Submit the invoice again.

## Endpoints added in layer 2

| Endpoint | Purpose |
|---|---|
| `POST /auth/register-key` | Store the browser's public key |
| `POST /mandates/prepare`, `POST /mandates/{id}/sign` | Policy signing flow |
| `GET /mandates/active`, `GET /mandates`, `GET /mandates/{id}/verify` | Active policy (with `verified`), history, re-verification |
| `GET /approvals`, `POST /approvals/{id}/approve`, `POST /approvals/{id}/reject` | Approval flow |
| `POST /payments`, `GET /payments/{id}` | Request a payment (same pipeline as the agent), one request with its summary |
| `PATCH /dev/invoices/{number}`, `POST /dev/mandates/{id}/tamper` | Development only test aids |

The `/dev` routes are mounted only when `APP_ENV=development`. They exist to demo the tamper refusal and never touch PayPal.

## Frontend

All eight pages are built to `docs/DESIGN.md` and `docs/FRONTEND.md`. The layer 2 screens are Policy (rules form, active policy with a Verified or Signature invalid badge, history, demo tools) and Approvals (decision cards with a signing modal that shows the exact data being signed). A pink banner appears on every page while the active policy fails verification, and a yellow one while there is no policy.

## Tests

```bash
cd backend && PAYPAL_MODE=fake pytest -q
```

| File | Covers |
|---|---|
| `test_mandate.py` | Signature helpers: valid, tampered payload, wrong key, bad length, cart built from the snapshot |
| `test_mandates_api.py` | Key registration, prepare, sign, replace, new key deactivates, history, verify, policy tamper |
| `test_verifier.py` | No policy, expired, forged signature, edited rules column, tampered invoice, replay, budget |
| `test_approvals.py` | Approve pays, reject does not, bad signature keeps the request open, tamper after request, expiry |
| `test_security.py` | Key replacement needs the password, login rate limit, weak production config refused, input limits, invoice claim (see [security.md](security.md)) |

The tests sign with a real P-256 key and produce the same 64 byte format a browser produces. A `policy` fixture in `conftest.py` creates an active signed policy for the tests that pay.

Without the frontend, `scripts/sign_policy.py` plays the browser's part. Its key lives in `scripts/owner_key.pem` (gitignored). It is a test aid only.

## Manual test path

1. Log in. A yellow banner says there is no active policy.
2. Pay INV-001: blocked, no active signed policy.
3. Policy page, Review and sign, Sign policy: Verified badge, banner gone.
4. Pay INV-001: paid.
5. Pay INV-003: needs approval. Approvals, Review and sign, Sign and approve: paid.
6. Pay INV-005: blocked with two reasons. Replay shows the failing check.
7. Policy page, Demo tools, Simulate tampering: pink banner, Signature invalid. Pay INV-002: blocked, policy signature invalid.
8. Tamper after approval: request INV-003, change its amount with `PATCH /dev/invoices/INV-003`, then approve. Result is blocked with "Amount changed after evaluation" and no payout.

## Known gaps

- Webhooks are a stub, so payout confirmation relies on polling.
- LLM policy drafting (`/mandates/draft`) is not built. The Policy page edits the rules form directly.
- Invoices still cannot be added without re-seeding.
- The private key lives in one browser. Clearing browser data loses it. Use Reset signing key in Demo tools and sign the policy again.
