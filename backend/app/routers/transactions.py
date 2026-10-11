from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
from ..models import Invoice, PaymentRequest, Transaction
from ..services.paypal_client import get_paypal
from ..services.pipeline import refresh_transaction

router = APIRouter(prefix="/transactions", tags=["transactions"], dependencies=[Depends(current_user)])


def txn_dict(t: Transaction, number: str | None):
    return {
        "id": t.id, "payment_request_id": t.payment_request_id, "invoice": number,
        "payout_batch_id": t.payout_batch_id, "paypal_txn_id": t.paypal_txn_id,
        "amount": float(t.amount), "currency": t.currency, "status": t.status,
        "created_at": t.created_at.isoformat(), "completed_at": t.completed_at.isoformat() if t.completed_at else None,
    }


@router.get("")
def list_transactions(db: Session = Depends(get_db)):
    rows = (db.query(Transaction, Invoice.number)
            .join(PaymentRequest, PaymentRequest.id == Transaction.payment_request_id)
            .join(Invoice, Invoice.id == PaymentRequest.invoice_id)
            .order_by(Transaction.id.desc()))
    return [txn_dict(t, n) for t, n in rows]


@router.post("/{txn_id}/refresh")
def refresh(txn_id: int, db: Session = Depends(get_db)):
    txn = db.get(Transaction, txn_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    refresh_transaction(db, txn, get_paypal())
    db.commit()
    return {"id": txn.id, "status": txn.status}
