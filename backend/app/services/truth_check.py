# Truth check: rule based signals. The LLM classifier (Layer 3) can only raise risk.
import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal
from statistics import median

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
OUTLIER_FACTOR = 3  # amount above this many times the supplier's median payout is flagged
MIN_HISTORY = 2
ROUND_STEP = 1000
DUP_TOLERANCE = Decimal("0.01")  # amounts within 1% count as the same
_INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u200e\u200f\u2060\ufeff\u00ad"))


def normalize(text: str) -> str:
    """Defeat cheap evasions: lookalike Unicode, zero-width characters, odd spacing, case."""
    return " ".join(unicodedata.normalize("NFKC", text).translate(_INVISIBLE).casefold().split())


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
    amt = Decimal(inv.amount)
    dup = (db.query(Invoice.number)
           .filter(Invoice.supplier_id == sup.id, Invoice.id != inv.id,
                   Invoice.amount.between(amt * (1 - DUP_TOLERANCE), amt * (1 + DUP_TOLERANCE)),
                   Invoice.status.notin_(["PENDING", "BLOCKED"])).first())
    if dup:
        s.review.append(f"Possible duplicate of {dup[0]}: same supplier and nearly the same amount")
    if len(history) >= MIN_HISTORY and float(amt) > OUTLIER_FACTOR * median(history):
        s.review.append(f"Amount is more than {OUTLIER_FACTOR}x this supplier's median payout")
    # every free-text field an attacker controls, not just the description
    text = normalize(" ".join([inv.description or "", inv.number or "", sup.name or ""]))
    if any(re.search(p, text) for p in PATTERNS):
        s.blocking.append("Invoice text contains instructions aimed at the payer or an AI")
    if not history and not sup.last_payout_email:
        s.review.append("First payment to this supplier")
    # a round amount alone is normal business; it only adds context to an already flagged invoice
    if (s.review or s.blocking) and amt >= ROUND_STEP and amt % ROUND_STEP == 0:
        s.review.append("Large round amount")
    return s
