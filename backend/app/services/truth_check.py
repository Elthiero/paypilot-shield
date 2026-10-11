# Truth check: rule based signals. The LLM classifier (Layer 3) can only raise risk.
import re
from dataclasses import dataclass, field

PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above) (instructions|policy|rules)",
    r"pay (this |it )?(immediately|now|right away)",
    r"override (the )?(policy|limit|rules)",
    r"you are (now )?an? (ai|assistant|agent)",
    r"system prompt",
]


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
    if sup.last_payout_email and inv.payee_email.strip().lower() != sup.last_payout_email.strip().lower():
        s.blocking.append("Payee email differs from the supplier's last successful payout email")
    text = inv.description or ""
    if any(re.search(p, text, re.I) for p in PATTERNS):
        s.blocking.append("Invoice text contains instructions aimed at the payer or an AI")
    if not history and not sup.last_payout_email:
        s.review.append("First payment to this supplier")
    return s
