import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Transaction
from ..services.audit import audit
from ..services.paypal_client import get_paypal
from ..services.pipeline import refresh_transaction

# Public on purpose: PayPal calls it, so there is no login. The PayPal signature is the only way in.
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _batch_id(resource: dict) -> str | None:
    """Batch events carry batch_header.payout_batch_id, item events carry payout_batch_id."""
    return (resource.get("batch_header") or {}).get("payout_batch_id") or resource.get("payout_batch_id")


@router.post("/paypal")
async def paypal_webhook(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    paypal = get_paypal()
    try:
        ok = paypal.verify_webhook({k.lower(): v for k, v in request.headers.items()}, raw)
    except Exception:
        raise HTTPException(status_code=503, detail="Could not verify the webhook")
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    try:
        event = json.loads(raw)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    # The body only says which payout changed. The status itself is fetched from PayPal, and a repeated
    # delivery finds the transaction already settled and does nothing.
    batch_id = _batch_id(event.get("resource") or {})
    txn = db.query(Transaction).filter_by(payout_batch_id=batch_id).first() if batch_id else None
    if txn and txn.status == "PENDING":
        audit(db, txn.payment_request_id, "webhook_received",
              {"event_id": event.get("id"), "event_type": event.get("event_type")})
        refresh_transaction(db, txn, paypal)
        db.commit()
    return {"ok": True}
