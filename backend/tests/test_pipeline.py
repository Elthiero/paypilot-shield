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
    assert any(x["code"] == "supplier_unverified" for x in r["reasons"])
    assert spy.payouts == []


def test_inv005_blocked_two_reasons(db, spy):
    r = submit_payment_request(db, "INV-005", paypal=spy)
    assert r["decision"] == "BLOCKED" and len(r["reasons"]) >= 2
    assert {x["code"] for x in r["reasons"]} >= {"payee_email_changed", "prompt_injection"}
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


def test_layer3_signal_turns_auto_pay_into_approval(db, spy):
    from decimal import Decimal
    from app.models import Invoice
    submit_payment_request(db, "INV-001", paypal=spy)
    db.add(Invoice(number="INV-X", supplier_id=1, description="Office supplies", amount=Decimal("251"),
                   payee_email="abc@x.test"))
    db.commit()
    r = submit_payment_request(db, "INV-X", paypal=spy)
    assert r["decision"] == "NEEDS_APPROVAL" and len(spy.payouts) == 1
    steps = {e["step"]: e for e in get_trace(db, r["payment_request_id"])}
    assert any(x["code"] == "duplicate_invoice" for x in steps["truth_check_done"]["detail"]["review"])


def test_payout_batch_id_is_stable_per_request_and_unique_across_a_reset():
    from datetime import datetime
    from types import SimpleNamespace as NS
    from app.services.pipeline import sender_batch_id
    first = NS(id=1, created_at=datetime(2026, 10, 12, 8, 0, 0))
    again = NS(id=1, created_at=datetime(2026, 10, 12, 8, 0, 0))
    after_reset = NS(id=1, created_at=datetime(2026, 10, 16, 9, 30, 0))  # seed.py restarted ids at 1
    assert sender_batch_id(first) == sender_batch_id(again)  # a retry reuses it, so PayPal refuses a second payout
    assert sender_batch_id(first) != sender_batch_id(after_reset)
    assert len(sender_batch_id(NS(id=999999, created_at=datetime(2026, 10, 12)))) <= 30  # PayPal's limit


def test_payout_uses_that_batch_id(db, spy):
    submit_payment_request(db, "INV-001", paypal=spy)
    assert spy.payouts[0][0].startswith("pp1-")
