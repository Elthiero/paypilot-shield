# Truth check: rule based signals. The LLM classifier (Layer 3) can only raise risk.
import re
from dataclasses import dataclass, field
from statistics import mean

from ..models import Invoice

PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above) (instructions|policy|rules)",
    r"pay (this |it )?(immediately|now|right away)",
    r"override (the )?(policy|limit|rules)",
    r"you are (now )?an? (ai|assistant|agent)",
    r"system prompt",
    r"(disregard|forget) (all |any |the )?(previous|prior|above|earlier)",
    r"(change|update|use) (the )?(payee|bank|paypal|payment) (email|details|account)",
    r"do not (flag|verify|check|review)",
    r"(approved|authorized) by (the )?(ceo|cfo|owner|manager)",
]
OUTLIER_FACTOR = 3  # amount above this many times the supplier's average payout is flagged
MIN_HISTORY = 2  # ponytail: plain mean, needs a few payouts first; use median/stdev if data gets noisy
ROUND_STEP = 1000


@dataclass
class Signals:
    blocking: list = field(default_factory=list)
    review: list = field(default_factory=list)

    def as_dict(self):
        return {"blocking": self.blocking, "review": self.review}


def run_truth_check(db, inv, sup, history) -> Signals:
    """history is the list of amounts (float) of earlier successful payouts to this supplier."""
    s = Signals()
    if not sup.verified:
        s.blocking.append("Supplier is not verified")
    payee = inv.payee_email.strip().lower()
    if sup.last_payout_email and payee != sup.last_payout_email.strip().lower():
        s.blocking.append("Payee email differs from the supplier's last successful payout email")
    elif payee != sup.paypal_email.strip().lower():
        s.review.append("Payee email differs from the supplier's registered PayPal email")
    amount = float(inv.amount)
    dup = (db.query(Invoice.number)
           .filter(Invoice.supplier_id == sup.id, Invoice.amount == inv.amount, Invoice.id != inv.id,
                   Invoice.status.notin_(["PENDING", "BLOCKED"])).first())
    if dup:
        s.review.append(f"Possible duplicate of {dup[0]}: same supplier and amount")
    if len(history) >= MIN_HISTORY and amount > OUTLIER_FACTOR * mean(history):
        s.review.append(f"Amount is more than {OUTLIER_FACTOR}x this supplier's average payout")
    if amount >= ROUND_STEP and amount % ROUND_STEP == 0:
        s.review.append("Large round amount")
    text = inv.description or ""
    if any(re.search(p, text, re.I) for p in PATTERNS):
        s.blocking.append("Invoice text contains instructions aimed at the payer or an AI")
    if not history and not sup.last_payout_email:
        s.review.append("First payment to this supplier")
    return s
