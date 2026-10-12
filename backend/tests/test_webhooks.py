from decimal import Decimal

from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models import AuditEvent, Invoice, PaymentRequest, Transaction

client = TestClient(app)


def _pending(db):
    inv = db.query(Invoice).filter_by(number="INV-001").one()
    pr = PaymentRequest(invoice_id=inv.id, invoice_hash="h", payee_email=inv.payee_email, amount=Decimal("250"), status="SENT")
    db.add(pr)
    db.flush()
    db.add(Transaction(payment_request_id=pr.id, payout_batch_id="BATCH1", amount=Decimal("250")))
    db.commit()
    return pr.id


def _post(sig="valid", batch="BATCH1", item=False):
    resource = {"payout_batch_id": batch} if item else {"batch_header": {"payout_batch_id": batch}}
    return client.post("/webhooks/paypal", json={"id": "WH-1", "event_type": "PAYMENT.PAYOUTSBATCH.SUCCESS", "resource": resource},
                       headers={"PAYPAL-TRANSMISSION-SIG": sig})


def test_bad_signature_is_rejected_and_changes_nothing(db):
    _pending(db)
    assert _post(sig="forged").status_code == 400
    assert db.query(Transaction).one().status == "PENDING"


def test_valid_event_settles_once_for_batch_and_item_events(db):
    pr_id = _pending(db)
    assert _post().status_code == 200
    assert _post(item=True).status_code == 200  # a repeated delivery is a no-op
    s = SessionLocal()
    try:
        assert s.query(Transaction).one().status == "SUCCESS"
        assert s.query(Invoice).filter_by(number="INV-001").one().status == "PAID"
        steps = [e.step for e in s.query(AuditEvent).filter_by(payment_request_id=pr_id)]
        assert steps.count("webhook_received") == 1 and steps.count("payout_confirmed") == 1
    finally:
        s.close()


def test_unknown_batch_is_acknowledged(db):
    assert _post(batch="NOPE").status_code == 200


def test_real_client_sends_the_raw_event_and_fails_closed(monkeypatch):
    import json

    from app.config import settings
    from app.services import paypal_client as pc

    sent = {}

    class R:
        def raise_for_status(self): pass
        def json(self): return {"verification_status": "SUCCESS"}

    monkeypatch.setattr(pc.httpx, "post", lambda url, **kw: sent.update(url=url, **kw) or R())
    monkeypatch.setattr(settings, "paypal_webhook_id", "WH-ID")
    c = pc.PayPalClient()
    monkeypatch.setattr(c, "_auth", lambda: "tok")
    h = {f"paypal-{k}": "x" for k in ("auth-algo", "cert-url", "transmission-id", "transmission-sig", "transmission-time")}
    raw = b'{"id":  "WH-1",  "resource": {}}'  # odd spacing must survive untouched
    assert c.verify_webhook(h, raw) is True
    assert sent["url"].endswith("/v1/notifications/verify-webhook-signature")
    body = json.loads(sent["content"])
    assert body["webhook_id"] == "WH-ID" and body["transmission_sig"] == "x" and body["webhook_event"]["id"] == "WH-1"
    assert b'{"id":  "WH-1",  "resource": {}}' in sent["content"].encode()
    assert c.verify_webhook({}, raw) is False  # missing headers
    monkeypatch.setattr(settings, "paypal_webhook_id", "")
    assert c.verify_webhook(h, raw) is False  # no webhook id configured


def test_real_client_reads_the_primary_balance(monkeypatch):
    from app.services import paypal_client as pc

    class R:
        def __init__(self, data): self.data = data
        def raise_for_status(self): pass
        def json(self): return self.data

    c = pc.PayPalClient()
    monkeypatch.setattr(c, "_auth", lambda: "tok")
    body = {"balances": [
        {"currency": "EUR", "primary": False, "available_balance": {"currency_code": "EUR", "value": "1.00"}},
        {"currency": "USD", "primary": True, "total_balance": {"currency_code": "USD", "value": "900.00"},
         "available_balance": {"currency_code": "USD", "value": "812.50"}}]}
    monkeypatch.setattr(pc.httpx, "get", lambda url, **kw: R(body))
    assert c.get_balance() == {"currency": "USD", "available": 812.5}
    monkeypatch.setattr(pc.httpx, "get", lambda url, **kw: R({"balances": []}))
    try:
        c.get_balance()
        assert False, "empty balances must raise"
    except ValueError:
        pass
