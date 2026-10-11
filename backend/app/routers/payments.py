from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
from ..models import Invoice, PaymentRequest
from ..services.pipeline import get_trace

router = APIRouter(prefix="/payments", tags=["payments"], dependencies=[Depends(current_user)])


@router.get("")
def list_requests(db: Session = Depends(get_db)):
    rows = (db.query(PaymentRequest, Invoice.number)
            .join(Invoice, Invoice.id == PaymentRequest.invoice_id)
            .order_by(PaymentRequest.id.desc()))
    return [
        {"id": p.id, "invoice": n, "amount": float(p.amount), "decision": p.decision, "risk": p.risk_level,
         "reasons": p.reasons, "status": p.status, "created_at": p.created_at.isoformat()}
        for p, n in rows
    ]


@router.get("/{pr_id}/trace")
def trace(pr_id: int, db: Session = Depends(get_db)):
    if not db.get(PaymentRequest, pr_id):
        raise HTTPException(status_code=404, detail="Payment request not found")
    return get_trace(db, pr_id)
