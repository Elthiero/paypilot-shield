from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
from ..models import Invoice, Supplier

router = APIRouter(prefix="/invoices", tags=["invoices"], dependencies=[Depends(current_user)])


def invoice_dict(inv: Invoice, sup: Supplier | None):
    return {
        "id": inv.id, "number": inv.number, "supplier": sup.name if sup else None,
        "supplier_verified": sup.verified if sup else None,
        "description": inv.description, "amount": float(inv.amount), "currency": inv.currency,
        "payee_email": inv.payee_email, "status": inv.status,
    }


@router.get("")
def list_invoices(db: Session = Depends(get_db)):
    rows = db.query(Invoice, Supplier).join(Supplier, Supplier.id == Invoice.supplier_id).order_by(Invoice.number)
    return [invoice_dict(i, s) for i, s in rows]


@router.get("/{number}")
def get_invoice(number: str, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter_by(number=number.upper()).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice_dict(inv, db.get(Supplier, inv.supplier_id))
