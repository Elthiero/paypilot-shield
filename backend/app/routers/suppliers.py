from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
from ..models import Supplier

router = APIRouter(prefix="/suppliers", tags=["suppliers"], dependencies=[Depends(current_user)])


@router.get("")
def list_suppliers(db: Session = Depends(get_db)):
    return [
        {"id": s.id, "name": s.name, "paypal_email": s.paypal_email, "verified": s.verified,
         "last_payout_email": s.last_payout_email, "country": s.country}
        for s in db.query(Supplier).order_by(Supplier.id)
    ]
