"""Signed policy (mandate) helpers.
The server builds the exact payload string, the browser signs it, the server verifies it.
WebCrypto returns raw 64 byte r||s signatures, Python needs DER (encode_dss_signature)."""
import base64
import json
import secrets

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature


def canonical(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def build_mandate_payload(user_id: int, rules: dict, policy_text: str) -> str:
    return canonical({"type": "intent_mandate", "user_id": user_id, "rules": rules,
                      "policy_text": policy_text, "nonce": secrets.token_hex(8)})


def build_cart_payload(mandate_id: int, invoice_number: str, pr, expires_at: str) -> str:
    """Built from the frozen snapshot on the payment request, so it cannot drift with the live invoice."""
    return canonical({"type": "cart", "mandate_id": mandate_id, "invoice_number": invoice_number,
                      "invoice_hash": pr.invoice_hash, "payee_email": pr.payee_email.lower(),
                      "amount": f"{pr.amount:.2f}", "currency": pr.currency, "request_id": pr.id, "expires_at": expires_at})


def verify_signature(public_key_b64: str, payload: str, signature_b64: str) -> bool:
    try:
        pub = serialization.load_der_public_key(base64.b64decode(public_key_b64))
        raw = base64.b64decode(signature_b64)
        if len(raw) != 64:
            return False
        r, s = int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")
        pub.verify(encode_dss_signature(r, s), payload.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False


def is_p256_public_key(public_key_b64: str) -> bool:
    try:
        key = serialization.load_der_public_key(base64.b64decode(public_key_b64))
        return isinstance(key, ec.EllipticCurvePublicKey) and key.curve.name == "secp256r1"
    except Exception:
        return False


def signed_rules(mandate) -> dict:
    """Rules as signed. Always read these, never the editable `rules` column."""
    return json.loads(mandate.payload)["rules"]
