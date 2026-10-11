from ..models import AuditEvent


def audit(db, payment_request_id, step, detail=None):
    ev = AuditEvent(payment_request_id=payment_request_id, step=step, detail=detail or {})
    db.add(ev)
    db.flush()
    return ev
