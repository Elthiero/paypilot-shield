# Deterministic decision. The LLM is never called here.
from .truth_check import reason


def decide(rules: dict, signals, spent_this_month, amount):
    if signals.blocking:
        return "BLOCKED", "HIGH", signals.blocking
    reasons = list(signals.review)
    if amount > rules["auto_limit"]:
        reasons.append(reason("above_auto_limit", "review", "Amount is above the auto limit"))
    if spent_this_month + amount > rules["monthly_budget"]:
        reasons.append(reason("budget_exceeded", "review", "Monthly budget would be exceeded"))
    if reasons:
        return "NEEDS_APPROVAL", "MEDIUM", reasons
    return "AUTO_PAY", "LOW", [reason("all_clear", "info", "Within policy and all checks passed")]
