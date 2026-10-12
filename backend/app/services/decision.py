# Deterministic decision. The LLM is never called here.
from .truth_check import reason


def decide(rules: dict, signals, spent_this_month, amount):
    blocking = list(signals.blocking)
    if spent_this_month + amount > rules["monthly_budget"]:  # approval cannot lift a budget overrun
        blocking.append(reason("budget_exceeded", "block", "Monthly budget would be exceeded"))
    if blocking:
        return "BLOCKED", "HIGH", blocking
    reasons = list(signals.review)
    if amount > rules["auto_limit"]:
        reasons.append(reason("above_auto_limit", "review", "Amount is above the auto limit"))
    if reasons:
        return "NEEDS_APPROVAL", "MEDIUM", reasons
    return "AUTO_PAY", "LOW", [reason("all_clear", "info", "Within policy and all checks passed")]
