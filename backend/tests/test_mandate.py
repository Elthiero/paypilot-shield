import base64
from decimal import Decimal
from types import SimpleNamespace as NS

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from app.services.mandate import build_cart_payload, build_mandate_payload, canonical, verify_signature


def make_key():
    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    return priv, base64.b64encode(pub).decode()


def sign_like_webcrypto(priv, payload: str) -> str:
    """WebCrypto output: raw r||s, 32 bytes each, base64."""
    r, s = decode_dss_signature(priv.sign(payload.encode(), ec.ECDSA(hashes.SHA256())))
    return base64.b64encode(r.to_bytes(32, "big") + s.to_bytes(32, "big")).decode()


def test_valid_signature():
    priv, pub = make_key()
    payload = build_mandate_payload(1, {"auto_limit": "500"}, "pay up to 500")
    assert verify_signature(pub, payload, sign_like_webcrypto(priv, payload))


def test_tampered_payload_rejected():
    priv, pub = make_key()
    payload = build_mandate_payload(1, {"auto_limit": "500"}, "pay up to 500")
    sig = sign_like_webcrypto(priv, payload)
    assert not verify_signature(pub, payload.replace("500", "5000"), sig)


def test_wrong_key_rejected():
    priv, _ = make_key()
    _, other_pub = make_key()
    payload = build_mandate_payload(1, {}, "x")
    assert not verify_signature(other_pub, payload, sign_like_webcrypto(priv, payload))


def test_bad_length_and_garbage_rejected():
    priv, pub = make_key()
    payload = "x"
    good = base64.b64decode(sign_like_webcrypto(priv, payload))
    assert not verify_signature(pub, payload, base64.b64encode(good[:63]).decode())
    assert not verify_signature(pub, payload, base64.b64encode(good + b"\0").decode())
    assert not verify_signature(pub, payload, "not base64!!")
    assert not verify_signature("not a key", payload, base64.b64encode(good).decode())


def test_payload_is_canonical_and_unique():
    assert canonical({"b": 1, "a": 2}) == '{"a":2,"b":1}'
    assert build_mandate_payload(1, {}, "x") != build_mandate_payload(1, {}, "x")  # fresh nonce


def test_cart_payload_comes_from_snapshot():
    pr = NS(id=7, invoice_hash="abc", payee_email="A@X.test", amount=Decimal("1500"), currency="USD")
    cart = build_cart_payload(3, "INV-003", pr, "2030-01-01T00:00:00")
    assert '"amount":"1500.00"' in cart and '"payee_email":"a@x.test"' in cart and '"request_id":7' in cart
    assert '"expires_at":"2030-01-01T00:00:00"' in cart
