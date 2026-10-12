# Devpost text (draft)

Paste each block into the matching Devpost field. Placeholders in [brackets] must be filled in before submitting. Do not commit the real password.

## Tagline

An AI agent that pays supplier invoices through PayPal, but only inside a spending policy you signed, and only after every invoice passes a truth check.

## Inspiration

Business email compromise and fake invoices cost companies billions every year. A changed bank detail, a look-alike supplier, a line hidden in an invoice. Putting an AI agent in charge of paying invoices makes this worse, because the agent can be tricked in exactly the same ways. We wanted to see what it takes to let an agent do the work without letting it hold the money.

## What it does

PayPilot Shield lets a business owner say "Pay INV-001" in a chat. The agent finds the invoice and asks for the payment. It never moves money itself. A deterministic rules engine decides one of three outcomes:

- **AUTO_PAY:** inside the owner's signed policy and every check passed. The payout is sent through the PayPal Payouts API.
- **NEEDS_APPROVAL:** for example, above the auto limit. The owner reviews the exact payment and approves it with a cryptographic signature.
- **BLOCKED:** a check failed. No PayPal call is made, and the reasons are shown in plain words.

What makes it trustworthy:

- **The owner signs the policy.** The spending limit, the monthly budget and the "verified suppliers only" rule are signed in the browser with a non-extractable ECDSA P-256 key. The key never leaves the browser. No valid signature means no payment.
- **Truth checks on every invoice:** unverified supplier, changed payee email, duplicate invoice, amount outlier against the supplier's history, new payee, round-amount pattern, and prompt-injection text hidden inside the invoice.
- **A last gate inside the payout code.** Just before PayPal is called, the signature and the invoice are verified again, so no code path can skip the rules. A tampered policy is refused.
- **Replayable audit log.** Every step of every decision is stored and can be replayed on screen: invoice loaded, history checked, truth check, decision, verifier, payout.
- **Real PayPal events.** PayPal's webhook is verified with PayPal's own signature check and settles the payout. The status is read back from PayPal, never trusted from the message.

## How we built it

- **Backend:** FastAPI, SQLAlchemy and PostgreSQL. PayPal Payouts sandbox for payouts, and PayPal webhooks with signature verification for confirmation.
- **AI:** Groq (qwen/qwen3.8-27b at the time of writing) through an OpenAI compatible client. The agent has no tool that moves money. Its only way to ask for a payment is `submit_payment_request`. If the model fails, a rules matcher takes over, so the product keeps working.
- **Frontend:** React, Vite, TypeScript and Tailwind. AG Grid powers the Payments, Invoices and Suppliers screens. The WebCrypto API does the signing.
- **Deploy:** Docker Compose with nginx, HTTPS, and security headers including a content security policy.
- **Quality:** about 80 automated tests, including forged webhook signatures, replayed approvals, tampered policies and a race on the monthly budget (an advisory lock keeps two payouts from overspending it). CI runs the tests, a dependency audit and the frontend build.
- **Claude Code** was our pair programmer for most of the code, tests and documentation.

The golden rule we built around: **the model proposes, deterministic code decides.** AI can raise a request's risk level but can never lower it, and invoice text is treated as untrusted data.

## Challenges we ran into

- **A payout is not instant.** In the sandbox a payout stays pending for about 35 seconds. We first polled PayPal in a loop, which made the agent feel slow and never caught the result. The verified webhook solved both.
- **Idempotency.** PayPal refuses a repeated batch id, which protects against double payments but broke us after a database reset. The id now carries a creation time.
- **Sandbox quirks.** Sandbox accounts in our country were refused for Payouts, while US accounts worked.
- **Models are different.** One model sent `null` for an optional field and the provider rejected the whole call. We changed the tool schema and added a test.
- **Prompt injection.** Invoice text can contain "ignore previous policy". The rules engine scans every text field and blocks it, and the AI cannot override that block.

## Accomplishments we're proud of

- An agent that is safe by construction, not by prompting: removing the money tool and keeping the decision in plain code.
- A signed-policy and signed-approval flow that works entirely in the browser, with a tamper test that stops payments.
- A real end-to-end run on the live site: AUTO_PAY paid, an over-limit invoice approved by signature and paid, and a fake invoice with a changed payee email and injected instructions blocked, all visible in the replay.

## What we learned

Letting an agent act with money is mostly an authorization problem, not an AI problem. Signed intent, a gate at the point of payment, and an audit trail you can replay matter more than the model.

## What's next

An LLM-based fraud classifier whose output can only raise risk, fraud thresholds inside the signed policy, adding and verifying suppliers with an owner signature, dispute handling, and multi-user roles.

## Built with

Python, FastAPI, SQLAlchemy, PostgreSQL, PayPal Payouts API (sandbox), PayPal webhooks, Groq, React, TypeScript, Vite, Tailwind CSS, AG Grid, WebCrypto, Docker, nginx, Claude Code

## Tools used and how (for the "tools" field)

- **PayPal Developer Platform (sandbox):** Payouts API to pay suppliers, OAuth for access, and webhooks verified with `verify-webhook-signature` to confirm payouts.
- **Groq (qwen/qwen3.8-27b):** the agent that reads the owner's request, looks up invoices and asks for payments through one tool. It explains the outcome in plain words.
- **AG Grid:** the operations grids for payments, payouts, invoices and suppliers.
- **Claude Code:** AI-assisted development of the code, tests and docs.

## How the project was updated during the hackathon

The project was started on 11 October 2026, after the submission period opened on 1 October, so all of it was built during the hackathon. Work landed in four layers: the core pipeline and the PayPal payout, the signed policy and approvals, the extra fraud signals, and the full web interface and deployment. Since then we added the PayPal webhook with signature verification, a privacy page, security hardening and performance fixes. The commit history in the repository shows each step.

## Testing instructions (for the judges)

Live demo: https://paypilot.donambi.dev (PayPal sandbox, no real money).

- **Login:** owner@paypilot.demo, password: [PASTE THE DEMO PASSWORD HERE]
- Code and setup instructions: https://github.com/Elthiero/paypilot-shield (MIT license, full local setup in the README).

Suggested path (about 3 minutes):

1. Sign in. On the first sign-in from a browser, a new signing key is created for that browser, so the previous policy is shown as "signature invalid".
2. **Policy:** type "Auto pay up to 500, budget 5000 a month", press Review and sign, then Sign policy.
3. **Agent:** ask "Pay INV-002". It should be AUTO_PAY and a sandbox payout is sent. It shows as sent and turns to paid when PayPal's webhook arrives, usually within a minute.
4. **Agent:** ask "Pay INV-003". It needs approval. Open **Approvals**, review and sign. The payout is sent.
5. **Agent:** ask "Pay INV-005". It is blocked, because the payee email changed and the invoice text contains instructions. Open **Payments** and press **Replay** to see each step.

Notes: each invoice can be paid once, so if one shows as already paid, use the **New invoice** button on the Invoices page to create another for an existing supplier. The demo uses one shared account, so signing in from another browser at the same time can make the policy need signing again.
