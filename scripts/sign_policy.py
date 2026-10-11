"""Test aid: plays the browser's part so you can sign a policy before the frontend exists.
The private key lives in scripts/owner_key.pem (gitignored). The real app keeps it non-extractable in the browser.

    cd backend && python ../scripts/sign_policy.py --auto-limit 500 --budget 5000 --days 30
    python ../scripts/sign_policy.py --url http://localhost:8000 --email me@x.com --password secret
"""
import argparse
import base64
import os
from datetime import date, timedelta
from pathlib import Path

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

KEY_FILE = Path(__file__).with_name("owner_key.pem")


def load_key():
    if KEY_FILE.exists():
        return serialization.load_pem_private_key(KEY_FILE.read_bytes(), password=None)
    key = ec.generate_private_key(ec.SECP256R1())
    KEY_FILE.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                           serialization.NoEncryption()))
    KEY_FILE.chmod(0o600)
    return key


def sign(key, payload: str) -> str:
    """Raw r||s, 64 bytes, like WebCrypto."""
    r, s = decode_dss_signature(key.sign(payload.encode(), ec.ECDSA(hashes.SHA256())))
    return base64.b64encode(r.to_bytes(32, "big") + s.to_bytes(32, "big")).decode()


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", default="http://localhost:8000")
    a.add_argument("--email", default=os.getenv("DEMO_EMAIL", "owner@paypilot.demo"))
    a.add_argument("--password", default=os.getenv("DEMO_PASSWORD", "change-me"))
    a.add_argument("--auto-limit", default="500")
    a.add_argument("--budget", default="5000")
    a.add_argument("--days", type=int, default=30)
    a.add_argument("--text", default="Auto pay verified suppliers up to the limit, ask me for anything above")
    a = a.parse_args()

    key = load_key()
    pub = base64.b64encode(key.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)).decode()
    with httpx.Client(base_url=a.url, timeout=30) as c:
        def call(method, path, **kw):
            r = c.request(method, path, **kw)
            if r.status_code >= 400:
                raise SystemExit(f"{path} failed: {r.status_code} {r.text}")
            return r.json()

        token = call("POST", "/auth/login", json={"email": a.email, "password": a.password})["token"]
        c.headers["Authorization"] = f"Bearer {token}"
        call("POST", "/auth/register-key", json={"public_key": pub})
        rules = {"auto_limit": a.auto_limit, "currency": "USD", "monthly_budget": a.budget, "require_verified": True,
                 "valid_until": (date.today() + timedelta(days=a.days)).isoformat()}
        p = call("POST", "/mandates/prepare", json={"policy_text": a.text, "rules": rules})
        m = call("POST", f"/mandates/{p['mandate_id']}/sign", json={"signature": sign(key, p["payload"])})
        print(f"Policy {m['id']} is active until {m['valid_until']}: {m['rules']}")


if __name__ == "__main__":
    main()
