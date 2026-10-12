# Security

What protects the money, what was hardened in the review of 12 Oct, and what is still open.

## Model

- The agent can only request a payment. A rules engine decides, and the owner signs policy and approvals in the browser with a non-extractable ECDSA P-256 key (see [layer2.md](layer2.md)).
- Right before PayPal is called the verifier re-checks the signed policy, the invoice against its frozen snapshot, the budget and a replay guard. Any failure means no PayPal call.
- Layer 3 signals can only raise risk (see [layer3.md](layer3.md)).

## Hardening in place

| Area | What |
|---|---|
| Environment | `APP_ENV` defaults to `production`. The `/dev` tamper routes are mounted only with `APP_ENV=development`. Outside development the API refuses to start unless `JWT_SECRET` has at least 32 characters and `DEMO_PASSWORD` at least 12 (not the defaults) |
| Double payment | Approving a request and evaluating an invoice each claim their row atomically (`UPDATE ... WHERE status = ...`). The PayPal batch id is `pp{request id}-{request creation time}`: the same for every attempt on one request, so PayPal refuses a second batch for it, and still unique after `seed.py` restarts ids at 1 |
| Signing key | Replacing a registered key needs the password (`POST /auth/register-key` returns 403 otherwise). A stolen login token alone cannot take over signing |
| Login | 5 failed attempts in 5 minutes per client IP and email returns 429. Bcrypt runs for unknown emails too, so timing does not reveal which emails exist |
| Input limits | Chat and policy text 2000 characters, size limits on login, key, signature and reject fields, currency `[A-Z]{3}`, policy valid for at most 366 days, old unsigned drafts are deleted on each prepare |
| Proxy headers | nginx sets `X-Forwarded-For` to the real client address (overwrites, never appends). uvicorn trusts forwarded headers only from the compose subnet (`FORWARDED_ALLOW_IPS=172.28.0.0/24`). Port 8000 is not published |
| Container | The backend image runs as a non-root user |
| Secrets | `.env` is gitignored and was never committed. `.env.example` holds placeholders only |

Tests: `backend/tests/test_security.py`.

## Known gaps

- Security headers beyond the basics in `frontend/nginx.conf`, and a Content-Security-Policy. The login token is in `sessionStorage`, so an XSS bug would expose it.
- Dependencies are not pinned and `python-jose` could be replaced by PyJWT. Add `pip-audit` to CI.
- The monthly budget check is not atomic: two parallel auto-pays on different invoices could overshoot it slightly.
- The login limiter is in memory and per process. It resets on restart. Use Redis or the database if the API runs on several workers.
- All data endpoints are single tenant. Approvals and payments are not scoped to a user, so multi-user roles would need that first.
- Replacing the signing key asks for the password with `window.prompt`, which shows the text on screen.
- The PayPal webhook is not built. When it is: verify PayPal's signature before trusting the body, and make the handler idempotent.
- Behind a second proxy (host nginx with TLS): `frontend/nginx.conf` trusts `X-Forwarded-For` from the compose subnet `172.28.0.0/24` only. The host nginx must send `proxy_set_header X-Forwarded-For $remote_addr;`. Check the subnet with `docker network inspect` and adjust `set_real_ip_from` if it differs.
