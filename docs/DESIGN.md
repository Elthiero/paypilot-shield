# PayPilot Shield: Design Guide (scrapbook style, v2.1 payments palette)

It is the visual contract for the frontend described in `docs/FRONTEND.md`. If a screen needs a value that is not here, add it here first, then use it.

The approved visual reference is the Design Preview artifact (the Agent screen). When this file and the preview disagree, fix the one that is wrong in the same pull request.

## 1. Design intent

**One line:** a playful, handmade, confident product where an AI helps, a rules engine decides, and the owner signs.

**Style:** scrapbook on ruled paper. Flat bright colors, thick black outlines, hard offset shadows, rotated sticker chips, tape on cards, a pixel display font for numbers, a handwritten font for small human notes, and mono caps for labels. It is inspired by the scrapbook portfolio genre in general. It is not a copy of any one site.

**Three ideas the design must communicate**
1. **The AI proposes, the rules decide.** Agent replies and rule decisions are always separate objects.
2. **The owner is in control.** Signing is a deliberate, visible moment.
3. **Everything is explainable.** Any payment can be replayed step by step. Reasons are plain words.

**The balance rule.** The style is loud, the data is not. Playful treatment (rotation, tape, handwriting) lives on shell elements, chips, buttons, chat and cards. Anything the owner must read precisely (tables, amounts, payloads, trace JSON, forms) sits on flat white with straight edges and normal type. If a decoration makes a number harder to read, remove the decoration.

**Decisions fixed for this project:** light theme only, ruled paper background, top navigation bar (no sidebar), flat color stickers, 2px black outlines, 2px corner radius, hard shadows, Lucide icons, comfortable density, ceremonial signing moments, subtle motion.

## 2. Color

Define every color as a token. Never use raw hex in components. Every text and surface pair below was checked against WCAG AA (4.5:1 for text).

### 2.1 Core palette

| Token | Hex | Use |
|---|---|---|
| `ink` | `#111111` | Text, outlines, hard shadows, black blocks |
| `ink-soft` | `#333333` | Secondary headings and notes |
| `ink-mute` | `#444444` | Captions and meta text (9.4:1 on paper) |
| `paper` | `#FBFBF7` | Page background (with ruled lines) |
| `rule` | `#E4E4DC` | Ruled lines on the paper background |
| `card` | `#FFFFFF` | Cards, inputs, nav bar, table body |
| `blue` | `#003087` | Primary action, user chat bubbles, links, step 1 tab (deep payments blue) |
| `blue-mid` | `#0070BA` | Focus ring, link hover, active icons (mid payments blue) |
| `cyan` | `#009CDE` | Step tab 3, info dots, decorative accents. Text on it is always `ink` |
| `yellow` | `#FFC439` | Active nav tab, tape, step 2 tab, needs approval (payments gold) |
| `pink` | `#FF5FA2` | Logo dot, bot avatar, blocked |
| `green` | `#4ADE9A` | Auto pay, paid, verified |

### 2.2 Tints (soft fills)

| Token | Hex | Use |
|---|---|---|
| `mint` | `#C9F2DD` | Soft success fill, sandbox sticker, starter chip |
| `rose` | `#FFC2DD` | Soft pink fill, starter chip |
| `butter` | `#FFE9A8` | Selected grid row, soft warning fill |
| `sky` | `#BFE6F7` | Soft info fill (pending, sent) |
| `blush` | `#FFB3B0` | Soft danger fill for banners |

### 2.3 Text on color (checked contrast)

| Foreground | Background | Ratio |
|---|---|---|
| `ink` | `yellow` | 11.9 |
| `ink` | `pink` | 6.7 |
| `ink` | `green` | 11.0 |
| `ink` | `mint` | 15.5 |
| `ink` | `rose` | 12.6 |
| `ink` | `sky` | 14.3 |
| `ink` | `cyan` | 6.1 |
| `ink` | `blush` | 11.1 |
| white | `blue` | 11.9 |
| white | `blue-mid` | 5.2 |
| white | `ink` | 18.9 |
| `blue` (link) | `paper` | 11.4 |
| `blue-mid` (focus ring, hover) | `paper` | 5.0 |

Rules:
- Text on yellow, pink, green, cyan and the tints is always `ink`. Never put white text on pink, green, yellow or cyan (it fails contrast).
- White text is only allowed on `blue`, `blue-mid` and `ink`.
- Color is never the only signal. Every sticker carries an icon and a text label.
- Large flat areas stay paper or white. Bright color appears on stickers, tabs, tape and the active nav tab.

### 2.4 Decision and status mapping (use exactly this)

| Value | Label | Icon (Lucide) | Sticker fill | Text |
|---|---|---|---|---|
| `AUTO_PAY` | Auto pay | `circle-check` | `green` | `ink` |
| `NEEDS_APPROVAL` | Needs approval | `pen-line` | `yellow` | `ink` |
| `BLOCKED` | Blocked | `shield-x` | `pink` | `ink` |
| `PAID` | Paid | `badge-check` | `green` | `ink` |
| `SENT` | Sent | `send` | `sky` | `ink` |
| `PENDING` | Pending | `clock` | `sky` | `ink` |
| `AWAITING_APPROVAL` | Awaiting approval | `hourglass` | `yellow` | `ink` |
| Risk `LOW` | Low risk | `gauge` | `mint` | `ink` |
| Risk `MEDIUM` | Medium risk | `gauge` | `butter` | `ink` |
| Risk `HIGH` | High risk | `gauge` | `ink` | white |
| Signature valid | Verified | `shield-check` | `green` | `ink` |
| Signature invalid | Signature invalid | `shield-alert` | `pink` | `ink` |
| anything else | raw value, title cased | `circle-help` | `card` | `ink` |

### 2.5 Payments palette (v2.1 change)

v2.1 swaps the original blue and yellow for colors inspired by PayPal's own product. Only the palette changes. Shape, type, shadows, components and layout stay exactly as in v2.

| Role | v2 | v2.1 | Inspired by |
|---|---|---|---|
| Primary blue | `#2347C5` | `#003087` | PayPal's deep brand blue, used across its business dashboard and wordmark |
| Mid blue (focus, hover) | none | `#0070BA` | PayPal's mid blue used for links and interactive states |
| Accent cyan | none | `#009CDE` | PayPal's light brand blue |
| Gold | `#F5C842` | `#FFC439` | The gold of the PayPal checkout button |
| Sky tint | `#B9D0FF` | `#BFE6F7` | Soft light blue fill matching the new blues |

Unchanged: `ink`, `paper`, `rule`, `card`, `pink`, `green` and the other tints. Pink stays the Blocked color and green stays Auto pay, so the decision mapping in 2.4 does not change.

Where each reference applies:
- **Dashboard feel (data screens):** deep `blue` for the nav accents, links and header text weight, `yellow` header row on grids, flat chips.
- **Checkout feel (approval and signing moments):** `yellow` tape and active states, `blue` primary action, `cyan` accents on the signing modal and the seal.

Brand rules:
- These are inspired colors, not PayPal's brand assets. Do not use PayPal's logo, wordmark or typeface (PayPal Sans or PayPalOpen) anywhere.
- Do not present PayPilot Shield as a PayPal product. Keep our own name, logo and the scrapbook style on every screen.
- Where a real PayPal button is needed, use the official PayPal SDK button unmodified (section 2.6). Never recolor or imitate it.
- Our `blue` and `yellow` stickers and buttons must stay visibly ours: always keep the 2px black outline, hard shadow and mono caps label so they cannot be mistaken for a PayPal button.

### 2.6 Official PayPal buttons

- Render PayPal buttons only through the PayPal JS SDK. Do not restyle them.
- On our light paper and white surfaces use the **blue** or **black** PayPal button. PayPal's current guidance says to use blue or black on light backgrounds and white on dark backgrounds. The gold button is being replaced by blue in PayPal's current brand update, so do not design around gold.
- Give the PayPal button its own white card with 24px clear space on all sides, so it does not sit next to our blue and yellow stickers. Put a mono caps label above it such as `PAY WITH PAYPAL`.
- Never place a PayPal button inside a taped decision card or rotate it.
- Allowed text: "Payouts powered by PayPal" in `ink-mute` Small, in the footer or Policy page.

## 3. Typography

Four fonts, each with one job. Load from Google Fonts with `display=swap`.

| Font | Weights | Job |
|---|---|---|
| **Inter** | 400, 500, 600, 700, 800 | Body, headlines, buttons, table cells |
| **JetBrains Mono** | 400, 500, 700 | Caps labels, nav, code, payloads, tool names |
| **Silkscreen** | 400, 700 | Pixel display: logo word, money amounts on cards, big stats |
| **Gaegu** | 400, 700 | Handwritten notes, section tags, empty state captions. Never body text |

| Style | Font | Size / line | Weight | Notes |
|---|---|---|---|---|
| Hero | Inter | 44 / 50 | 800 | Tracking -0.02em, home and login only |
| H1 | Inter | 28 / 34 | 800 | Page titles |
| H2 | Inter | 20 / 28 | 800 | Card titles |
| H3 | Inter | 15 / 24 | 700 | Subsections |
| Body | Inter | 15 / 22 | 400 | Chat and cards |
| Small | Inter | 13 / 20 | 400 | Table cells, helper text |
| Label | JetBrains Mono | 11 / 16 | 700 | Uppercase, letter-spacing 0.08em |
| Code | JetBrains Mono | 13 / 20 | 400 | Payloads, JSON, tool calls |
| Pixel amount | Silkscreen | 24 / 32 | 700 | Money on decision cards |
| Pixel stat | Silkscreen | 32 / 40 | 700 | Stat cards |
| Note | Gaegu | 20 to 26 / 24 to 28 | 700 | Section tags, small human notes |

Rules:
- Use `font-variant-numeric: tabular-nums` for every money value and number column.
- Gaegu is at least 20px, only for short phrases (a few words), never for instructions or errors.
- Silkscreen is only for numbers and the logo word.
- Money: `Intl.NumberFormat("en-US", { style: "currency", currency })`, right aligned in tables.

## 4. Shape, outline, shadow, spacing

- Base unit **4px** (Tailwind scale: 4, 8, 12, 16, 24, 32, 48).
- Outline: **2px solid `ink`** on cards, buttons, inputs, stickers and nav bottom edge.
- Radius: **2px** on cards, buttons, inputs, bubbles; **3px** on section tags; full circle only for avatars and the logo dot. No big rounded corners.
- Hard shadows (no blur), always `ink`:
  - `hard-sm`: `3px 3px 0 #111111` (stickers, chips, small buttons)
  - `hard`: `4px 4px 0 #111111` (chat bubbles, inputs, cards)
  - `hard-lg`: `6px 6px 0 #111111` (decision card, modal)
- Rotation: stickers and decorative elements rotate between **-2deg and +2deg**, always the same value per element (no random values at runtime). The decision card may rotate 0.6deg. Tables, forms, code blocks, inputs and modals never rotate.
- Page padding 48px horizontal on desktop (32px under 1100px). Card padding 20 to 24px. Section gap 24 to 40px.
- Main target viewport 1440 by 900, minimum 1024. Nothing may break at 768.

### Ruled paper background

```css
body {
  background-color: #FBFBF7;
  background-image: repeating-linear-gradient(
    to bottom, transparent 0, transparent 31px, #E4E4DC 31px, #E4E4DC 32px);
}
```
Apply it to the page area. Cards, tables, inputs and modals are solid white on top of it, so text never sits on the lines.

## 5. Layout

```
+----------------------------------------------------------------+
| Top nav (48px): logo | tabs ........ sandbox | email | sign out |
+----------------------------------------------------------------+
|  Hero band (home): note, headline, three sticker chips         |
+----------------------------------------------------------------+
|  Content: main column (flex) + right column (380px)            |
+----------------------------------------------------------------+
```

**Top nav (48px, white, 2px `ink` bottom border)**
- Left: logo dot (26px circle, `pink`, 2px outline, black check) and the word `PAYPILOT` in Silkscreen 14px.
- Tabs in JetBrains Mono 11px bold uppercase, letter-spacing 0.08em, full nav height, 14px horizontal padding, each with a 12px Lucide icon: Agent, Policy, Approvals (with a blue count badge), Payments, Invoices, Suppliers.
- Active tab: `yellow` background, `ink` text. Hover: `butter` background.
- Right: Sandbox or Fake sticker (`mint`, 2px outline, 4px radius, dot), user email in mono 11px, Sign out button.
- Replay is reached from other pages, not listed in the nav.

**Hero band (home page only):** centered, 44px top padding. A Gaegu note (22px, rotated -2deg) such as "hi owner, what are we paying today?", the Hero headline "The AI asks. The rules decide.", then three sticker chips (Auto pay, You sign, Blocked) at -2, +1.5 and -1 degrees. Other pages replace the hero with a normal H1 row (section 11).

**Content area:** a flex row that wraps. Main column grows (min 560px). Right column is fixed at 380px and drops below the main column under 1100px.

## 6. Components

### 6.1 Sticker chip (StatusBadge)
- Rectangular, 2px `ink` outline, `hard-sm` shadow, 4px 10px padding, JetBrains Mono 11px bold uppercase tracking 0.08em, 12px icon (stroke 3) with 6px gap.
- Fill and icon from section 2.4. Rotate by a fixed per-use value within +/-2deg when used in hero or card headers. In table cells use **no rotation and no shadow** (flat, 2px outline) so rows stay aligned.

### 6.2 Buttons
| Variant | Style | Use |
|---|---|---|
| Primary | `ink` fill, white text, with a 18px `blue` square before the label, mono caps 12px, 2px outline | Send, Sign and approve, Draft |
| Brand | `blue` fill, white text, 2px outline, `hard-sm` | Secondary strong actions |
| Secondary | white fill, 2px `ink` outline, mono caps 11px | Cancel, Sign out, Refresh |
| Starter chip | colored fill (`yellow`, `mint`, `rose`), 2px outline, `hard-sm`, Inter 14px 600, rotated within +/-2deg | Suggested prompts |
| Danger | `pink` fill, `ink` text, 2px outline, `hard-sm` | Reject, Simulate tampering |

Height 40px (36px small, 50px for chat send). Hover: translate (-1px, -1px) and grow the shadow by 1px. Active: translate (2px, 2px) and shrink the shadow to 0. Disabled: 50 percent opacity, no shadow, `cursor-not-allowed`. Pending: spinner inside, label stays.

### 6.3 Inputs
White, 2px `ink` outline, 2px radius, `hard` shadow, 50px height (chat) or 44px (forms), 16px padding. Label above in mono caps 11px. Helper text Small `ink-mute`. Focus: 3px `blue-mid` outline with 2px offset (keep the shadow). Error: outline `ink`, a `pink` banner under the field with `circle-alert` icon and the message.

### 6.4 Cards
White, 2px `ink` outline, 2px radius, `hard` shadow, 20 to 24px padding. Header: H2 left, optional action right. A card never has a colored left edge (use a sticker instead). Optional tape (6.6).

### 6.5 Section tag
A small white label box (2px outline, 3px radius, 0 12px padding) in Gaegu 26px bold such as "chat" or "what the agent did", placed above a section. It replaces plain section headings on the home screen. On data pages use H2 instead.

### 6.6 Tape and polaroid card
- Tape: two pieces, 76 by 24px, `rgba(255,196,57,0.75)`, rotated -6deg and +5deg, positioned at the top corners overlapping the card edge by 14px.
- Used on the decision card and the signing modal only. Do not tape ordinary cards.

### 6.7 Step block (trace entry)
A 2 part block: an angled tab on top and a black body.
- Tab: JetBrains Mono 11px bold uppercase, padding 7px 24px 7px 14px, with `clip-path: polygon(0 0, calc(100% - 14px) 0, 100% 100%, 0 100%)`. Tab fill alternates `blue` (white text) and `yellow` (`ink` text), then `cyan`, `pink`, `green` for more steps (`ink` text on all of them).
- Body: `ink` background, white text, 14px 16px padding. First line is the tool call in JetBrains Mono 13px, second line a plain summary in `#D9D9D9`.

### 6.8 Chat bubbles
- User: right aligned, `blue` fill, white text, 2px outline, `hard` shadow, max width 420px.
- Agent: left aligned with a 34px `pink` circle avatar (2px outline, black check), white bubble, 2px outline, `hard` shadow, max width 640px.
- Under agent bubbles: JetBrains Mono 11px caps, `ink-mute`: "Rules mode", "AI mode" or "AI fallback to rules", plus a `blue` "View decision" link.

### 6.9 Tables (AG Grid)
Flat and readable. Wrap the grid in a white card (2px outline, `hard` shadow). Base theme Quartz with these overrides:

```css
.ag-theme-quartz {
  --ag-font-family: Inter, system-ui, sans-serif;
  --ag-font-size: 13px;
  --ag-foreground-color: #111111;
  --ag-background-color: #FFFFFF;
  --ag-header-background-color: #FFC439;
  --ag-header-foreground-color: #111111;
  --ag-border-color: #111111;
  --ag-row-border-color: #E4E4DC;
  --ag-row-hover-color: #FBFBF7;
  --ag-selected-row-background-color: #FFE9A8;
  --ag-range-selection-border-color: #0070BA;
  --ag-row-height: 46px;
  --ag-header-height: 44px;
  --ag-cell-horizontal-padding: 16px;
  --ag-border-radius: 2px;
}
.ag-theme-quartz .ag-header-cell-text {
  font-family: "JetBrains Mono", monospace; font-size: 11px; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase;
}
```
Numbers right aligned with tabular numerals. Status columns use flat sticker chips (no rotation, no shadow). Empty overlay uses EmptyState.

### 6.10 Drawer
Slides in from the right, 480px, white, 2px `ink` left outline, `hard-lg` shadow cast to the left (`-6px 6px 0 #111111`), 24px padding, header with H2 and a close button (secondary, icon only, `aria-label="Close"`). Used for invoice detail.

### 6.11 Banners
Full width, 2px `ink` outline, 2px radius, `hard-sm` shadow, 12px 16px padding, a left Lucide icon, bold title, one line of detail. Fill: `pink` for tamper and errors, `yellow` for warnings and "Drafted by AI", `mint` for success, `sky` for info. Text is `ink`.

### 6.12 Empty, loading, error
- **Empty:** a white card with a 40px Lucide icon in a `yellow` circle (2px outline), a Gaegu line (22px) such as "nothing here yet", one plain Small sentence, and an optional primary button.
- **Loading:** skeleton blocks in `#EFEFE8` with a 2px dashed `ink` outline and a gentle opacity pulse. Spinner only inside buttons.
- **Error:** a `pink` banner with the server `detail` text and a Secondary "Try again" button.

### 6.13 Code and payload block
White background, 2px `ink` outline, 2px radius, 12px padding, JetBrains Mono 13px, horizontal scroll, a Secondary small Copy button at the top right. Never rotated.

## 7. Key patterns

### 7.1 Decision card (signature element)
Polaroid style card with tape (6.6), 2px outline, `hard-lg` shadow, rotated 0.6deg only on the Agent screen (0deg elsewhere). Structure:
1. Top row: label "INVOICE" (mono caps), invoice number (Inter 20px 800), supplier (Small, `ink-mute`), and the amount in Silkscreen 24px on the right.
2. Sticker row: decision chip (rotated -2deg) and risk chip (rotated 1.5deg).
3. Gaegu 22px lead-in: "blocked because:" or "needs your approval because:" or "all clear:".
4. Reasons list: each reason is one line with a 16px `triangle-alert` (or `circle-check` for passes) icon in `ink`, Inter 14px.
5. Footer: 2px dashed `ink` top border, Gaegu 20px centered "decided by rules, not by AI".

This footer is part of the design. Never remove it.

### 7.2 Signing ceremony (modal)
Used for policy signing and approval signing. 560px wide, white, 2px outline, `hard-lg` shadow, taped (6.6), backdrop `rgba(17,17,17,0.55)`. Does not rotate.

1. Header: a 44px `yellow` circle (2px outline) with a `key-round` icon, H2 "Sign with your key", one line: "Your key never leaves this browser."
2. Summary block: the facts being signed in a flat card (amount, payee, invoice, or policy limits).
3. Collapsible "Exact data you are signing" using the code block (the payload string).
4. Footer: Secondary "Cancel", Primary "Sign and approve" (or "Sign policy").
5. States:
   - **Signing:** button spinner and the text "Signing...".
   - **Sealed:** a 72px `green` circle with a black `badge-check` and a hard shadow, scale-in animation, Gaegu "signed and verified!", a Replay link.
   - **Failed:** a `pink` banner with the server message and a "Try again" button.

Focus moves into the modal. `Escape` closes it unless signing. Focus returns to the trigger.

### 7.3 Tamper alert
A `pink` banner pinned at the top of the content area on every page while the active policy fails verification: `shield-alert` icon, title "Policy signature is invalid", detail "All payments are stopped until you sign a new policy.", and a Primary button "Review policy". The Policy tab in the nav gets a small `pink` dot with a 2px outline.

### 7.4 Trace timeline (Replay)
Use step blocks (6.7) stacked with 12px gaps, tab colors cycling `blue`, `yellow`, `cyan`, `pink`, `green`. Each block shows the step label as the tab text, the time in mono Small on the right of the tab row, a one sentence summary, and an expandable raw JSON code block. A failing step gets a `pink` tab. The final block is the decision card (7.1) with the decision chip. No entrance animation on page load.

### 7.5 Chat screen
- Main column: Section tag "chat", the thread (bubbles 6.8), starter chips, then the input row (input plus Primary Send).
- Right column (380px): Section tag "what the agent did", the decision card for `submit_payment_request` first (so the verdict is visible without scrolling), then step blocks for each tool call. At 1100px and wider the column sticks under the nav and scrolls on its own if it is taller than the screen. The Gaegu line "the agent can only request payments" sits under the chat input.
- `aria-live="polite"` on the thread.

## 8. Motion

Subtle. Everything respects `prefers-reduced-motion` (use instant changes).

| Where | Motion | Duration / easing |
|---|---|---|
| Buttons and chips | Translate and shadow change on hover and press | 100ms ease-out |
| Page content | Fade in and 4px upward slide on route change | 160ms ease-out |
| Drawer and modal | Slide from right / fade and scale from 0.98 | 200ms cubic-bezier(0.2, 0, 0, 1) |
| New chat message | Fade and 4px slide | 160ms |
| Skeletons | Opacity pulse 0.6 to 1 | 1.2s loop |
| Signing seal | Scale 0.8 to 1 with one ring pulse | 400ms, once |
| Tamper banner | Slides down | 200ms |

No parallax, no bouncing, no looping decorative animation. Rotations are static.

## 9. Brand assets

- **Name:** PayPilot Shield. Short form: PayPilot.
- **Logo:** a 26px `pink` circle with a 2px `ink` outline and a thick black check mark, next to the word `PAYPILOT` in Silkscreen 700. Build as inline SVG and text, no image file needed.
- **Favicon and tab title:** the pink circle with the check on a `yellow` rounded square. Title pattern: `Page name | PayPilot Shield`.
- **Login screen:** centered card on ruled paper. Gaegu note "welcome back!", H1 "Sign in", fields, Primary button. Beside it (or above under 1100px) three taped sticker lines: "AI proposes" (`sky`), "Rules decide" (`yellow`), "You sign" (`pink`), and the note "Sandbox demo. No real money moves."

## 10. Copy and voice

- Plain, warm, specific. Short sentences. Say what happened, then why, then what the owner can do.
- Lowercase Gaegu notes may be a little friendly ("hi owner", "nothing here yet"). Everything else is normal sentence case and precise.
- Name system actions ("The rules engine blocked this payment"). Never blame the user. No hype words.
- No em dashes or en dashes anywhere in the UI.
- Buttons are verb first: "Request payment", "Review and sign", "Sign and approve", "Reject".

| Moment | Copy |
|---|---|
| Home note | "hi owner, what are we paying today?" |
| Empty approvals | Gaegu "nothing is waiting for you" plus "Ask the agent to pay an invoice that needs a decision." |
| Empty payments | Gaegu "no payments yet" plus "Ask the agent to pay an invoice to see its decision here." |
| Blocked lead-in | "blocked because:" |
| Needs approval lead-in | "needs your approval because:" |
| Draft banner | "Drafted by AI. Not active until you sign." |
| Session expired | "Your session expired. Sign in again to continue." |
| Plain HTTP signing error | "Signing needs a secure connection (HTTPS). Open the app over HTTPS." |
| Key missing | "This browser has no signing key. Create a new key to approve payments." |

## 11. Screen specifications

Behavior and data live in FRONTEND.md section 7. This is the visual layer.

- **Login:** section 9. Centered, stickers beside the form.
- **Agent (home):** hero band (section 5), then chat main column and right column (7.5).
- **Other pages (Policy, Approvals, Payments, Invoices, Suppliers, Replay):** no hero. A page header row: Gaegu note on top (short, e.g. "your invoices"), H1, one line of description in `ink-mute`, primary action on the right. Content below on white cards.
- **Invoices:** status filter chips (flat sticker style) above the grid. Row click opens the drawer. The untrusted description sits in a white box with a 2px dashed `ink` outline, a `triangle-alert` icon, and the caption "Untrusted invoice text. Treated as data, never as instructions." Rows with an email mismatch show a small `triangle-alert` icon with a tooltip.
- **Suppliers:** same pattern as Invoices without a drawer. Verified column uses a `green` Verified chip or a plain `card` chip.
- **Payments:** three stat cards on top (Paid total, Awaiting approval, Blocked), each a white card with a Silkscreen 32px number, a mono label, and a 32px icon in a `green`, `yellow` or `pink` circle. Below, a tab control (Requests, Payouts) in the nav tab style (active tab `yellow`), then the grid.
- **Approvals:** a single column of decision cards (max width 720px, no rotation), each ending with Reject (Danger) and "Review and sign" (Primary). The signing ceremony opens in the modal.
- **Policy:** two columns. Left: the active policy card (rules as a definition list), the Verified chip, valid until, history list. Right (380px): the editor card with the plain language box, Draft button, the form, and "Review and sign". The `yellow` banner "Drafted by AI. Not active until you sign." shows after drafting. A collapsed "Demo tools" card at the bottom holds the Danger button "Simulate tampering" (demo builds only).
- **Replay:** header decision card, then the trace timeline (7.4), then a Secondary "Copy as JSON" button.

## 12. Tailwind setup

`tailwind.config.ts` (extend, do not replace the default scale):

```ts
import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: "#111111", soft: "#333333", mute: "#444444" },
        paper: "#FBFBF7",
        rule: "#E4E4DC",
        card: "#FFFFFF",
        blue: { DEFAULT: "#003087", mid: "#0070BA" },
        cyan: { DEFAULT: "#009CDE" },
        yellow: { DEFAULT: "#FFC439" },
        pink: { DEFAULT: "#FF5FA2" },
        green: { DEFAULT: "#4ADE9A" },
        mint: "#C9F2DD",
        rose: "#FFC2DD",
        butter: "#FFE9A8",
        sky: "#BFE6F7",
        blush: "#FFB3B0",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
        pixel: ["Silkscreen", "monospace"],
        hand: ["Gaegu", "cursive"],
      },
      borderRadius: { DEFAULT: "2px", tag: "3px" },
      borderWidth: { DEFAULT: "2px" },
      boxShadow: {
        "hard-sm": "3px 3px 0 #111111",
        hard: "4px 4px 0 #111111",
        "hard-lg": "6px 6px 0 #111111",
      },
      rotate: { "2": "2deg", "1.5": "1.5deg", "1": "1deg", "-1": "-1deg", "-1.5": "-1.5deg", "-2": "-2deg" },
    },
  },
  plugins: [],
} satisfies Config;
```

Also add to `index.html`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Gaegu:wght@400;700&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&family=Silkscreen:wght@400;700&display=swap" rel="stylesheet">
```
Install icons with `npm i lucide-react`. Set `body` classes to `bg-paper text-ink font-sans antialiased` and add the ruled paper CSS from section 4 to the global stylesheet. Because Tailwind's default `border` utility now means 2px, use `border` for outlines and `border-0` or an explicit `border-[1px]` when a hairline is needed (for example row dividers in tables).

## 13. Accessibility rules

- Text contrast at least 4.5:1. The palette above already passes. Keep text on bright fills as `ink`.
- Visible focus ring on every interactive element: 3px `blue-mid`, offset 2px. Never remove outlines without a replacement.
- Chips and stickers always have a text label. Rotation never changes reading order or hit areas.
- Gaegu text carries no critical information. Anything important is repeated in Inter.
- Minimum target size 36px (44px for primary actions).
- Modals trap focus, use `aria-labelledby`, and return focus on close.
- Live regions: agent replies and signing results use `aria-live="polite"`. Errors use `role="alert"`.
- Tables keep real header cells and an accessible name.
- Respect `prefers-reduced-motion`.

## 14. Do and do not

Do:
- Keep playful elements on the shell, chips, chat and cards, and keep data flat and readable.
- Use ink text on every bright fill.
- Show the reason with every decision and keep "decided by rules, not by AI".
- Show exact payloads before signing.
- Use tabular numerals for all money.

Do not:
- Rotate anything inside a table, form, modal or code block.
- Use more than two Gaegu phrases per screen section.
- Put white text on pink, green, yellow or cyan.
- Use gradients, blur shadows, glassmorphism or emoji (use Lucide icons).
- Show a payment button that bypasses the request flow.
- Use em dashes or en dashes in copy.

## 15. Review checklist (per pull request)

- [ ] Only tokens from this file are used. No raw hex in components.
- [ ] All four states (loading, empty, error, data) exist.
- [ ] Chips use the exact mapping in section 2.4 with icon plus text.
- [ ] Money is tabular and right aligned in tables. Nothing rotates inside tables.
- [ ] Hard shadows and 2px outlines are consistent. No blur shadows.
- [ ] Keyboard path works: tab order, focus ring, modal focus trap.
- [ ] Reduced motion tested.
- [ ] Checked at 1440 and 1024 widths.
- [ ] No em or en dashes in copy.

## 16. Open items

- Check the new palette on the approved Agent-screen preview and update the preview artifact to match v2.1.
- Confirm the focus ring (`blue-mid`) and link colors on every screen before merging.
- Confirm the logo after a first pass in the app, then export the favicon to `frontend/public/`.
- Review the Policy and Approvals screens in this style once built, since they carry the most text and forms.
- If the playful style tests poorly on data screens, tighten section 1 balance rule first (flatter chips, fewer notes) before changing tokens.