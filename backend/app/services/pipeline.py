"""The request pipeline. Plain Python, no LLM. Layer 1 has no signatures yet."""
import calendar
import hashlib
import json
from datetime import date, datetime, timedelta
from decimal import Decimal

import httpx
from sqlalchemy import func, text

from ..config import settings
from ..models import AuditEvent, Invoice, Mandate, PaymentRequest, Supplier, Transaction, User
from .audit import audit
from .mandate import build_cart_payload, signed_rules
from .decision import decide
from .paypal_client import get_paypal
from .truth_check import reason, run_truth_check
from .verifier import verify_before_payment


CART_HOURS = 24


def default_rules() -> dict:
    return {
        "auto_limit": Decimal(str(settings.default_auto_limit)),
        "monthly_budget": Decimal(str(settings.default_monthly_budget)),
    }


def active_policy(db):
    """(mandate, user) for the active, unexpired signed policy, or (None, None). Single owner app."""
    m = db.query(Mandate).filter_by(active=True).order_by(Mandate.id.desc()).first()
    if not m or date.fromisoformat(signed_rules(m)["valid_until"]) < date.today():
        return None, None
    return m, db.get(User, m.user_id)


def policy_rules(mandate) -> dict:
    """Signed rules when a policy is active, otherwise the config defaults (payment is then refused anyway)."""
    if not mandate:
        return default_rules()
    r = signed_rules(mandate)
    return {"auto_limit": Decimal(str(r["auto_limit"])), "monthly_budget": Decimal(str(r["monthly_budget"]))}


def invoice_hash(inv: Invoice) -> str:
    material = json.dumps({
        "number": inv.number, "supplier_id": inv.supplier_id, "payee_email": inv.payee_email,
        "amount": f"{Decimal(inv.amount):.2f}", "currency": inv.currency, "description": inv.description,
    }, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def supplier_history(db, supplier_id: int) -> list:
    rows = (db.query(Transaction.amount)
            .join(PaymentRequest, PaymentRequest.id == Transaction.payment_request_id)
            .join(Invoice, Invoice.id == PaymentRequest.invoice_id)
            .filter(Invoice.supplier_id == supplier_id, Transaction.status == "SUCCESS").all())
    return [float(r[0]) for r in rows]


def spent_this_month(db) -> Decimal:
    start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total = (db.query(func.coalesce(func.sum(Transaction.amount), 0))
             .filter(Transaction.status.in_(["SUCCESS", "PENDING"]), Transaction.created_at >= start).scalar())
    return Decimal(str(total or 0))


def get_trace(db, pr_id: int) -> list:
    rows = db.query(AuditEvent).filter_by(payment_request_id=pr_id).order_by(AuditEvent.id).all()
    return [{"id": e.id, "step": e.step, "detail": e.detail, "at": e.created_at.isoformat()} for e in rows]


def summarize(db, pr: PaymentRequest, inv: Invoice) -> dict:
    txn = db.query(Transaction).filter_by(payment_request_id=pr.id).order_by(Transaction.id.desc()).first()
    return {
        "ok": True, "payment_request_id": pr.id, "invoice": inv.number, "amount": float(pr.amount),
        "decision": pr.decision, "risk": pr.risk_level, "reasons": pr.reasons or [], "status": pr.status,
        "transaction": None if not txn else {
            "id": txn.id, "status": txn.status, "payout_batch_id": txn.payout_batch_id, "paypal_txn_id": txn.paypal_txn_id,
        },
    }


def refresh_transaction(db, txn: Transaction, paypal) -> Transaction:
    """Poll PayPal for the payout status and update the transaction, request and invoice."""
    if txn.status != "PENDING":
        return txn
    data = paypal.get_batch(txn.payout_batch_id)
    batch_status = data["batch_header"]["batch_status"]
    items = data.get("items", [])
    pr = db.get(PaymentRequest, txn.payment_request_id)
    inv = db.get(Invoice, pr.invoice_id)
    if batch_status == "SUCCESS":
        txn.status = "SUCCESS"
        txn.paypal_txn_id = (items[0].get("transaction_id") if items else None)
        txn.completed_at = datetime.utcnow()
        pr.status = "PAID"
        inv.status = "PAID"
        audit(db, pr.id, "payout_confirmed", {"batch_status": batch_status, "paypal_txn_id": txn.paypal_txn_id})
    elif batch_status in ("DENIED", "CANCELED", "FAILED"):
        txn.status = "FAILED"
        txn.completed_at = datetime.utcnow()
        pr.status = "FAILED"
        inv.status = "FAILED"
        audit(db, pr.id, "payout_failed", {"batch_status": batch_status,
                                           "items": [i.get("transaction_status") for i in items]})
    return txn


def sender_batch_id(pr: PaymentRequest) -> str:
    """PayPal's sender_batch_id. Same for every attempt on one request, so PayPal refuses a second payout for it.
    The creation time keeps it unique across a database reset (seed.py restarts request ids at 1), and
    the whole id stays under PayPal's 30 character limit."""
    return f"pp{pr.id}-{calendar.timegm(pr.created_at.utctimetuple())}"


PAYOUT_LOCK = 7001  # arbitrary advisory lock id


def execute_payout(db, pr: PaymentRequest, inv: Invoice, paypal, wait: bool = True) -> None:
    """The only place in the codebase that moves money. The verifier runs here, so no caller can skip it."""
    # One payout at a time reads and spends the monthly budget. The lock is released by the caller's commit,
    # so the next payout sees this one's transaction. SQLite (tests, dev) has one writer, so it needs none.
    # ponytail: a global lock serializes payouts, fine at this volume.
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": PAYOUT_LOCK})
    mandate, user = active_policy(db)
    paid = db.query(Transaction).filter(Transaction.payment_request_id == pr.id,
                                        Transaction.status.in_(["SUCCESS", "PENDING"])).count() > 0
    failures = verify_before_payment(pr, inv, invoice_hash(inv), spent_this_month(db), mandate, user, paid)
    if failures:
        pr.status, pr.decision, pr.risk_level = "BLOCKED", "BLOCKED", "HIGH"  # the audit trail keeps the rules' original decision
        pr.reasons = [reason("verifier_refused", "block", f) for f in failures]
        inv.status = "BLOCKED"
        audit(db, pr.id, "verifier_failed", {"failures": failures, "paypal_called": False})
        return
    audit(db, pr.id, "verifier_passed", {"mandate_id": mandate.id})
    batch_id = sender_batch_id(pr)
    try:
        resp = paypal.send_payout(batch_id, pr.payee_email, Decimal(pr.amount), pr.currency,
                                  f"Invoice {inv.number}")
    except httpx.HTTPStatusError as e:
        pr.status = "FAILED"
        inv.status = "FAILED"
        audit(db, pr.id, "payout_error", {"http_status": e.response.status_code, "body": e.response.text[:500]})
        return
    payout_batch_id = resp["batch_header"]["payout_batch_id"]
    txn = Transaction(payment_request_id=pr.id, payout_batch_id=payout_batch_id, amount=pr.amount,
                      currency=pr.currency, status="PENDING")
    db.add(txn)
    pr.status = "SENT"
    inv.status = "SENT"
    db.flush()
    audit(db, pr.id, "payout_sent", {"sender_batch_id": batch_id, "payout_batch_id": payout_batch_id,
                                     "receiver": pr.payee_email, "amount": float(pr.amount)})
    if not wait:
        return
    # One check, no waiting. A real sandbox payout stays PENDING for about 35 s, so polling here only delayed the
    # reply. The PayPal webhook, the Payments page poll and Refresh settle it.
    refresh_transaction(db, txn, paypal)


def submit_payment_request(db, invoice_number: str, paypal=None, wait: bool = True) -> dict:
    paypal = paypal or get_paypal()
    inv = db.query(Invoice).filter_by(number=invoice_number.strip().upper()).first()
    if not inv:
        return {"ok": False, "error": f"Invoice {invoice_number} not found"}
    sup = db.get(Supplier, inv.supplier_id)

    # Idempotency: never create a second payment for something already paid or in flight
    if inv.status in ("PAID", "SENT", "AWAITING_APPROVAL"):
        existing = (db.query(PaymentRequest).filter_by(invoice_id=inv.id)
                    .order_by(PaymentRequest.id.desc()).first())
        if existing:
            out = summarize(db, existing, inv)
            out["note"] = f"Invoice is already {inv.status}. No new request was created."
            return out

    # Claim the invoice atomically so two simultaneous requests cannot both evaluate (and pay) it
    claimed = (db.query(Invoice).filter(Invoice.id == inv.id, Invoice.status == inv.status)
               .update({"status": "EVALUATING"}, synchronize_session=False))
    if not claimed:
        db.rollback()
        return {"ok": False, "error": f"Invoice {inv.number} is being processed by another request. Try again."}
    db.refresh(inv)

    pr = PaymentRequest(invoice_id=inv.id, invoice_hash=invoice_hash(inv), payee_email=inv.payee_email,
                        amount=inv.amount, currency=inv.currency, status="RECEIVED")
    db.add(pr)
    db.flush()
    audit(db, pr.id, "request_received", {"invoice": inv.number})
    audit(db, pr.id, "invoice_loaded", {"supplier": sup.name, "amount": float(inv.amount),
                                        "payee_email": inv.payee_email, "invoice_hash": pr.invoice_hash})

    history = supplier_history(db, sup.id)
    audit(db, pr.id, "supplier_history_checked", {"successful_payouts": len(history)})

    signals = run_truth_check(db, inv, sup, history)
    audit(db, pr.id, "truth_check_done", signals.as_dict())

    mandate, _ = active_policy(db)
    rules = policy_rules(mandate)
    pr.mandate_id = mandate.id if mandate else None
    spent = spent_this_month(db)
    decision, risk, reasons = decide(rules, signals, spent, Decimal(inv.amount))
    pr.decision, pr.risk_level, pr.reasons = decision, risk, reasons
    audit(db, pr.id, "decision_made", {"decision": decision, "risk": risk, "reasons": reasons,
                                       "rules": {k: float(v) for k, v in rules.items()},
                                       "spent_this_month": float(spent)})

    if decision == "BLOCKED":
        pr.status = "BLOCKED"
        inv.status = "BLOCKED"
        audit(db, pr.id, "blocked_no_payout", {"paypal_called": False})
    elif decision == "NEEDS_APPROVAL":
        pr.status = "AWAITING_APPROVAL"
        inv.status = "AWAITING_APPROVAL"
        if mandate:  # without a signed policy the approval can be requested but never executed
            expires = (datetime.utcnow() + timedelta(hours=CART_HOURS)).isoformat(timespec="seconds")
            pr.cart_payload = build_cart_payload(mandate.id, inv.number, pr, expires)
        audit(db, pr.id, "approval_requested", {"reasons": reasons})
    else:
        execute_payout(db, pr, inv, paypal, wait=wait)

    db.commit()
    return summarize(db, pr, inv)
