import threading
from decimal import Decimal

import pytest

from app.db import SessionLocal, engine
from app.models import Invoice, Supplier
from app.services.paypal_client import FakePayPalClient
from app.services.pipeline import submit_payment_request
from tests.conftest import make_policy


@pytest.mark.skipif(engine.dialect.name != "postgresql", reason="needs Postgres: TEST_DATABASE_URL=postgresql://... pytest")
def test_parallel_payouts_cannot_overshoot_monthly_budget(db):
    make_policy(db, auto_limit="5000")  # monthly budget is 5000
    abc = db.query(Supplier).filter_by(name="ABC Supplies").one()
    glob = db.query(Supplier).filter_by(name="Global Services").one()
    db.add_all([Invoice(number="INV-100", supplier_id=abc.id, description="Equipment", amount=Decimal("3000"), payee_email="abc@x.test"),
                Invoice(number="INV-101", supplier_id=glob.id, description="Equipment", amount=Decimal("3100"), payee_email="glob@x.test")])
    db.commit()
    barrier, out = threading.Barrier(2), {}

    def pay(number):
        s = SessionLocal()
        try:
            barrier.wait()
            out[number] = submit_payment_request(s, number, paypal=FakePayPalClient(), wait=False)["status"]
        finally:
            s.close()

    threads = [threading.Thread(target=pay, args=(n,)) for n in ("INV-100", "INV-101")]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sorted(out.values()) == ["BLOCKED", "SENT"], out  # 3000 + 3100 is over 5000: exactly one may go
