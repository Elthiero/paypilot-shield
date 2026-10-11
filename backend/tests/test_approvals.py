import pytest

from app.models import Invoice, PaymentRequest
from app.services.mandate import build_cart_payload
from tests.test_api import login
from tests.test_mandate import sign_like_webcrypto

pytestmark = pytest.mark.usefixtures("policy")


def request_inv003(client, h):
    client.post("/agent/chat", json={"message": "Pay INV-003"}, headers=h)
    (a,) = client.get("/approvals", headers=h).json()
    return a


def test_approve_pays(client, policy):
    h = login(client)
    a = request_inv003(client, h)
    assert a["invoice"] == "INV-003" and a["cart_payload"] and client.get("/transactions", headers=h).json() == []
    r = client.post(f"/approvals/{a['id']}/approve", json={"signature": sign_like_webcrypto(policy.priv, a["cart_payload"])}, headers=h)
    assert r.status_code == 200 and r.json()["status"] == "PAID"
    assert len(client.get("/transactions", headers=h).json()) == 1 and client.get("/approvals", headers=h).json() == []
    steps = [e["step"] for e in client.get(f"/payments/{a['id']}/trace", headers=h).json()]
    assert steps.index("approval_requested") < steps.index("approved") < steps.index("verifier_passed")


def test_reject_does_not_pay(client):
    h = login(client)
    a = request_inv003(client, h)
    r = client.post(f"/approvals/{a['id']}/reject", json={"reason": "too expensive"}, headers=h)
    assert r.json()["status"] == "REJECTED" and client.get("/transactions", headers=h).json() == []
    assert client.post(f"/approvals/{a['id']}/approve", json={"signature": "x"}, headers=h).status_code == 409


def test_bad_signature_keeps_request_open(client, policy):
    h = login(client)
    a = request_inv003(client, h)
    bad = sign_like_webcrypto(policy.priv, a["cart_payload"] + "x")
    assert client.post(f"/approvals/{a['id']}/approve", json={"signature": bad}, headers=h).status_code == 400
    assert len(client.get("/approvals", headers=h).json()) == 1 and client.get("/transactions", headers=h).json() == []


def test_tamper_after_approval_is_refused(client, policy):
    h = login(client)
    a = request_inv003(client, h)
    client.patch("/dev/invoices/INV-003", json={"amount": "1.00", "payee_email": "attacker@x.test"}, headers=h)
    r = client.post(f"/approvals/{a['id']}/approve", json={"signature": sign_like_webcrypto(policy.priv, a["cart_payload"])}, headers=h).json()
    assert r["status"] == "BLOCKED" and "Amount changed after evaluation" in r["reasons"]
    assert client.get("/transactions", headers=h).json() == []


def test_expired_approval_is_closed(client, db, policy):
    h = login(client)
    a = request_inv003(client, h)
    pr = db.query(PaymentRequest).get(a["id"])
    pr.cart_payload = build_cart_payload(policy.id, "INV-003", pr, "2020-01-01T00:00:00")
    db.commit()
    r = client.post(f"/approvals/{a['id']}/approve", json={"signature": "x"}, headers=h)
    assert r.status_code == 409 and "expired" in r.json()["detail"]
    db.expire_all()
    assert db.query(Invoice).filter_by(number="INV-003").first().status == "PENDING"
