from decimal import Decimal

from app.models import Invoice, PaymentRequest
from app.services.pipeline import execute_payout, get_trace, submit_payment_request
from tests.conftest import make_policy


def steps(db, r):
    return [e["step"] for e in get_trace(db, r["payment_request_id"])]


def test_no_policy_refuses_to_pay(db, spy):
    r = submit_payment_request(db, "INV-001", paypal=spy)
    assert r["status"] == "BLOCKED" and r["reasons"] == ["No active signed policy"]
    assert spy.payouts == [] and "verifier_failed" in steps(db, r)


def test_expired_policy_refuses(db, spy):
    make_policy(db, days=-1)
    r = submit_payment_request(db, "INV-001", paypal=spy)
    assert r["status"] == "BLOCKED" and spy.payouts == []


def test_forged_signature_refuses(db, spy):
    make_policy(db, sign=False)
    r = submit_payment_request(db, "INV-001", paypal=spy)
    assert r["reasons"] == ["Policy signature invalid"] and spy.payouts == []


def test_valid_policy_pays_and_audits_verifier(db, spy, policy):
    r = submit_payment_request(db, "INV-001", paypal=spy)
    assert r["status"] == "PAID" and "verifier_passed" in steps(db, r)
    assert r["payment_request_id"] and db.get(PaymentRequest, r["payment_request_id"]).mandate_id == policy.id


def test_editing_rules_column_does_not_change_decisions(db, spy, policy):
    policy.rules = {**policy.rules, "auto_limit": "100000"}
    db.commit()
    assert submit_payment_request(db, "INV-003", paypal=spy)["decision"] == "NEEDS_APPROVAL"


def test_tampered_invoice_after_evaluation_is_refused(db, spy, policy):
    r = submit_payment_request(db, "INV-003", paypal=spy)           # evaluated at 1500
    pr = db.get(PaymentRequest, r["payment_request_id"])
    pr.decision = "AUTO_PAY"                                        # skip approval, which is step 4
    inv = db.query(Invoice).filter_by(number="INV-003").first()
    inv.amount = Decimal("1.00")
    inv.payee_email = "attacker@x.test"
    execute_payout(db, pr, inv, spy)
    failures = get_trace(db, pr.id)[-1]["detail"]["failures"]
    assert "Amount changed after evaluation" in failures and "Payee changed after evaluation" in failures
    assert "Invoice changed after evaluation" in failures and spy.payouts == []


def test_replay_of_paid_request_is_refused(db, spy, policy):
    r = submit_payment_request(db, "INV-001", paypal=spy)
    pr = db.get(PaymentRequest, r["payment_request_id"])
    execute_payout(db, pr, db.query(Invoice).filter_by(number="INV-001").first(), spy)
    assert "This request was already paid" in get_trace(db, pr.id)[-1]["detail"]["failures"]
    assert len(spy.payouts) == 1


def test_budget_is_enforced_by_verifier(db, spy, policy):
    r = submit_payment_request(db, "INV-003", paypal=spy)
    pr = db.get(PaymentRequest, r["payment_request_id"])
    pr.decision = "AUTO_PAY"
    pr.amount = Decimal("6000")  # snapshot above the signed 5000 budget
    execute_payout(db, pr, db.query(Invoice).filter_by(number="INV-003").first(), spy)
    assert "Monthly budget exceeded" in get_trace(db, pr.id)[-1]["detail"]["failures"]
