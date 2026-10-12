# Layer 4: presentation

Layer 4 is the React app. It decides nothing. It shows what the backend decided and it is where the owner signs. Design rules are in [DESIGN.md](DESIGN.md), the API contract is in [FRONTEND.md](FRONTEND.md), screenshots are in `docs/screenshots/`.

Stack: React, Vite, TypeScript, Tailwind, AG Grid, lucide-react, WebCrypto (`idb-keyval` for the key).

## Pages

| Route | What it does |
|---|---|
| `/login` | Sign in. After login the browser registers its public key |
| `/` Agent | Chat with the agent, a decision card, and the list of tool calls the agent made |
| `/invoices`, `/suppliers` | Grids with a drawer. Invoices has "request payment" |
| `/payments` | Stat cards, a Requests tab (with Requested time) and a Payouts tab (Sent, Completed, Duration). Pending payouts refresh themselves |
| `/policy` | Write the rules, review, sign. Shows the active policy with a Verified or Signature invalid badge, history, and demo tools |
| `/approvals` | Payments waiting for the owner. Review and sign the exact cart |
| `/replay/:id` | Every step of one payment with times, offsets from the first step and the total time |

A pink banner shows on every page while the active policy fails verification, a yellow one while there is no policy.

## How it talks to the backend

- `src/lib/api.ts` calls `${BASE_URL}api` (so `/api` at the root and `/paypilot/api` under `/paypilot/`), unless `VITE_API_URL` is set. In Docker, nginx proxies `/api` to the backend.
- The login token is kept in `sessionStorage`. A 401 sends the user back to the login page.
- `src/lib/crypto.ts` creates a non-extractable ECDSA P-256 key in IndexedDB. The server builds the string to sign and the browser signs it unchanged. Replacing a key the server already knows needs the password.
- `src/hooks/useHealth.ts` reads `/health` once per page load. It gives the PayPal mode chip in the header (`paypal_mode`) and decides whether the demo tools are shown (`dev_tools`).

## Demo tools

The "Simulate tampering" button on the Policy page appears only when `/health` says `dev_tools: true`, which is true only when the backend runs with `APP_ENV=development`. That is exactly when the `/dev` routes it calls exist. There is no build flag, so a Docker image built once behaves correctly in both cases.

## Agent chat

With no `LLM_API_KEY` the rule matcher answers (header label "rules"). With a key the LLM answers ("AI mode"). Either way the agent can only request payments.

| You type | Rules matcher does |
|---|---|
| `Pay INV-001`, `pay invoice 4`, `pay inv #4` | Submits that invoice to the pipeline |
| `Why INV-004?` | Explains the stored decision and steps |
| `list invoices`, `show pending`, `which are blocked?` | Lists invoices, filtered by a status word (pending, paid, sent, blocked, awaiting, failed, rejected) |
| `pay all pending` | Submits each pending invoice, at most 10, one by one. Each gets its own full decision. One line per invoice in the reply |

The LLM tool `list_invoices` takes the same optional `status`.

## Live payout status

While any payout is `PENDING` the Payments page calls `POST /transactions/{id}/refresh` for each one every 5 seconds (not while the tab is hidden), then reloads. After about 2 minutes it stops and the manual Refresh button remains. A note above the grid says it is checking.

## Base path

`VITE_BASE=/paypilot/ docker compose build frontend` builds for `/paypilot/`. The frontend container serves the files at its own root, so the host nginx must strip the prefix: `location /paypilot/ { proxy_pass http://frontend:80/; }`. Router basename, assets and API calls all follow `BASE_URL`.

## Accessibility

Focus ring on every control, `prefers-reduced-motion` respected, color is never the only signal (icon and text on every badge), modals take focus and close with Escape.

## Verified on 12 Oct

Run in a scratch Playwright script against the Docker stack with the fake PayPal client (not part of CI):

- Keyboard only: login (Tab, type, Enter), open the signing modal with Enter, close it with Escape. Focus moves into the modal.
- Demo tools button appears from `/health` with no build flag.
- Under `/paypilot/`: login, the `/paypilot/approvals` deep link and a reload on it, every API call went to `/paypilot/api/`, no failed requests.
- Payout polling: with a mocked `PENDING` payout the page called refresh, showed `SUCCESS` without a click, and removed the note.

The full demo path also ran once on the real PayPal sandbox (see `docs/devlog.md`, 12 Oct): two payouts sent and confirmed, two blocked, tamper refused. The Duration column shows the time until the app saw `SUCCESS`, which includes the wait for the next refresh, not PayPal's own processing time.

Backend tests cover the matcher, status filter, "pay all pending" and `/health` (`tests/test_agent_rules.py`, `tests/test_api.py`).

## Known gaps

- No automated frontend tests and no browser tests in CI. The Playwright script above is manual.
- Loading, empty and error states come from the shared `OpsGrid`, `Spinner`, `EmptyState` and `ErrorState`. I did not check every page by hand for all four states.
- Adding invoices from the UI is not built (`POST /invoices` does not exist, invoices come from `seed.py`).
- Replacing the signing key uses `window.prompt`, which shows the password on screen.
- Responsive check at 1024 px and the final visual polish pass are still open.
