import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
from ..models import Invoice, PaymentRequest, Supplier
from ..schemas import PaymentIn
from ..services.paypal_client import get_paypal
from ..services.pipeline import get_trace, submit_payment_request, summarize

log = logging.getLogger(__name__)
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


_balance = {"at": 0.0, "value": None}


@router.get("/balance")
def paypal_balance():
    """The PayPal account balance, cached for 20 s. Never an error: the page just shows it as unavailable."""
    if _balance["value"] is None or time.time() - _balance["at"] > 20:
        try:
            _balance["value"] = {"ok": True, **get_paypal().get_balance()}
        except Exception as e:  # missing Transaction Search permission, outage, bad credentials
            code = getattr(getattr(e, "response", None), "status_code", None)
            log.warning("PayPal balance unavailable: %s", e)
            _balance["value"] = {"ok": False, "error": f"PayPal returned {code}" if code else "PayPal balance unavailable"}
        _balance["at"] = time.time()
    return _balance["value"]


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
