from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import DUMMY_HASH, create_token, current_user, login_limiter, verify_password
from ..models import Mandate, User
from ..schemas import KeyIn, LoginIn
from ..services.mandate import is_p256_public_key

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    key = (request.client.host if request.client else "?", body.email.lower())
    if login_limiter.blocked(key):
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in a few minutes.")
    user = db.query(User).filter_by(email=body.email).first()
    # always run bcrypt so the response time does not reveal whether the email exists
    ok = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not ok:
        login_limiter.fail(key)
        raise HTTPException(status_code=401, detail="Wrong email or password")
    login_limiter.reset(key)
    return {"token": create_token(user.id), "email": user.email}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "email": user.email}


@router.post("/register-key")
def register_key(body: KeyIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not is_p256_public_key(body.public_key):
        raise HTTPException(status_code=400, detail="Not a P-256 public key (base64 SPKI)")
    if user.public_key and user.public_key != body.public_key:
        # Replacing the signing key needs the password, so a stolen login token alone cannot take over signing
        if not body.password or not verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=403, detail="Password required to replace the signing key")
    if user.public_key != body.public_key:
        # A new key invalidates any policy signed with the old one
        db.query(Mandate).filter_by(user_id=user.id, active=True).update({"active": False})
        user.public_key = body.public_key
        db.commit()
    return {"ok": True}
