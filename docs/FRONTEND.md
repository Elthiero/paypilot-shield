# PayPilot Shield: Frontend Guide

Audience: Elthiero, Alain, and Claude Code while building the web app.
Companion file: `docs/DESIGN.md` (visual language, written after the reference images). This file says what to build and how. DESIGN.md says how it should look.

Status legend used below: **LIVE** means the endpoint exists in the repo today and is tested. Change a contract only by editing this file in the same pull request.

---

## 1. What the frontend is for

PayPilot Shield lets a business owner pay supplier invoices through an AI agent, but only inside a spending policy the owner signed, and only after an invoice truth check. The frontend has four jobs:

1. **Talk to the agent** in plain language ("Pay INV-003", "Why was INV-004 blocked?").
2. **Let the owner sign** the spending policy and individual approvals with a key that never leaves the browser.
3. **Show every decision** (AUTO_PAY, NEEDS_APPROVAL, BLOCKED) with the reasons.
4. **Replay the audit log** of any payment so a judge or an auditor can see exactly what happened.

Golden rule the UI must make visible: the AI proposes, deterministic code decides. The UI never offers a "pay now" button that skips the pipeline. Every payment goes through the pipeline, and the UI only shows its result.

## 2. Stack and conventions

| Concern | Choice |
|---|---|
| Framework | React 18, TypeScript, Vite 5 |
| Routing | react-router-dom v6 |
| Tables | AG Grid Community (`ag-grid-react`) |
| Styling | Tailwind CSS v3. Design tokens come from DESIGN.md and live in `tailwind.config.ts` |
| Signing | WebCrypto, ECDSA P-256, non-extractable key stored in IndexedDB via `idb-keyval` |
| Auth | JWT from `/auth/login`, kept in `sessionStorage` under `token` |
| Server state | Plain `fetch` through `src/lib/api.ts`, with small hooks. No Redux |

Rules:
- One component per file, named export default, props typed. No `any`.
- All HTTP goes through `api()` in `src/lib/api.ts`. No `fetch` inside pages.
- Money is displayed with `Intl.NumberFormat`, never string concatenation. Amounts arrive as JSON numbers.
- Every page has four states: loading, empty, error, data. Build all four.
- Untrusted text (invoice description, agent reply) is rendered as plain text. Never use `dangerouslySetInnerHTML`.
- No em dashes or en dashes in any UI copy, docs or comments.

### Environment variables

| Variable | Dev | Production (VPS) |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | `/paypilot/api` |
| `VITE_BASE` | `/` | `/paypilot/` |

In `vite.config.ts` set `base: process.env.VITE_BASE || "/"`. In `main.tsx` use `<BrowserRouter basename={import.meta.env.BASE_URL}>`. This keeps the Render fallback (served at `/`) and the VPS (served at `/paypilot/`) both working.

## 3. File layout

```
frontend/src/
  main.tsx
  App.tsx                  routes + layout shell + auth guard
  lib/
    api.ts                 fetch wrapper, attaches Bearer token, throws ApiError
    types.ts               TypeScript types for every API payload (section 6)
    crypto.ts              keypair, sign, base64 helpers, raw to DER note (section 8)
    format.ts              money, dates, status labels
  hooks/
    useApi.ts              { data, loading, error, reload } for GET calls
    useAuth.ts             login, logout, token state
  components/
    Shell.tsx              sidebar, top bar, page container
    StatusBadge.tsx        decision and status chips (colors from DESIGN.md)
    DecisionTrace.tsx      ordered audit steps for one payment request
    ApprovalCard.tsx       one pending approval with sign button
    PolicyEditor.tsx       rules form + signed state
    OpsGrid.tsx            thin AG Grid wrapper with shared theme and column helpers
    EmptyState.tsx, ErrorState.tsx, Spinner.tsx
  pages/
    Login.tsx  AgentChat.tsx  Invoices.tsx  Suppliers.tsx
    Payments.tsx  Approvals.tsx  Policy.tsx  Replay.tsx
```

All page and component files exist today as 3 line placeholders, so fill them in place.

## 4. Routes

| Path | Page | Auth |
|---|---|---|
| `/login` | Login | public |
| `/` | AgentChat (home) | required |
| `/policy` | Policy | required |
| `/approvals` | Approvals | required |
| `/payments` | Payments | required |
| `/invoices` | Invoices | required |
| `/suppliers` | Suppliers | required |
| `/replay/:id` | Replay (id is a payment request id) | required |

Auth guard: if `sessionStorage.token` is missing, redirect to `/login`. If any API call returns 401, clear the token and redirect to `/login` with a "Session expired" message.

## 5. API reference

Base URL is `VITE_API_URL`. All endpoints except `/health` and `/auth/login` need `Authorization: Bearer <token>`. Errors are FastAPI style `{"detail": "..."}`, so show `detail` to the user.

### 5.1 LIVE endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | `{ ok: true, paypal_mode: "sandbox" or "fake" }`. Show paypal_mode as a badge in the top bar |
| POST | `/auth/login` | Body `{ email, password }`. Returns `{ token, email }`. 401 `Wrong email or password` |
| GET | `/auth/me` | Returns `{ id, email }`. Use at app start to validate the token |
| GET | `/suppliers` | Array of `{ id, name, paypal_email, verified, last_payout_email, country }` |
| GET | `/invoices` | Array of invoices (shape below) ordered by number |
| GET | `/invoices/{number}` | One invoice, 404 `Invoice not found`. Number is case insensitive |
| POST | `/agent/chat` | Body `{ message }`. Returns `{ reply, payment_request_id?, trace[], mode }` |
| GET | `/payments` | Array of payment requests, newest first |
| GET | `/payments/{pr_id}/trace` | Ordered audit events for one request. 404 if unknown |
| GET | `/transactions` | Array of PayPal payouts, newest first |
| POST | `/transactions/{txn_id}/refresh` | Re-reads PayPal status. Returns `{ id, status }` |

Invoice shape:
```json
{ "id": 1, "number": "INV-001", "supplier": "ABC Supplies", "supplier_verified": true,
  "description": "Office supplies", "amount": 250.0, "currency": "USD",
  "payee_email": "sb-...@personal.example.com", "status": "PENDING" }
```

Agent chat response:
```json
{ "reply": "INV-004 was BLOCKED and no payment was made. Reason: ...",
  "payment_request_id": 12,
  "mode": "rules" ,
  "trace": [ { "tool": "submit_payment_request", "input": { "invoice_number": "INV-004" }, "output": { } } ] }
```
`mode` is one of `rules` (no LLM key), `llm`, or `rules_fallback` (LLM failed, rules took over; the trace then holds an `llm_error` entry). Show `mode` as a small label under the reply.

Payment request shape (`/payments`):
```json
{ "id": 12, "invoice": "INV-004", "amount": 900.0, "decision": "BLOCKED", "risk": "HIGH",
  "reasons": ["Supplier is not verified"], "status": "BLOCKED", "created_at": "2026-10-11T10:00:00" }
```

Transaction shape (`/transactions`):
```json
{ "id": 3, "payment_request_id": 10, "invoice": "INV-001", "payout_batch_id": "ABC123",
  "paypal_txn_id": null, "amount": 250.0, "currency": "USD", "status": "SUCCESS",
  "created_at": "...", "completed_at": "..." }
```

Trace event shape (`/payments/{id}/trace`): `{ id, step, detail, at }`. `step` is a snake_case string such as `truth_check` or `decision`. Render it as a readable label (replace underscores, capitalize) and show `detail` as a collapsible JSON block. Do not hardcode the list of steps, because new steps will appear in Layer 2 and 3.

Enums used in the UI:
- Decision: `AUTO_PAY`, `NEEDS_APPROVAL`, `BLOCKED`
- Risk: `LOW`, `MEDIUM`, `HIGH`
- Invoice status: `PENDING`, `AWAITING_APPROVAL`, `SENT`, `PAID`, `BLOCKED`
- Transaction status: `PENDING`, `SUCCESS`, `DENIED` and other PayPal values. Treat unknown values as neutral chips, never crash

### 5.2 Layer 2 endpoints (LIVE, built and tested)

**Keys**
| Method | Path | Body / Response |
|---|---|---|
| POST | `/auth/register-key` | Body `{ public_key }`: base64 of the SPKI DER public key (`exportKey("spki")`). 400 if it is not a P-256 key. Returns `{ ok: true }`. Registering a different key deactivates the active policy, because its signature no longer matches |

**Policy (mandate)**. Flow: prepare, sign in the browser, activate.
| Method | Path | Body / Response |
|---|---|---|
| POST | `/mandates/prepare` | Body `{ policy_text, rules }`. Needs a registered key. 422 if `valid_until` is past. Saves an inactive mandate and returns `{ mandate_id, payload }`. `payload` is the exact string to sign (it contains a server nonce, so never rebuild it) |
| POST | `/mandates/{id}/sign` | Body `{ signature }` (base64 of the raw 64 byte r\|\|s). Verifies, activates, deactivates older policies. Returns the mandate. 400 `Signature invalid` |
| GET | `/mandates/active` | The active, unexpired mandate or `null`: `{ id, policy_text, rules, payload, signature, active, verified, valid_until }`. `verified` is false when the stored signature no longer matches |
| GET | `/mandates` | History of signed mandates, newest first, same shape |
| GET | `/mandates/{id}/verify` | `{ valid, reason }` |
| POST | `/dev/mandates/{id}/tamper` | Development only (`APP_ENV=development`). Raises the signed auto limit tenfold without re-signing. `verify` then returns `valid: false` and every payment is refused with `Policy signature invalid` |
| POST | `/dev/invoices/{number}` (PATCH) | Development only. Body `{ amount?, payee_email? }`. Changes the live invoice to demo the "changed after evaluation" refusal |

Rules type (matches `schemas.Rules`). Decimals travel as strings in the signed payload, but the form can send numbers:
```ts
type Rules = { auto_limit: number | string; currency: string; monthly_budget: number | string;
               require_verified: boolean; valid_until: string /* ISO date */ };
```
`POST /mandates/draft` (LLM drafting) is NOT built. The Policy page edits the rules form directly. Add a Draft button later without changing the flow.

**Approvals**
| Method | Path | Body / Response |
|---|---|---|
| GET | `/approvals` | Pending: `[{ id, invoice, supplier, amount, currency, risk, reasons[], cart_payload, created_at }]`. `id` is the payment request id. `cart_payload` is the exact string to sign. It holds the payee email, invoice hash and an `expires_at` 24 hours ahead |
| POST | `/approvals/{id}/approve` | Body `{ signature }` over `cart_payload`. 400 `Signature invalid` (the request stays open), 409 if not awaiting or expired. Runs the verifier and the payout. Returns the pipeline summary. A refusal comes back as `status: "BLOCKED"` with the failures in `reasons` |
| POST | `/approvals/{id}/reject` | Body `{ reason? }`. Sets `REJECTED`, returns the summary |

**Payments**
| Method | Path | Body / Response |
|---|---|---|
| POST | `/payments` | Body `{ invoice_number }`. Same pipeline the agent uses. Returns the pipeline summary |
| GET | `/payments/{pr_id}` | Summary plus `supplier`, `currency`, `created_at`. Used by Replay for the header |

Pipeline summary shape: `{ ok, payment_request_id, invoice, amount, decision, risk, reasons[], status, transaction: { id, status, payout_batch_id, paypal_txn_id } | null, note? }`.

Extra statuses the UI must handle: `REJECTED`, `EXPIRED`, `FAILED` (see DESIGN.md 2.4).

**Webhook (not built, not called by the frontend).** `POST /webhooks/paypal` is a stub. Transaction status changes after `Refresh`.

## 6. TypeScript types (`src/lib/types.ts`)

```ts
export type Decision = "AUTO_PAY" | "NEEDS_APPROVAL" | "BLOCKED";
export type Risk = "LOW" | "MEDIUM" | "HIGH";

export interface Supplier { id: number; name: string; paypal_email: string; verified: boolean;
  last_payout_email: string | null; country: string; }

export interface Invoice { id: number; number: string; supplier: string | null;
  supplier_verified: boolean | null; description: string; amount: number; currency: string;
  payee_email: string; status: string; }

export interface PaymentRequest { id: number; invoice: string; amount: number;
  decision: Decision | null; risk: Risk | null; reasons: string[] | null; status: string; created_at: string; }

export interface Transaction { id: number; payment_request_id: number; invoice: string | null;
  payout_batch_id: string | null; paypal_txn_id: string | null; amount: number; currency: string;
  status: string; created_at: string; completed_at: string | null; }

export interface TraceEvent { id: number; step: string; detail: Record<string, unknown>; at: string; }

export interface AgentToolCall { tool: string; input?: Record<string, unknown>; output?: unknown; }
export interface AgentReply { reply: string; payment_request_id?: number | null;
  mode: "rules" | "llm" | "rules_fallback"; trace: AgentToolCall[]; }

export interface Rules { auto_limit: number | string; currency: string; monthly_budget: number | string;
  require_verified: boolean; valid_until: string; }
export interface Mandate { id: number; rules: Rules; policy_text: string; payload: string;
  signature: string | null; valid_until: string | null; active: boolean; verified: boolean; }
export interface ApprovalItem { id: number; invoice: string; supplier: string; amount: number;
  currency: string; reasons: string[]; risk: Risk; created_at: string; cart_payload: string; }
export interface PaymentSummary { ok: boolean; payment_request_id: number; invoice: string; amount: number;
  decision: Decision; risk: Risk; reasons: string[]; status: string; note?: string;
  transaction: { id: number; status: string; payout_batch_id: string | null; paypal_txn_id: string | null } | null; }
```

## 7. Screens: what to build and how

For every screen: layout and look come from DESIGN.md. Below is behavior, data, states and acceptance checks.

### 7.1 Login (`/login`)
- Form: email, password, submit. Prefill nothing in production. In development a hint line can show the demo email.
- On submit call `POST /auth/login`. Store `token` in `sessionStorage`. After success, call `ensureKeypair()` then `POST /auth/register-key` once if the user has no registered key (store a `keyRegistered` flag in `localStorage`).
- States: submitting (disable button), error (show `detail`).
- Accept: wrong password shows "Wrong email or password"; success lands on `/`.

### 7.2 Agent chat (`/`) , home screen
- A conversation column plus a side panel "What the agent did".
- Send message with `POST /agent/chat`. Show user bubble, then the agent `reply`. Keep history in component state only.
- Under each agent reply show: the `mode` label, and if `payment_request_id` is present a "View decision" link to `/replay/{id}`.
- Side panel renders `trace[]` as the list of tool calls (tool name, input, short output). Highlight `submit_payment_request` and show its `decision` as a StatusBadge.
- Starter chips: "Pay INV-001", "Pay INV-003", "Why was INV-004 blocked?", "List invoices".
- Safety: render reply as text. The agent can never trigger a payment from the UI side. State this in a one line note under the input: "The agent can only request payments. A rules engine decides."
- Accept: "Pay INV-005" returns BLOCKED and the panel shows the reasons; "Pay INV-001" returns a paid or sent message.

### 7.3 Invoices (`/invoices`)
- AG Grid with columns: Number, Supplier, Verified (icon), Amount, Status (StatusBadge), Payee email.
- Row click opens a side drawer with full details. The description is shown inside a visibly marked "Untrusted invoice text" box, to teach judges that it is treated as data.
- Button "Request payment" in the drawer calls `POST /payments`.
- Highlight rows whose `payee_email` differs from the supplier's `last_payout_email` (needs a supplier lookup). This is the INV-005 story.
- Accept: five seeded invoices render, filter by status works.

### 7.4 Suppliers (`/suppliers`)
- AG Grid: Name, Country, PayPal email, Verified, Last payout email. Flag a mismatch between `paypal_email` and `last_payout_email`.
- Read only in v1.

### 7.5 Payments (`/payments`)
Two tabs.
- **Requests** (from `/payments`): ID, Invoice, Amount, Decision, Risk, Reasons (first reason plus count), Status, Created. Row action "Replay" goes to `/replay/{id}`.
- **Payouts** (from `/transactions`): Invoice, Amount, Status, Batch id, Completed. Row action "Refresh" calls `POST /transactions/{id}/refresh` and updates the row.
- Add summary cards on top: total paid, awaiting approval, blocked count. Compute them client side from the lists.

### 7.6 Approvals (`/approvals`)
- List of ApprovalCards from `GET /approvals`. Empty state: "Nothing waiting for you."
- Each card shows invoice, supplier, amount, payee email, risk, and every reason in plain words. A collapsible "What you are signing" shows `cart_payload` exactly.
- **Approve** flow: `ensureKeypair()` then `signPayload(cart_payload)` then `POST /approvals/{id}/approve` with the signature. Disable the button while pending. On success show the resulting status and a link to Replay.
- **Reject** flow: optional note, `POST /approvals/{id}/reject`.
- Errors: 400 invalid signature shows "The signature did not verify. Re-register your key". If the browser has no key (IndexedDB cleared), offer "Create new key" which calls `ensureKeypair()` and `POST /auth/register-key`.
- Accept: INV-003 ($1,500) appears here after the agent is asked to pay it, and approving it creates a payout.

### 7.7 Policy (`/policy`)
- Shows the active signed policy (rules in readable form), a **Verified** or **Signature invalid** badge from `verified` on `GET /mandates/active` (or `GET /mandates/{id}/verify`), and valid_until.
- Editor: a rules form pre-filled with the current policy. (A plain language Draft button via `POST /mandates/draft` is optional and not built yet.) The form holds (auto limit, monthly budget, require verified suppliers, valid until). The owner can edit every field.
- **Review and sign** shows a diff against the current policy, calls `POST /mandates/prepare`, signs the returned `payload` with the browser key and calls `POST /mandates/{id}/sign`.
- The AI-drafted values are labeled "Drafted by AI, not active until you sign".
- Tamper demo (development and demo builds only): button "Simulate tampering" calls `POST /dev/mandates/{id}/tamper`, then the page reloads the verify badge, which flips to invalid, and a banner states that all payments are now stopped until the owner signs a new policy.
- Accept: sign, refresh, badge stays valid; tamper turns the badge invalid; paying any invoice is then refused.

### 7.8 Replay (`/replay/:id`)
- Header from `GET /payments/{id}` (or from the list as a fallback): invoice, amount, decision badge, risk, status.
- Body: `DecisionTrace` , a vertical timeline of `GET /payments/{id}/trace`. Each step shows label, time, a pass or fail style when `detail` has a recognisable result, and an expandable raw JSON.
- A "Copy as JSON" button for the whole trace, useful for the demo and for judges.
- Accept: INV-005 shows the truth check failing on the changed payee email and the injected text, and ends at BLOCKED with no payout step.

## 8. Signing, step by step (`src/lib/crypto.ts`)

The server builds the exact string. The browser signs that string unchanged. Never rebuild or reformat the payload in the browser.

```ts
import { get, set } from "idb-keyval";

export async function ensureKeypair(): Promise<CryptoKeyPair> {
  const existing = await get("paypilot-keypair");
  if (existing) return existing;
  const pair = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, false, ["sign", "verify"]);
  await set("paypilot-keypair", pair);
  return pair;
}

export async function exportPublicKey(pair: CryptoKeyPair): Promise<string> {
  const spki = await crypto.subtle.exportKey("spki", pair.publicKey);   // the server loads SPKI DER only
  return btoa(String.fromCharCode(...new Uint8Array(spki)));
}

export async function signPayload(payload: string): Promise<string> {
  const pair = await ensureKeypair();
  const sig = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, pair.privateKey,
                                       new TextEncoder().encode(payload));
  return btoa(String.fromCharCode(...new Uint8Array(sig)));   // 64 bytes raw r||s, base64
}
```

Notes for the implementer:
- WebCrypto returns raw 64 byte r||s. The Python side converts it to DER with `encode_dss_signature`. The frontend sends the raw value in base64 and does nothing else.
- The private key is created with `extractable: false`, so even our own code cannot read it. If IndexedDB is cleared, a new key must be registered and older pending approvals cannot be signed with it.
- Signing requires a secure context: HTTPS in production, `localhost` in development. This is one more reason the VPS uses HTTPS.
- `crypto.subtle` is undefined on plain HTTP. Detect it and show a clear error.

## 9. API client (`src/lib/api.ts`) changes

The current helper throws `Error("401 {...}")`. Replace with:
- An `ApiError` class holding `status` and `detail` (parse `{ detail }` from the body).
- A 401 handler: clear `sessionStorage.token` and navigate to `/login`.
- A typed signature: `api<T>(path, options): Promise<T>`.
- `Content-Type: application/json` only when a body exists.

## 10. Shared UI pieces

- **StatusBadge**: one component for decisions, risk, invoice status and transaction status. Maps value to color token from DESIGN.md, with unknown values falling back to neutral. Always pairs color with text (never color alone).
- **OpsGrid**: wraps AG Grid with the shared theme, default column behavior (sortable, resizable), a "no rows" overlay, and a loading overlay. Import AG Grid CSS once in `main.tsx`.
- **Shell**: sidebar with the eight destinations, top bar with the `paypal_mode` badge ("Sandbox" or "Fake"), the user email and a Sign out button. A pending approvals count badge on the Approvals link (poll `/approvals` every 30 seconds).

## 11. Accessibility and quality bar

- Keyboard reachable controls, visible focus ring, labels on every input.
- Contrast meets WCAG AA. Check badge colors in both states.
- Responsive down to a laptop width of 1024px as the main target; tablet is nice to have. Judges will use a laptop.
- No console errors in the demo path.
- Every async button shows a pending state and cannot be double clicked into two payments.

## 12. Build order (maps to the project gates)

1. Foundation: Tailwind, `api.ts` with ApiError, `types.ts`, Shell, auth guard, Login. (Day 1)
2. Read only screens on LIVE endpoints: Invoices, Suppliers, Payments (both tabs), Replay. (Days 2 to 3)
3. Agent chat with the trace side panel. (Day 3)
4. Layer 2 UI against mock data: Policy and Approvals with `crypto.ts`. Swap mocks for the real endpoints when the backend lands, before the 24 Oct gate.
5. Polish pass using DESIGN.md: empty and error states, responsive checks, demo data path.
6. Feature freeze on 3 Nov: only bug fixes after that.

Suggested split: Alain takes steps 1, 2 and 5. Elthiero takes the Layer 2 backend and steps 3 and 4. The contracts above are live, so both sides can work in parallel.

## 13. Demo path the UI must support end to end

1. Log in. 2. Policy page: sign a policy (limit 500, budget 5000). 3. Chat "Pay INV-001": AUTO_PAY, paid. 4. Chat "Pay INV-003": needs approval, go to Approvals, sign, payout sent. 5. Chat "Pay INV-005": BLOCKED, open Replay to show the changed payee email and the injected text ignored. 6. Policy page: Simulate tampering, the badge turns invalid, paying is refused.

## 14. Acceptance checklist

- [ ] All eight routes render with loading, empty, error and data states.
- [ ] Token expiry sends the user to `/login`.
- [ ] No page calls `fetch` directly.
- [ ] Signing works on `localhost` and on HTTPS, and shows a clear message on plain HTTP.
- [ ] The base path works at `/` and at `/paypilot/` with deep links such as `/paypilot/approvals`.
- [ ] `npm run build` passes (CI runs it).
- [ ] The demo path in section 13 runs without console errors.

## 15. Open items

- DESIGN.md (visual language) is written after the reference images are provided.
- `POST /mandates/draft` (plain language policy drafting) is not built.
- Decide whether `/mandates/draft` uses the LLM or a rule parser first (the LLM is optional, the rule parser is the fallback).
