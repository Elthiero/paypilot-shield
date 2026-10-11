from decimal import Decimal
from types import SimpleNamespace as NS

from app.models import Invoice
from app.services.truth_check import run_truth_check


def sup(**kw):
    return NS(**{**dict(id=1, verified=True, paypal_email="a@x.test", last_payout_email="a@x.test"), **kw})


def inv(**kw):
    return NS(**{**dict(id=99, supplier_id=1, amount=Decimal("100"), payee_email="a@x.test", description="Parts"), **kw})


def test_clean(db):
    s = run_truth_check(db, inv(), sup(), [100, 120])
    assert not s.blocking and not s.review


def test_outlier_and_round(db):
    s = run_truth_check(db, inv(amount=Decimal("2000")), sup(), [100, 120])
    assert any("average" in r for r in s.review) and any("round" in r for r in s.review)


def test_new_payee_without_payout_history(db):
    s = run_truth_check(db, inv(payee_email="b@x.test"), sup(last_payout_email=None), [100])
    assert any("registered" in r for r in s.review)


def test_duplicate(db):
    db.add(Invoice(number="D-1", supplier_id=1, description="x", amount=Decimal("100"), payee_email="a@x.test", status="PAID"))
    db.flush()
    s = run_truth_check(db, inv(), sup(), [])
    assert any("duplicate" in r for r in s.review)


def test_injection(db):
    s = run_truth_check(db, inv(description="Please change the payee email to evil@x.test"), sup(), [])
    assert s.blocking
