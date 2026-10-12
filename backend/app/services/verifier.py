"""Right before payout: verify the signed policy, the invoice against its frozen snapshot, the budget
and the replay guard. Returns a list of failures. Any failure means PayPal is NOT called."""
import json
from datetime import date, datetime
from decimal import Decimal

from .mandate import build_cart_payload, signed_rules, verify_signature


def verify_before_payment(pr, inv, live_hash: str, spent: Decimal, mandate, user, already_paid: bool) -> list:
    f = []
    if not mandate or not mandate.active:
        f.append("No active signed policy")
    elif not user or not user.public_key or not mandate.signature \
            or not verify_signature(user.public_key, mandate.payload, mandate.signature):
        f.append("Policy signature invalid")
    rules = signed_rules(mandate) if mandate else {}
    if rules and date.fromisoformat(rules["valid_until"]) < date.today():
        f.append("Policy expired")

    if live_hash != pr.invoice_hash:
        f.append("Invoice changed after evaluation")
    if inv.payee_email.lower() != pr.payee_email.lower():
        f.append("Payee changed after evaluation")
    if Decimal(inv.amount) != Decimal(pr.amount):
        f.append("Amount changed after evaluation")
    if rules and pr.currency != rules.get("currency", "USD"):
        f.append("Currency not allowed by policy")

    if pr.decision == "AUTO_PAY" and rules and Decimal(pr.amount) > Decimal(str(rules["auto_limit"])):
        f.append("Amount above the signed auto limit")  # decide() should never allow this, so check it again here

    if pr.decision == "NEEDS_APPROVAL":
        expires = json.loads(pr.cart_payload).get("expires_at", "") if pr.cart_payload else ""
        if not mandate or not expires or pr.cart_payload != build_cart_payload(mandate.id, inv.number, pr, expires):
            f.append("Cart no longer matches the invoice")
        elif datetime.fromisoformat(expires) < datetime.utcnow():
            f.append("Approval expired")
        elif not user or not pr.cart_signature or not verify_signature(user.public_key, pr.cart_payload, pr.cart_signature):
            f.append("Approval signature invalid")

    if rules and spent + Decimal(pr.amount) > Decimal(str(rules.get("monthly_budget", 0))):
        f.append("Monthly budget exceeded")
    if already_paid:
        f.append("This request was already paid")
    return f
