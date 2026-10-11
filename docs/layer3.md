# Layer 3: detection

Layer 3 adds fraud signals to the truth check (`backend/app/services/truth_check.py`). No new endpoint, table or pipeline step. Every reason lands in the existing `truth_check_done` and `decision_made` audit entries, so the Replay page shows it.

## Signals

| Signal | Level | Trigger |
|---|---|---|
| Supplier not verified | Blocking | `supplier.verified` is false (Layer 1) |
| Payee email changed | Blocking | Invoice payee differs from the supplier's last successful payout email (Layer 1) |
| Prompt injection | Blocking | Invoice description, number or supplier name matches a phrase in `PATTERNS`. Text is normalised first (Unicode lookalikes, zero-width characters, extra spaces, case) |
| New payee email | Review | Supplier has no payout history yet and the invoice payee differs from the registered PayPal email |
| Duplicate invoice | Review | Another invoice from the same supplier has an amount within 1% and is not `PENDING` or `BLOCKED` |
| Amount outlier | Review | Amount is more than 3x the supplier's median successful payout (needs at least 2 payouts) |
| Round amount | Review | Amount is a multiple of 1000 and at least 1000, but only added when another signal already fired |
| First payment | Review | No history and no last payout email (Layer 1) |

Blocking gives `BLOCKED` with no payout. Review gives `NEEDS_APPROVAL`. Layer 3 never lowers risk and never calls an LLM.

## Tuning

Constants at the top of `truth_check.py`: `OUTLIER_FACTOR`, `MIN_HISTORY`, `ROUND_STEP`, `DUP_TOLERANCE`, `PATTERNS`.

## Tests

`backend/tests/test_truth_check.py` covers each signal and the injection evasions. `test_pipeline.py` checks that a Layer 3 signal turns an auto pay into an approval and shows in the trace. The five demo invoices decide the same as before.

## Not built

- LLM classifier that can only raise risk. Optional, first to cut.
- Thresholds are fixed in code, not part of the signed policy (it would change the signed payload).
- Structured reasons (`{code, level, message}`). It would change the API contract in `FRONTEND.md`, so it needs Alain's agreement.
