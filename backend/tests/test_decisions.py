from decimal import Decimal

from app.services.decision import decide
from app.services.truth_check import Signals, reason

RULES = {"auto_limit": Decimal("500"), "monthly_budget": Decimal("5000")}


def test_auto_pay():
    assert decide(RULES, Signals(), Decimal("0"), Decimal("250"))[0] == "AUTO_PAY"


def test_needs_approval_over_limit():
    assert decide(RULES, Signals(), Decimal("0"), Decimal("1500"))[0] == "NEEDS_APPROVAL"


def test_blocked_on_signal():
    s = Signals(blocking=[reason("supplier_unverified", "block", "Supplier is not verified")])
    assert decide(RULES, s, Decimal("0"), Decimal("900"))[0] == "BLOCKED"
