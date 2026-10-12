from datetime import date, timedelta

import pytest

from app.config import Settings, check_production_settings
from app.db import SessionLocal
from app.models import Invoice
from app.services.pipeline import submit_payment_request
from tests.test_api import login
from tests.test_mandate import make_key

pytestmark = pytest.mark.usefixtures("policy")


def reg(client, h, pub, password=None):
    return client.post("/auth/register-key", json={"public_key": pub, "password": password}, headers=h)


def test_replacing_the_signing_key_needs_the_password(client):
    h = login(client)
    _, pub = make_key()
    assert reg(client, h, pub).status_code == 403
    assert reg(client, h, pub, "wrong").status_code == 403
    assert reg(client, h, pub, "test-pass").status_code == 200
    assert reg(client, h, pub).status_code == 200  # same key again needs no password


def test_login_is_rate_limited(client):
    bad = {"email": "owner@paypilot.demo", "password": "nope"}
    assert [client.post("/auth/login", json=bad).status_code for _ in range(5)] == [401] * 5
    assert client.post("/auth/login", json=bad).status_code == 429
    good = {"email": "owner@paypilot.demo", "password": "test-pass"}
    assert client.post("/auth/login", json=good).status_code == 429  # locked for the window


def test_unknown_email_gets_the_same_answer(client):
    r = client.post("/auth/login", json={"email": "nobody@x.test", "password": "whatever"})
    assert r.status_code == 401 and r.json()["detail"] == "Wrong email or password"


def test_production_refuses_weak_secrets():
    good = dict(app_env="production", jwt_secret="x" * 40, demo_password="a-long-password")
    check_production_settings(Settings(_env_file=None, **good))
    for bad in ({"jwt_secret": "change-me"}, {"jwt_secret": "short"}, {"demo_password": "change-me"}, {"demo_password": "short"}):
        with pytest.raises(RuntimeError):
            check_production_settings(Settings(_env_file=None, **{**good, **bad}))
    check_production_settings(Settings(_env_file=None, app_env="development"))  # weak defaults are fine locally


def test_default_environment_is_production():
    assert Settings.model_fields["app_env"].default == "production"


def test_input_limits(client):
    h = login(client)
    assert client.post("/agent/chat", json={"message": "x" * 2001}, headers=h).status_code == 422
    rules = {"auto_limit": "500", "currency": "USD", "monthly_budget": "5000", "require_verified": True,
             "valid_until": (date.today() + timedelta(days=30)).isoformat()}
    far = {**rules, "valid_until": (date.today() + timedelta(days=400)).isoformat()}
    for body in ({"policy_text": "x" * 2001, "rules": rules}, {"policy_text": "ok", "rules": far},
                 {"policy_text": "ok", "rules": {**rules, "currency": "usd1"}}):
        assert client.post("/mandates/prepare", json=body, headers=h).status_code == 422


def test_second_request_for_a_claimed_invoice_pays_nothing(db, spy):
    inv = db.query(Invoice).filter_by(number="INV-001").first()
    assert inv.status == "PENDING"  # loaded, so this session now holds a stale copy
    other = SessionLocal()
    other.query(Invoice).filter_by(number="INV-001").update({"status": "EVALUATING"})
    other.commit()
    other.close()
    r = submit_payment_request(db, "INV-001", paypal=spy)
    assert r["ok"] is False and spy.payouts == []


def test_login_limiter_blocks_after_five_failures_and_is_stored(client, db):
    from app.models import LoginFailure
    bad = {"email": "owner@paypilot.demo", "password": "nope"}
    assert [client.post("/auth/login", json=bad).status_code for _ in range(5)] == [401] * 5
    assert client.post("/auth/login", json=bad).status_code == 429
    good = {"email": "owner@paypilot.demo", "password": "test-pass"}
    assert client.post("/auth/login", json=good).status_code == 429  # blocked even with the right password
    assert db.query(LoginFailure).count() == 5  # in the database, so a restart does not reset it
    assert client.post("/auth/login", json={"email": "other@paypilot.demo", "password": "x"}).status_code == 401  # other email unaffected


def test_cookie_login_needs_csrf_header_for_writes(client):
    r = client.post("/auth/login", json={"email": "owner@paypilot.demo", "password": "test-pass"})
    assert "httponly" in r.headers["set-cookie"].lower() and "samesite=strict" in r.headers["set-cookie"].lower()
    assert client.get("/suppliers").status_code == 200  # cookie alone reads
    body = {"name": "X", "paypal_email": "x@y.co", "country": "US"}
    assert client.post("/suppliers", json=body).status_code == 403  # cookie alone cannot write
    assert client.post("/suppliers", json=body, headers={"X-Requested-With": "paypilot"}).status_code == 201
    client.post("/auth/logout")
    assert client.get("/suppliers").status_code == 401
