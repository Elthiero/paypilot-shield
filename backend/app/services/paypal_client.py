"""PayPal client with a real sandbox implementation and a fake for tests and fallback."""
import json
import time
import uuid
from decimal import Decimal

import httpx

from ..config import settings


class PayPalClient:
    def __init__(self):
        self._token = None
        self._expires = 0.0

    def _auth(self) -> str:
        if self._token and time.time() < self._expires - 60:
            return self._token
        r = httpx.post(
            f"{settings.paypal_base_url}/v1/oauth2/token",
            auth=(settings.paypal_client_id, settings.paypal_client_secret),
            data={"grant_type": "client_credentials"},
            timeout=30,
        )
        r.raise_for_status()
        d = r.json()
        self._token = d["access_token"]
        self._expires = time.time() + d["expires_in"]
        return self._token

    def _headers(self, extra=None):
        h = {"Authorization": f"Bearer {self._auth()}", "Content-Type": "application/json"}
        if extra:
            h.update(extra)
        return h

    def send_payout(self, request_id: str, email: str, amount: Decimal, currency: str = "USD", note: str = "") -> dict:
        """request_id doubles as sender_batch_id so a retry can never pay twice."""
        body = {
            "sender_batch_header": {
                "sender_batch_id": request_id,
                "email_subject": "Payment from PayPilot Shield",
                "email_message": note or settings.paypal_sender_note,
            },
            "items": [{
                "recipient_type": "EMAIL",
                "receiver": email,
                "amount": {"value": f"{amount:.2f}", "currency": currency},
                "note": note or settings.paypal_sender_note,
                "sender_item_id": f"item-{request_id}",
            }],
        }
        r = httpx.post(
            f"{settings.paypal_base_url}/v1/payments/payouts",
            json=body,
            headers=self._headers({"PayPal-Request-Id": request_id}),
            timeout=30,
        )
        r.raise_for_status()
        return r.json()  # contains batch_header.payout_batch_id

    def get_batch(self, batch_id: str) -> dict:
        r = httpx.get(
            f"{settings.paypal_base_url}/v1/payments/payouts/{batch_id}",
            headers=self._headers(),
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    def get_balance(self) -> dict:
        """Balance of the account behind the app's credentials. Needs Transaction Search on the PayPal app."""
        r = httpx.get(f"{settings.paypal_base_url}/v1/reporting/balances", params={"currency_code": "USD"},
                      headers=self._headers(), timeout=15)
        r.raise_for_status()
        rows = r.json().get("balances") or []
        if not rows:
            raise ValueError("PayPal returned no balances")
        b = next((x for x in rows if x.get("primary")), rows[0])
        value = (b.get("available_balance") or b.get("total_balance"))["value"]
        return {"currency": b.get("currency", "USD"), "available": float(value)}

    def verify_webhook(self, headers: dict, raw_body: bytes) -> bool:
        """Ask PayPal to check the signature. The event is sent as the raw text PayPal signed, not re-serialised."""
        h = {k: headers.get(f"paypal-{k}") for k in ("auth-algo", "cert-url", "transmission-id", "transmission-sig", "transmission-time")}
        if not all(h.values()) or not settings.paypal_webhook_id:
            return False
        head = json.dumps({k.replace("-", "_"): v for k, v in h.items()} | {"webhook_id": settings.paypal_webhook_id})
        r = httpx.post(
            f"{settings.paypal_base_url}/v1/notifications/verify-webhook-signature",
            content=head[:-1] + ', "webhook_event": ' + raw_body.decode() + "}",
            headers=self._headers(),
            timeout=30,
        )
        r.raise_for_status()
        return r.json().get("verification_status") == "SUCCESS"


class FakePayPalClient:
    """No network. Always succeeds. Used by tests and as a demo fallback."""

    def send_payout(self, request_id, email, amount, currency="USD", note=""):
        return {"batch_header": {"payout_batch_id": "FAKE" + uuid.uuid4().hex[:8], "batch_status": "PENDING"}}

    def get_balance(self):
        return {"currency": "USD", "available": 10000.0}

    def verify_webhook(self, headers, raw_body):
        return headers.get("paypal-transmission-sig") == "valid"  # tests send "valid" or anything else

    def get_batch(self, batch_id):
        return {
            "batch_header": {"batch_status": "SUCCESS"},
            "items": [{"transaction_status": "SUCCESS", "transaction_id": "FAKETXN" + batch_id[-4:]}],
        }


def get_paypal():
    return FakePayPalClient() if settings.paypal_mode == "fake" else PayPalClient()
