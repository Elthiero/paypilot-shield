from app.models import Transaction
from app.services.pipeline import submit_payment_request, get_trace

import pytest
pytestmark = pytest.mark.usefixtures("policy")


def test_inv001_auto_pay(db, spy):
    r = submit_payment_request(db, "INV-001", paypal=spy)
    assert r["decision"] == "AUTO_PAY" and r["status"] == "PAID"
    assert len(spy.payouts) == 1 and spy.payouts[0][1] == "abc@x.test"


def test_inv002_auto_pay(db, spy):
    assert submit_payment_request(db, "INV-002", paypal=spy)["status"] == "PAID"


def test_inv003_needs_approval_no_payout(db, spy):
    r = submit_payment_request(db, "INV-003", paypal=spy)
    assert r["decision"] == "NEEDS_APPROVAL" and r["status"] == "AWAITING_APPROVAL"
    assert spy.payouts == []


def test_inv004_blocked_unverified(db, spy):
    r = submit_payment_request(db, "INV-004", paypal=spy)
    assert r["decision"] == "BLOCKED"
    assert any("not verified" in x for x in r["reasons"])
    assert spy.payouts == []


def test_inv005_blocked_two_reasons(db, spy):
    r = submit_payment_request(db, "INV-005", paypal=spy)
    assert r["decision"] == "BLOCKED" and len(r["reasons"]) >= 2
    assert any("email" in x for x in r["reasons"]) and any("instructions" in x for x in r["reasons"])
    assert spy.payouts == []


def test_idempotent_second_submit_does_not_pay_twice(db, spy):
    submit_payment_request(db, "INV-001", paypal=spy)
    r2 = submit_payment_request(db, "INV-001", paypal=spy)
    assert len(spy.payouts) == 1
    assert db.query(Transaction).count() == 1
    assert "already" in r2["note"]


def test_unknown_invoice(db, spy):
    assert submit_payment_request(db, "INV-999", paypal=spy)["ok"] is False


def test_audit_trace_has_steps_in_order(db, spy):
    r = submit_payment_request(db, "INV-001", paypal=spy)
    steps = [e["step"] for e in get_trace(db, r["payment_request_id"])]
    assert steps[:2] == ["request_received", "invoice_loaded"]
    assert "decision_made" in steps and steps[-1] == "payout_confirmed"
