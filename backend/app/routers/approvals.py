import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
from ..models import Invoice, PaymentRequest, Supplier, User
from ..schemas import RejectIn, SignIn
from ..services.audit import audit
from ..services.mandate import verify_signature
from ..services.paypal_client import get_paypal
from ..services.pipeline import execute_payout, summarize

router = APIRouter(prefix="/approvals", tags=["approvals"], dependencies=[Depends(current_user)])


def awaiting(db: Session, pr_id: int) -> tuple[PaymentRequest, Invoice]:
    pr = db.get(PaymentRequest, pr_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Payment request not found")
    if pr.status != "AWAITING_APPROVAL":
        raise HTTPException(status_code=409, detail=f"Request is {pr.status}, not awaiting approval")
    return pr, db.get(Invoice, pr.invoice_id)


@router.get("")
def list_approvals(db: Session = Depends(get_db)):
    rows = (db.query(PaymentRequest, Invoice, Supplier)
            .join(Invoice, Invoice.id == PaymentRequest.invoice_id)
            .join(Supplier, Supplier.id == Invoice.supplier_id)
            .filter(PaymentRequest.status == "AWAITING_APPROVAL").order_by(PaymentRequest.id))
    return [{"id": p.id, "invoice": i.number, "supplier": s.name, "amount": float(p.amount), "currency": p.currency,
             "risk": p.risk_level, "reasons": p.reasons, "cart_payload": p.cart_payload,
             "created_at": p.created_at.isoformat()} for p, i, s in rows]


@router.post("/{pr_id}/approve")
def approve(pr_id: int, body: SignIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """The owner signed the exact cart in the browser. The verifier re-checks everything before PayPal is called."""
    pr, inv = awaiting(db, pr_id)
    if not pr.cart_payload:
        raise HTTPException(status_code=409, detail="No cart: there was no active signed policy when this was requested")
    if datetime.fromisoformat(json.loads(pr.cart_payload)["expires_at"]) < datetime.utcnow():
        pr.status, inv.status = "EXPIRED", "PENDING"
        audit(db, pr.id, "approval_expired", {})
        db.commit()
        raise HTTPException(status_code=409, detail="Approval expired. Submit the invoice again.")
    if not user.public_key or not verify_signature(user.public_key, pr.cart_payload, body.signature):
        raise HTTPException(status_code=400, detail="Signature invalid")  # request stays open for a retry
    # Claim the request atomically so a double click cannot approve (and pay) twice
    claimed = (db.query(PaymentRequest).filter(PaymentRequest.id == pr.id, PaymentRequest.status == "AWAITING_APPROVAL")
               .update({"status": "APPROVING"}, synchronize_session=False))
    if not claimed:
        db.rollback()
        raise HTTPException(status_code=409, detail="This request is already being approved")
    db.refresh(pr)
    pr.cart_signature = body.signature
    audit(db, pr.id, "approved", {"user": user.email})
    execute_payout(db, pr, inv, get_paypal())
    db.commit()
    return summarize(db, pr, inv)


@router.post("/{pr_id}/reject")
def reject(pr_id: int, body: RejectIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    pr, inv = awaiting(db, pr_id)
    pr.status, inv.status = "REJECTED", "REJECTED"
    audit(db, pr.id, "rejected", {"user": user.email, "reason": body.reason})
    db.commit()
    return summarize(db, pr, inv)
