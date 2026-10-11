from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import create_token, current_user, verify_password
from ..models import Mandate, User
from ..schemas import KeyIn, LoginIn
from ..services.mandate import is_p256_public_key

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong email or password")
    return {"token": create_token(user.id), "email": user.email}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "email": user.email}


@router.post("/register-key")
def register_key(body: KeyIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not is_p256_public_key(body.public_key):
        raise HTTPException(status_code=400, detail="Not a P-256 public key (base64 SPKI)")
    if user.public_key != body.public_key:
        # A new key invalidates any policy signed with the old one
        db.query(Mandate).filter_by(user_id=user.id, active=True).update({"active": False})
        user.public_key = body.public_key
        db.commit()
    return {"ok": True}
