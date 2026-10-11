from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
from ..models import Mandate, User
from ..schemas import PrepareIn, SignIn
from ..services.audit import audit
from ..services.mandate import build_mandate_payload, signed_rules, verify_signature

MAX_POLICY_DAYS = 366

router = APIRouter(prefix="/mandates", tags=["mandates"], dependencies=[Depends(current_user)])


def is_verified(m: Mandate, user: User) -> bool:
    return bool(m.signature and user.public_key and verify_signature(user.public_key, m.payload, m.signature))


def mandate_dict(m: Mandate, user: User) -> dict:
    return {"id": m.id, "policy_text": m.policy_text, "rules": signed_rules(m), "payload": m.payload,
            "signature": m.signature, "active": m.active, "verified": is_verified(m, user),
            "valid_until": m.valid_until.date().isoformat() if m.valid_until else None}


@router.post("/prepare")
def prepare(body: PrepareIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Server builds the exact string to sign. The browser signs these bytes, nothing is re-serialized."""
    if not user.public_key:
        raise HTTPException(status_code=400, detail="Register a public key first")
    try:
        until = datetime.combine(date.fromisoformat(body.rules.valid_until), datetime.min.time())
    except ValueError:
        raise HTTPException(status_code=422, detail="valid_until must be an ISO date")
    if until.date() < date.today():
        raise HTTPException(status_code=422, detail="valid_until is in the past")
    if until.date() > date.today() + timedelta(days=MAX_POLICY_DAYS):
        raise HTTPException(status_code=422, detail=f"valid_until is more than {MAX_POLICY_DAYS} days away")
    rules = body.rules.model_dump(mode="json")
    payload = build_mandate_payload(user.id, rules, body.policy_text)
    m = Mandate(user_id=user.id, policy_text=body.policy_text, rules=rules, payload=payload, valid_until=until)
    db.query(Mandate).filter(Mandate.user_id == user.id, Mandate.signature.is_(None)).delete()  # drop old unsigned drafts
    db.add(m)
    db.commit()
    return {"mandate_id": m.id, "payload": payload}


@router.post("/{mandate_id}/sign")
def sign(mandate_id: int, body: SignIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = db.get(Mandate, mandate_id)
    if not m or m.user_id != user.id:
        raise HTTPException(status_code=404, detail="Mandate not found")
    if not user.public_key or not verify_signature(user.public_key, m.payload, body.signature):
        raise HTTPException(status_code=400, detail="Signature invalid")
    db.query(Mandate).filter(Mandate.user_id == user.id, Mandate.id != m.id).update({"active": False})
    m.signature, m.active = body.signature, True
    audit(db, None, "mandate_activated", {"mandate_id": m.id, "rules": m.rules})
    db.commit()
    return mandate_dict(m, user)


@router.get("/active")
def active(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Feeds the active policy badge. An expired policy counts as none."""
    m = db.query(Mandate).filter_by(user_id=user.id, active=True).first()
    if not m or (m.valid_until and m.valid_until.date() < date.today()):
        return None
    return mandate_dict(m, user)


@router.get("")
def history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Mandate).filter(Mandate.user_id == user.id, Mandate.signature.isnot(None)).order_by(Mandate.id.desc())
    return [mandate_dict(m, user) for m in rows]


@router.get("/{mandate_id}/verify")
def verify(mandate_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = db.get(Mandate, mandate_id)
    if not m or m.user_id != user.id:
        raise HTTPException(status_code=404, detail="Mandate not found")
    ok = is_verified(m, user)
    return {"valid": ok, "reason": "Signature matches the signed policy" if ok else "Signature does not match the policy"}
