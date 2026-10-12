import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
from ..models import Invoice, Supplier
from ..schemas import InvoiceIn
from ..services.audit import audit

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


def next_number(db) -> str:
    nums = [int(m.group(1)) for (n,) in db.query(Invoice.number) if (m := re.fullmatch(r"INV-(\d+)", n))]
    return f"INV-{max(nums, default=0) + 1:03d}"


@router.post("", status_code=201)
def create_invoice(body: InvoiceIn, db: Session = Depends(get_db)):
    # The text is stored as is. The injection scan runs when payment is requested and blocks it then.
    sup = db.get(Supplier, body.supplier_id)
    if not sup:
        raise HTTPException(status_code=404, detail="Supplier not found")
    number = (body.number or next_number(db)).upper()
    if db.query(Invoice).filter_by(number=number).first():
        raise HTTPException(status_code=409, detail=f"Invoice {number} already exists")
    inv = Invoice(number=number, supplier_id=sup.id, description=body.description.strip(), amount=body.amount,
                  currency=body.currency, payee_email=body.payee_email.strip(), status="PENDING")
    db.add(inv)
    try:
        db.flush()
    except IntegrityError:  # two creates raced for the same number
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Invoice {number} already exists")
    audit(db, None, "invoice_created", {"number": number, "supplier_id": sup.id, "amount": str(body.amount)})
    db.commit()
    return invoice_dict(inv, sup)


@router.get("/{number}")
def get_invoice(number: str, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter_by(number=number.upper()).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice_dict(inv, db.get(Supplier, inv.supplier_id))
