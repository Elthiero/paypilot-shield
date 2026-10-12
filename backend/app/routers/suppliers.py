from collections import Counter
from statistics import median

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
from ..models import Invoice, PaymentRequest, Supplier, Transaction
from ..services.audit import audit

router = APIRouter(prefix="/suppliers", tags=["suppliers"], dependencies=[Depends(current_user)])


class SupplierIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    paypal_email: str = Field(max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    country: str = Field("US", pattern=r"^[A-Z]{2}$")


def supplier_dict(s: Supplier):
    return {"id": s.id, "name": s.name, "paypal_email": s.paypal_email, "verified": s.verified,
            "last_payout_email": s.last_payout_email, "country": s.country}


@router.post("", status_code=201)
def create_supplier(body: SupplierIn, db: Session = Depends(get_db), user=Depends(current_user)):
    sup = Supplier(name=body.name.strip(), paypal_email=body.paypal_email.strip(), country=body.country, verified=False)
    db.add(sup)
    db.flush()
    audit(db, None, "supplier_created", {"supplier_id": sup.id, "name": sup.name, "by": user.email})
    db.commit()
    return supplier_dict(sup)


@router.post("/{supplier_id}/verify")
def verify_supplier(supplier_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    sup = db.get(Supplier, supplier_id)
    if not sup:
        raise HTTPException(status_code=404, detail="Supplier not found")
    sup.verified = True
    audit(db, None, "supplier_verified", {"supplier_id": sup.id, "by": user.email})
    db.commit()
    return supplier_dict(sup)


@router.get("")
def list_suppliers(db: Session = Depends(get_db)):
    return [supplier_dict(s) for s in db.query(Supplier).order_by(Supplier.id)]


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
