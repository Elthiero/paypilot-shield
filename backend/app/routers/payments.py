from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
from ..models import Invoice, PaymentRequest, Supplier
from ..schemas import PaymentIn
from ..services.pipeline import get_trace, submit_payment_request, summarize

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


@router.post("")
def request_payment(body: PaymentIn, db: Session = Depends(get_db)):
    """Same pipeline the agent uses. It cannot skip any check."""
    return submit_payment_request(db, body.invoice_number)


@router.get("/{pr_id}")
def one(pr_id: int, db: Session = Depends(get_db)):
    pr = db.get(PaymentRequest, pr_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Payment request not found")
    inv = db.get(Invoice, pr.invoice_id)
    out = summarize(db, pr, inv)
    out.update(supplier=db.get(Supplier, inv.supplier_id).name, currency=pr.currency, created_at=pr.created_at.isoformat())
    return out
