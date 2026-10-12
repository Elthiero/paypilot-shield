from collections import Counter
from statistics import median

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
from ..models import Invoice, PaymentRequest, Supplier, Transaction

router = APIRouter(prefix="/suppliers", tags=["suppliers"], dependencies=[Depends(current_user)])


@router.get("")
def list_suppliers(db: Session = Depends(get_db)):
    return [
        {"id": s.id, "name": s.name, "paypal_email": s.paypal_email, "verified": s.verified,
         "last_payout_email": s.last_payout_email, "country": s.country}
        for s in db.query(Supplier).order_by(Supplier.id)
    ]


@router.get("/{supplier_id}/analytics")
def supplier_analytics(supplier_id: int, db: Session = Depends(get_db)):
    sup = db.get(Supplier, supplier_id)
    if not sup:
        raise HTTPException(status_code=404, detail="Supplier not found")
    prs = (db.query(PaymentRequest, Invoice).join(Invoice, Invoice.id == PaymentRequest.invoice_id)
           .filter(Invoice.supplier_id == supplier_id).order_by(PaymentRequest.id.desc()).all())
    paid = (db.query(Transaction, Invoice.number)
            .join(PaymentRequest, PaymentRequest.id == Transaction.payment_request_id)
            .join(Invoice, Invoice.id == PaymentRequest.invoice_id)
            .filter(Invoice.supplier_id == supplier_id, Transaction.status == "SUCCESS")
            .order_by(Transaction.created_at).all())
    amounts = [float(t.amount) for t, _ in paid]
    flags = Counter(r["code"] for pr, _ in prs for r in (pr.reasons or []) if isinstance(r, dict) and r["level"] != "info")
    return {
        "supplier": {"id": sup.id, "name": sup.name, "verified": sup.verified, "country": sup.country},
        "invoices": db.query(Invoice).filter_by(supplier_id=supplier_id).count(),
        "requests": len(prs),
        "decisions": dict(Counter(pr.decision for pr, _ in prs if pr.decision)),
        "paid_count": len(amounts),
        "paid_total": sum(amounts),
        "paid_median": median(amounts) if amounts else None,
        "paid_max": max(amounts) if amounts else None,
        "last_paid_at": paid[-1][0].created_at.isoformat() if paid else None,
        "flags": dict(flags.most_common()),
        "payments": [{"invoice": n, "amount": float(t.amount), "currency": t.currency, "at": t.created_at.isoformat()} for t, n in paid],
    }
