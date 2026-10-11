# Deterministic decision. The LLM is never called here.
def decide(rules: dict, signals, spent_this_month, amount):
    if signals.blocking:
        return "BLOCKED", "HIGH", signals.blocking
    reasons = list(signals.review)
    if amount > rules["auto_limit"]:
        reasons.append("Amount is above the auto limit")
    if spent_this_month + amount > rules["monthly_budget"]:
        reasons.append("Monthly budget would be exceeded")
    if reasons:
        return "NEEDS_APPROVAL", "MEDIUM", reasons
    return "AUTO_PAY", "LOW", ["Within policy and all checks passed"]
