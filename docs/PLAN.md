# PayPilot Shield: Team Plan

Put this file at `docs/PLAN.md`. Update the checkboxes in your pull requests.

**Team:** Elthiero (backend, integrations, deploy) and Alain (frontend). Both share docs, demo and submission.
**Deadline:** Devpost closes Thu 12 Nov 2026, 12:00 PST (22:00 Kigali). **Our submit target: Tue 10 Nov.** Keep 2 days of slack.
**Today:** Mon 12 Oct. That is 29 days to the target.

## 1. Where we are

| Area | Status |
|---|---|
| Layer 1 core (login, invoices, pipeline, agent with rules fallback, real sandbox payout, audit log) | Done, tag `v0.1-core` |
| Layer 2 trust (signed policy, signed approvals, verifier, tamper test) | Done, tag `v0.2-trust` |
| Layer 3 detection (extra fraud signals, structured reasons) | Done, tag `v0.3-detection`. LLM classifier not built |
| Frontend (Layer 4) | All 8 pages built and calling the real API, plus New invoice form, vendor history and a total paid chart. Base path deep link tested (see `docs/layer4.md`). Polish checks (four states, reduced motion) still open |
| Docs | FRONTEND.md and DESIGN.md written. Design preview approved |
| Webhook | Not built (stub). The manual Refresh button covers it |
| Deploy | **Live** at https://paypilot.donambi.dev (served at the root, `/api` proxied, HTTPS, sandbox PayPal, demo tools off). `ci.yml` runs tests, `pip-audit` and the frontend build. No automatic deploy workflow, deploys are manual |
| Security | Review of 12 Oct done and fixed, see `docs/security.md` for the open items |

## 2. Gates (dates that must hold)

| Date | Gate | Pass condition |
|---|---|---|
| Sun 18 Oct | **Contract freeze** | Frontend can build every screen against mock data. Planned endpoints are agreed in FRONTEND.md |
| Sat 24 Oct | **Layer 2 gate** | Sign policy in the browser, approve a payment by signature, tamper test stops payments |
| Sat 31 Oct | **Integration gate** | Whole demo path (section 7) runs end to end on a real URL |
| Tue 3 Nov | **Feature freeze** | Only bug fixes after this day |
| Sat 7 Nov | **Demo ready** | Video recorded, README final, Devpost text drafted |
| Tue 10 Nov | **Submit** | Submitted and the submission page opened and checked |

If a gate slips by more than 2 days, cut scope using section 8, do not push the freeze.

## 3. Ownership

| Area | Owner | Reviewer |
|---|---|---|
| `backend/`, `scripts/`, deploy files | Elthiero | Alain |
| `frontend/` | Alain | Elthiero |
| `docs/FRONTEND.md` API contract section | Elthiero proposes, both agree | Both |
| `docs/DESIGN.md` | Alain | Elthiero |
| README, demo script, Devpost text | Shared, Elthiero drives | Alain |

Set this in `.github/CODEOWNERS`:
```
/backend/   @Elthiero
/frontend/  @alaingaye
/docs/      @Elthiero @alaingaye
```

## 4. How we work together

- **Branches:** `be/<topic>` for backend, `fe/<topic>` for frontend. One topic per branch, small pull requests, merged within 1 day.
- **Main is protected:** pull request required, CI green, one review from the other person (a quick look is enough, do not block each other for more than a few hours).
- **API contract rule:** the contract is section 5 of FRONTEND.md. A change to a response shape is made in a pull request to that file first, then code follows. Backend never changes a shape silently.
- **Mock first:** Alain builds against mocks (`VITE_USE_MOCKS=true`, a mock layer inside `api.ts` that returns the shapes from FRONTEND.md). When a backend endpoint lands, flip that one endpoint to real.
- **Backend for Alain locally:** no Postgres needed. Run `cd backend && PAYPAL_MODE=fake uvicorn app.main:app --reload` (SQLite by default) and run `python seed.py`. Fake mode never calls PayPal.
- **Secrets:** `.env` never committed. PayPal and LLM keys stay with Elthiero. Alain does not need them.
- **Claude Code:** each person works with their own Claude Code session. `CLAUDE.md` holds the shared rules (golden rule, tests must pass, no dashes). Tell it to read the relevant doc first (FRONTEND.md and DESIGN.md for Alain, FRONTEND.md section 5 for Elthiero).
- **Sync:** a 15 minute call or message thread each day: what I finished, what I do next, what blocks me. A short weekly review every Sunday against the gates.

## 5. Week by week

### Week 1: Sun 11 to Sat 17 Oct (foundation)

**Elthiero (backend)**
- [ ] Housekeeping: replace seed emails with the US sandbox personal accounts, reset the password in the setup SQL, add CODEOWNERS, protect `main`, invite Alain
- [x] OpenAI compatible LLM support (Grok or Groq) with the rules fallback kept
- [x] `POST /payments` and `GET /payments/{id}` (small additions, section 5.2 of FRONTEND.md)
- [ ] CORS and `VITE_API_URL` confirmed for local dev
- [x] Tag `v0.1-core`
- [x] Draft the Layer 2 design note (mandate payload format, signature check) in `docs/devlog.md`

**Alain (frontend)**
- [ ] Clone, run backend locally in fake mode, log in via curl to confirm it works
- [ ] Tailwind, fonts, tokens, global ruled paper background, `lucide-react`
- [x] `api.ts` with `ApiError`, 401 handling, mock layer, `types.ts`
- [x] Shell (top nav), StatusBadge, EmptyState, ErrorState, Spinner, auth guard
- [x] Login page
- [x] Agent screen (chat, step blocks, decision card) against the real `/agent/chat`

**Handoff by Sat 17 Oct:** `POST /payments` live. Alain's Login and Agent screens work against the real backend.

### Week 2: Sun 18 to Sat 24 Oct (Layer 2, the 24 Oct gate)

**Elthiero (backend)**
- [x] `POST /auth/register-key` (renamed from `/auth/public-key`; store the user's JWK public key)
- [x] Mandate service: build the exact payload string from rules, store, verify ECDSA P-256 signature (raw r||s to DER with `encode_dss_signature`)
- [x] `/mandates`: `GET /current`, `POST /draft` (rule parser first, LLM optional), `POST /` (verify and activate), `GET /` (history), `GET /{id}/verify`
- [x] Pipeline reads the active signed mandate instead of defaults. No valid mandate means no payment (BLOCKED, reason "No valid signed policy")
- [x] `/approvals`: `GET /`, `POST /{id}/approve` (verify signature over `cart_payload`, then execute payout), `POST /{id}/reject`
- [x] Tamper endpoint (non production) and the tamper test in pytest
- [x] Tests for: valid signature, wrong signature, modified payload, expired mandate, replayed approval
- [x] Post the finished contract (any changes) to FRONTEND.md by Wed 21 Oct

**Alain (frontend)**
- [x] Invoices (grid, drawer, request payment), Suppliers, Payments (stat cards, two tabs), Replay (trace timeline)
- [x] `crypto.ts`: keypair, export public key, sign, secure context check
- [x] Signing modal component (ceremony, sealed state)
- [x] Policy and Approvals pages against mocks first, then real endpoints as they land
- [x] Register the public key after first login

**Gate Sat 24 Oct:** sign a policy in the browser, approve INV-003 by signature, tamper turns the badge invalid and payments stop.

### Week 3: Sun 25 Oct to Sat 31 Oct (integration and detection)

**Elthiero (backend)**
- [x] Layer 3 signals (keep small): duplicate invoice, amount outlier vs supplier history, new payee email, round amount pattern, prompt injection phrases. Each adds a reason to the audit log
- [ ] PayPal webhook endpoint with signature verification (`PAYPAL_WEBHOOK_ID`), idempotent handling
- [x] Deploy to the VPS: `docker-compose.yml`, Postgres via `DATABASE_URL`, HTTPS. Live at https://paypilot.donambi.dev (root path, so `/paypilot/` is not used in production)
- [ ] Deploy workflow (deploys are manual today)
- [x] Seed and reset script for demo data (`python seed.py` wipes and reseeds, no `--reset` flag)

**Alain (frontend)**
- [x] Wire every screen to real endpoints, remove unused mocks
- [x] Base path support (`VITE_BASE=/paypilot/`, router basename, API follows the base) and test at `/paypilot/approvals` deep link (see `docs/layer4.md`)
- [ ] All four states on every page, keyboard path, reduced motion
- [x] Tamper banner and the Demo tools card
- [x] Production build served by nginx (the `frontend` container, live)

**Gate Sat 31 Oct:** full demo path on the live URL. Deployed since 12 Oct; the full demo path on the live URL still has to be run and timed.

### Week 4: Sun 1 to Sat 7 Nov (freeze, polish, demo)

- [ ] **Tue 3 Nov: feature freeze.** Bug fixes only
- [ ] Both: bug bash on the live URL, one person drives the demo path while the other watches for errors (console and server logs)
- [ ] Elthiero: backend hardening (rate limit on login, error messages, health checks), final test run, README setup instructions verified from a clean clone
- [ ] Alain: visual polish pass against the design preview, responsive check at 1440 and 1024, login screen
- [ ] Both: demo script (`docs/demo-script.md`), record the video (script first, 2 takes), screenshots in `docs/screenshots/`
- [ ] Both: Devpost text draft: problem, what it does, how we built it (golden rule), challenges, what is next. Read the official rules page again for required items (video length, repo link, test account or demo access)

### Final days: Sun 8 to Tue 10 Nov (submit)

- [ ] Sun 8: freeze the demo data and the video. Fix only blockers
- [ ] Mon 9: a person who has not touched the project runs the README and the live demo, fix what they hit
- [ ] Tue 10: submit in the morning Kigali time. Open the submission page, check the video plays, links work, repo is public, no secrets in history
- [ ] Wed 11 and Thu 12 (until 22:00 Kigali): only fixes to the Devpost page if something is wrong

## 6. Backend task detail (Elthiero)

| Order | Task | Files | Done when |
|---|---|---|---|
| 1 | Housekeeping and CODEOWNERS | `seed.py`, `scripts/`, `.github/` | Seed uses real sandbox emails |
| 2 | LLM provider switch | `config.py`, `services/agent.py`, `requirements.txt`, test | 19 tests pass, `mode: "llm"` live |
| 3 | `POST /payments`, `GET /payments/{id}` | `routers/payments.py` | Invoices page can request a payment |
| 4 | Public key | `routers/auth.py`, `models.py` | JWK stored for the user |
| 5 | Mandate payload and verify | `services/mandate.py`, `services/verifier.py` | Unit tests for good and bad signatures |
| 6 | Mandate endpoints | `routers/mandates.py` | Sign, activate, verify, history |
| 7 | Pipeline uses the signed mandate | `services/pipeline.py`, `decision.py` | No valid mandate means BLOCKED |
| 8 | Approvals | `routers/approvals.py` | Approve by signature creates a payout |
| 9 | Tamper and tests | `routers/mandates.py`, `tests/` | Tamper test passes in CI |
| 10 | Layer 3 signals | `services/truth_check.py` | Reasons show in the trace |
| 11 | Webhook | `routers/webhooks.py` | Status updates after PayPal events |
| 12 | VPS deploy | `docker-compose.yml`, nginx, workflow | Live HTTPS URL |

## 7. Demo path (what everything serves)

1. Log in.
2. Policy: write "Auto pay up to 500, budget 5000 a month", Draft, review, sign.
3. Agent: "Pay INV-001". AUTO_PAY, paid through PayPal sandbox.
4. Agent: "Pay INV-003" ($1,500). NEEDS_APPROVAL. Approvals: review, sign, payout sent.
5. Agent: "Pay INV-005". BLOCKED (changed payee email and injected text). Replay shows each step.
6. Policy: Simulate tampering. Signature invalid. Paying is refused until a new signed policy.

Rehearse this path every Friday starting 23 Oct, and record how long it takes (target under 3 minutes).

## 8. Scope cuts (in this order, if time runs short)

1. Layer 3 signals beyond duplicate invoice and new payee email
2. LLM drafting of the policy (keep the rule parser)
3. PayPal webhook (keep the manual Refresh button)
4. Suppliers page (read only list is enough)
5. VPS deploy (run locally and record the demo from there)

**Never cut:** the signed policy, the signed approval, the tamper test, the audit replay, the BLOCKED demo. They are the product.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Signature mismatch between browser and Python (raw vs DER, string differences) | Server builds the payload, browser signs it unchanged, write the cross check test first (Week 2, day 1) |
| PayPal sandbox slow or down on demo day | Fake mode fallback, recorded video as backup, show Replay from stored data |
| Backend and frontend drift | Contract rule in section 4, mocks, contract freeze on 18 Oct |
| VPS problems late | Deploy early (Week 3), record the video from a local run as backup |
| LLM provider rate limit or outage | Rules fallback already built and tested |
| One person blocked | Daily sync, small pull requests, the other person unblocks the same day |
| Scope creep | Feature freeze 3 Nov, cuts list in section 8 |

## 10. Definition of done (any task)

- [ ] Code merged to `main` through a pull request with CI green
- [ ] Tests added for new backend logic, `npm run build` passes for frontend
- [ ] Contract and docs updated if a shape or screen changed
- [ ] No secrets, no em or en dashes in text
- [ ] Works on the live URL (after Week 3)

## 11. This week's first five actions

1. Elthiero: merge the housekeeping branch, invite Alain, protect `main`.
2. Alain: accept the invite, clone, run the backend in fake mode, open `/docs` (Swagger) to see the live endpoints.
3. Both: agree the PLANNED endpoint contract in FRONTEND.md section 5.2 (comment in a pull request, 30 minutes).
4. Alain: start the foundation branch `fe/foundation` (Tailwind, tokens, Shell, api.ts).
5. Elthiero: start `be/payments-endpoint`, then `be/llm-provider`.
