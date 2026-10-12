import pytest

pytestmark = pytest.mark.usefixtures("policy")


def login(client):
    r = client.post("/auth/login", json={"email": "owner@paypilot.demo", "password": "test-pass"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_wrong_password(client):
    r = client.post("/auth/login", json={"email": "owner@paypilot.demo", "password": "nope"})
    assert r.status_code == 401


def test_protected_routes_need_token(client):
    assert client.get("/invoices").status_code == 401


def test_invoices_and_suppliers(client):
    h = login(client)
    inv = client.get("/invoices", headers=h).json()
    assert [i["number"] for i in inv] == ["INV-001", "INV-002", "INV-003", "INV-004", "INV-005"]
    assert len(client.get("/suppliers", headers=h).json()) == 4


def test_agent_pays_inv001_and_explains_inv005(client):
    h = login(client)
    r = client.post("/agent/chat", json={"message": "Pay INV-001"}, headers=h).json()
    assert "paid" in r["reply"].lower() and r["mode"] == "rules"
    r5 = client.post("/agent/chat", json={"message": "please pay inv 5"}, headers=h).json()
    assert "BLOCKED" in r5["reply"]
    why = client.post("/agent/chat", json={"message": "Why INV-005?"}, headers=h).json()
    assert "BLOCKED" in why["reply"]
    tx = client.get("/transactions", headers=h).json()
    assert len(tx) == 1 and tx[0]["invoice"] == "INV-001" and tx[0]["status"] == "SUCCESS"
    pays = client.get("/payments", headers=h).json()
    assert len(pays) == 2
    trace = client.get(f"/payments/{pays[0]['id']}/trace", headers=h).json()
    assert trace[0]["step"] == "request_received"


def test_health(client):
    h = client.get("/health").json()
    assert h["paypal_mode"] == "fake" and h["dev_tools"] is True  # the test env is APP_ENV=development
