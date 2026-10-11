"""
Test your PayPal sandbox credentials.

Usage:
    pip install requests python-dotenv
    python test_paypal_sandbox.py              # step 1 and 2: token + capabilities check
    python test_paypal_sandbox.py --payout     # also sends a $1.00 sandbox payout and checks its status
    python test_paypal_sandbox.py --payout --email someone@personal.example.com

.env file (same folder):
    PAYPAL_CLIENT_ID=your_sandbox_client_id
    PAYPAL_SECRECT_KEY=your_sandbox_secret     (PAYPAL_SECRET_KEY also works)
"""
import argparse
import base64
import os
import sys
import time
import uuid

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Minimal .env reader if python-dotenv is not installed
    if os.path.exists(".env"):
        for line in open(".env", encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

BASE = "https://api-m.sandbox.paypal.com"
CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "").strip()
SECRET = (os.getenv("PAYPAL_SECRECT_KEY") or os.getenv("PAYPAL_SECRET_KEY") or os.getenv("PAYPAL_CLIENT_SECRET") or "").strip()


def ok(msg):
    print(f"[ OK ] {msg}")


def fail(msg):
    print(f"[FAIL] {msg}")


def info(msg):
    print(f"       {msg}")


def show_error(r):
    try:
        body = r.json()
    except Exception:
        body = r.text
    info(f"HTTP {r.status_code}")
    info(f"Response: {body}")
    debug_id = r.headers.get("Paypal-Debug-Id")
    if debug_id:
        info(f"PayPal debug id (give this to PayPal support): {debug_id}")


def get_token():
    print("\nStep 1: OAuth token")
    if not CLIENT_ID or not SECRET:
        fail("PAYPAL_CLIENT_ID or PAYPAL_SECRECT_KEY missing from your environment or .env file")
        sys.exit(1)
    info(f"Client ID loaded: {CLIENT_ID[:6]}...{CLIENT_ID[-4:]} (length {len(CLIENT_ID)})")
    r = requests.post(
        f"{BASE}/v1/oauth2/token",
        auth=(CLIENT_ID, SECRET),
        data={"grant_type": "client_credentials"},
        headers={"Accept": "application/json"},
        timeout=30,
    )
    if r.status_code != 200:
        fail("Could not get a token")
        show_error(r)
        info("Check: sandbox (not live) credentials, no extra spaces or quotes, secret copied fully.")
        sys.exit(1)
    data = r.json()
    ok(f"Token received, expires in {data.get('expires_in')} seconds")
    scopes = data.get("scope", "")
    info(f"App id: {data.get('app_id')}")
    payouts_scope = "https://uri.paypal.com/services/payments/payouts" in scopes
    info(f"Payouts scope listed in token: {payouts_scope} (informational only, the real test is the payout below)")
    return data["access_token"], payouts_scope


def headers(token, extra=None):
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if extra:
        h.update(extra)
    return h


def check_identity(token):
    print("\nStep 2: Basic API call (userinfo)")
    r = requests.get(f"{BASE}/v1/identity/oauth2/userinfo?schema=paypalv1.1", headers=headers(token), timeout=30)
    if r.status_code == 200:
        ok("API accepts the token")
    else:
        info("Userinfo may be disabled for your app, which is normal. Not a blocker.")
        info(f"HTTP {r.status_code}")


def send_payout(token, email, amount):
    print("\nStep 3: Create a sandbox payout")
    batch_id = f"test-{uuid.uuid4().hex[:12]}"
    body = {
        "sender_batch_header": {
            "sender_batch_id": batch_id,
            "email_subject": "Sandbox test payout",
            "email_message": "Test payment from my sandbox script",
        },
        "items": [
            {
                "recipient_type": "EMAIL",
                "receiver": email,
                "amount": {"value": f"{amount:.2f}", "currency": "USD"},
                "note": "Sandbox test",
                "sender_item_id": f"item-{batch_id}",
            }
        ],
    }
    r = requests.post(
        f"{BASE}/v1/payments/payouts",
        json=body,
        headers=headers(token, {"PayPal-Request-Id": batch_id}),
        timeout=30,
    )
    if r.status_code not in (200, 201):
        fail("Payout request was rejected")
        show_error(r)
        info("PERMISSION_DENIED or AUTHORIZATION_ERROR usually means Payouts is not enabled for this app or account.")
        info("Fallback plan: use the Invoicing API instead (see section 15.3 of the build guide).")
        sys.exit(1)
    data = r.json()
    payout_batch_id = data["batch_header"]["payout_batch_id"]
    ok(f"Payout created, payout_batch_id = {payout_batch_id}")
    info(f"Initial status: {data['batch_header'].get('batch_status')}")
    return payout_batch_id


def poll_payout(token, payout_batch_id, tries=6, wait=5):
    print("\nStep 4: Check payout status")
    for i in range(1, tries + 1):
        r = requests.get(f"{BASE}/v1/payments/payouts/{payout_batch_id}", headers=headers(token), timeout=30)
        if r.status_code != 200:
            fail("Could not read the payout")
            show_error(r)
            return
        data = r.json()
        batch_status = data["batch_header"]["batch_status"]
        items = data.get("items", [])
        item_status = items[0]["transaction_status"] if items else "n/a"
        info(f"Attempt {i}: batch={batch_status}, item={item_status}")
        if batch_status in ("SUCCESS", "DENIED", "CANCELED"):
            (ok if batch_status == "SUCCESS" else fail)(f"Final batch status: {batch_status}")
            if batch_status != "SUCCESS":
                import json
                for it in items:
                    iid = it.get("payout_item_id")
                    if not iid:
                        continue
                    rr = requests.get(f"{BASE}/v1/payments/payouts-item/{iid}", headers=headers(token), timeout=30)
                    detail = rr.json() if rr.headers.get("content-type", "").startswith("application/json") else rr.text
                    print("\nItem detail (read the 'errors' block):")
                    print(json.dumps(detail, indent=2))
            if item_status == "UNCLAIMED":
                info("UNCLAIMED means the receiver email has no sandbox account. Use a sandbox personal account email.")
            return
        time.sleep(wait)
    info("Still pending. Sandbox can be slow, re-check later in the Sandbox dashboard.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--payout", action="store_true", help="also send a test payout")
    ap.add_argument("--email", default=os.getenv("PAYPAL_TEST_RECEIVER", "sb-test-buyer@personal.example.com"),
                    help="sandbox PERSONAL account email to receive the payout")
    ap.add_argument("--amount", type=float, default=1.00)
    args = ap.parse_args()

    token, payouts_scope = get_token()
    check_identity(token)

    if args.payout:
        pid = send_payout(token, args.email, args.amount)
        poll_payout(token, pid)
    else:
        print("\nToken works. Run again with --payout --email <sandbox personal email> to test a real sandbox payout.")

    print("\nDone.")


if __name__ == "__main__":
    main()
