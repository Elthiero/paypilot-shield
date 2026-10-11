"""Test aids for the tamper demo. Only mounted when APP_ENV=development. It never touches PayPal."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
import json

from ..models import Invoice, Mandate
from ..services.mandate import canonical
from ..schemas import TamperIn

router = APIRouter(prefix="/dev", tags=["dev"], dependencies=[Depends(current_user)])


@router.patch("/invoices/{number}")
def tamper(number: str, body: TamperIn, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter_by(number=number.upper()).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if body.amount is not None:
        inv.amount = body.amount
    if body.payee_email is not None:
        inv.payee_email = body.payee_email
    db.commit()
    return {"number": inv.number, "amount": float(inv.amount), "payee_email": inv.payee_email}


@router.post("/mandates/{mandate_id}/tamper")
def tamper_mandate(mandate_id: int, db: Session = Depends(get_db)):
    """Raises the signed auto limit tenfold without re-signing, so the signature no longer matches."""
    m = db.get(Mandate, mandate_id)
    if not m:
        raise HTTPException(status_code=404, detail="Mandate not found")
    data = json.loads(m.payload)
    data["rules"]["auto_limit"] = str(int(float(data["rules"]["auto_limit"]) * 10))
    m.payload = canonical(data)
    db.commit()
    return {"ok": True}
