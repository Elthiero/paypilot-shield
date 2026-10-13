# Demo script (under 3 minutes)

The rules: under 3 minutes, public on YouTube, shows the project working, no third-party trademarks and no copyrighted music. Aim for 2:45 so there is margin. Judges are not required to watch past 3:00.

## Before you record (pre-flight)

1. On the server run `docker compose exec backend python seed.py`. It wipes the data and resets the five demo invoices. Do it right before recording, not before rehearsals.
2. Open the live site in a fresh Chrome window at 1920x1080 (or 1440x900), zoom 110%. Hide the bookmarks bar and extensions. Turn off autofill suggestions and notifications.
3. The policy form starts with an auto limit of 500 and a monthly budget of 5000, which is what the demo needs. The "Policy in plain words" box is only a note stored with the policy, it does not set the limits.
4. Sign in once. The policy is empty after a re-seed, so the first thing on camera is signing it.
5. Rehearse twice with `Pay INV-002`, `Pay INV-003` and `Pay INV-005`, then re-seed again before the real take. Each invoice can only be paid once.
6. Do not show the PayPal dashboard or logo. Show the app's own Payments and Replay pages, which prove the same thing.
7. Record with OBS or the desktop recorder, one mic, no music. Export MP4 and upload as **Public** (not unlisted) on YouTube. Paste the link in the Devpost form.

The AI replies take about 5 to 15 seconds (Groq, three tool calls). Talk through the wait, or cut it in editing. Do not speed up the screen with the signing modal.

## Script

| Time | Show | Say |
|------|------|-----|
| 0:00 to 0:15 | Login page, then sign in | Invoice fraud costs businesses billions. If an AI agent pays your invoices, how do you stop it being tricked? This is PayPilot Shield, running on the PayPal sandbox. |
| 0:15 to 0:40 | **Policy**: check the auto limit is 500 and the monthly budget 5000, Review and sign, Sign policy | The owner sets the rules and signs them in the browser. The key never leaves the browser, and nothing is paid without this signature. |
| 0:40 to 1:10 | **Agent**: "Pay INV-002". Show the decision card: AUTO_PAY, low risk | The agent can only ask for a payment. A rules engine decides, not the AI. This one is inside the policy and every check passed, so a payout goes to PayPal. |
| 1:10 to 1:25 | **Payments**: the payout shows sent, then paid | PayPal confirms it with a signed webhook, and we read the status back from PayPal before we trust it. |
| 1:25 to 1:55 | **Agent**: "Pay INV-003" (needs approval). Go to **Approvals**, Review and sign | $1,500 is above the auto limit. A human signs the exact payment. The signature is checked again just before PayPal is called. |
| 1:55 to 2:25 | **Agent**: "Pay INV-005" (blocked). Open the **Replay** | The payee email changed and the invoice text contains instructions aimed at the payer. Two reasons, blocked, and PayPal was never contacted. Every step is replayable. |
| 2:25 to 2:40 | Replay steps: verifier, payout, `webhook_received`, `payout_confirmed` | The audit log shows each decision, including the webhook that confirmed the first payment. |
| 2:40 to 2:50 | Policy page or title card with the URL | PayPilot Shield. The model proposes, deterministic code decides, you sign. paypilot.donambi.dev |

## The tamper test

The "Simulate tampering" button only exists when the backend runs with `APP_ENV=development`, so the live site does not have it. Two options:

- **Skip it** and say "tampered policies are refused by the verifier" over the Replay. This is the safe choice for a 3 minute video.
- **Record it from a local run** (`APP_ENV=development`, fake or sandbox PayPal) and cut it in as a 10 second clip after the INV-005 block: press Simulate tampering, the badge turns "signature invalid", and the agent refuses to pay.

## Backup plan

- If the AI reply fails and shows `rules_fallback`, the demo still works. Re-record that take or keep going, since the decision is the same.
- If an invoice is already paid, press **New invoice** and create one under $500 for an existing supplier.
- If the policy shows "signature invalid" after signing in from another browser, sign it again.
