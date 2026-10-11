from datetime import date, timedelta

from tests.test_api import login
from tests.test_mandate import make_key, sign_like_webcrypto

RULES = {"auto_limit": "500", "currency": "USD", "monthly_budget": "5000", "require_verified": True,
         "valid_until": (date.today() + timedelta(days=30)).isoformat()}


def setup(client):
    h = login(client)
    priv, pub = make_key()
    assert client.post("/auth/register-key", json={"public_key": pub}, headers=h).status_code == 200
    return h, priv


def prepare(client, h, rules=RULES):
    return client.post("/mandates/prepare", json={"policy_text": "auto pay up to 500", "rules": rules}, headers=h)


def test_register_key_rejects_garbage(client):
    h = login(client)
    assert client.post("/auth/register-key", json={"public_key": "nope"}, headers=h).status_code == 400


def test_prepare_needs_key(client):
    assert prepare(client, login(client)).status_code == 400


def test_sign_activates_policy(client):
    h, priv = setup(client)
    assert client.get("/mandates/active", headers=h).json() is None
    p = prepare(client, h).json()
    r = client.post(f"/mandates/{p['mandate_id']}/sign", json={"signature": sign_like_webcrypto(priv, p["payload"])}, headers=h)
    assert r.status_code == 200 and r.json()["active"] is True
    assert client.get("/mandates/active", headers=h).json()["id"] == p["mandate_id"]


def test_bad_signature_does_not_activate(client):
    h, priv = setup(client)
    p = prepare(client, h).json()
    bad = sign_like_webcrypto(priv, p["payload"] + "x")
    assert client.post(f"/mandates/{p['mandate_id']}/sign", json={"signature": bad}, headers=h).status_code == 400
    assert client.get("/mandates/active", headers=h).json() is None


def test_new_policy_replaces_old_and_new_key_deactivates(client):
    h, priv = setup(client)
    ids = []
    for _ in range(2):
        p = prepare(client, h).json()
        client.post(f"/mandates/{p['mandate_id']}/sign", json={"signature": sign_like_webcrypto(priv, p["payload"])}, headers=h)
        ids.append(p["mandate_id"])
    assert client.get("/mandates/active", headers=h).json()["id"] == ids[1]
    _, pub2 = make_key()
    client.post("/auth/register-key", json={"public_key": pub2}, headers=h)
    assert client.get("/mandates/active", headers=h).json() is None


def test_past_expiry_rejected(client):
    h, _ = setup(client)
    old = {**RULES, "valid_until": (date.today() - timedelta(days=1)).isoformat()}
    assert prepare(client, h, old).status_code == 422


def activate(client):
    h, priv = setup(client)
    p = prepare(client, h).json()
    client.post(f"/mandates/{p['mandate_id']}/sign", json={"signature": sign_like_webcrypto(priv, p["payload"])}, headers=h)
    return h, p["mandate_id"]


def test_history_and_verify(client):
    h, mid = activate(client)
    assert [m["id"] for m in client.get("/mandates", headers=h).json()] == [mid]
    assert client.get("/mandates/active", headers=h).json()["verified"] is True
    assert client.get(f"/mandates/{mid}/verify", headers=h).json()["valid"] is True


def test_policy_tamper_flips_verify_and_blocks_payment(client):
    h, mid = activate(client)
    assert client.post(f"/dev/mandates/{mid}/tamper", headers=h).json() == {"ok": True}
    assert client.get(f"/mandates/{mid}/verify", headers=h).json()["valid"] is False
    assert client.get("/mandates/active", headers=h).json()["verified"] is False
    r = client.post("/payments", json={"invoice_number": "INV-001"}, headers=h).json()
    assert r["status"] == "BLOCKED" and r["reasons"] == ["Policy signature invalid"] and r["transaction"] is None
    one = client.get(f"/payments/{r['payment_request_id']}", headers=h).json()
    assert one["invoice"] == "INV-001" and one["supplier"] == "ABC Supplies"
