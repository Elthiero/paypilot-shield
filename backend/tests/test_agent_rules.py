import pytest

from app.services.agent import run_agent
from app.services.pipeline import submit_payment_request

pytestmark = pytest.mark.usefixtures("policy")


def say(db, msg):
    return run_agent(db, msg)


@pytest.mark.parametrize("msg", ["pay invoice 1", "Pay Invoice #1", "pay inv 1", "pay INV-001", "pay invoice-1"])
def test_pay_phrasings_all_find_the_invoice(db, msg):
    r = say(db, msg)
    assert "INV-001" in r["reply"] and r["payment_request_id"]


def test_list_filters_by_status(db):
    submit_payment_request(db, "INV-001")
    paid = say(db, "show paid invoices")["reply"]
    assert "INV-001" in paid and "INV-002" not in paid
    pending = say(db, "which invoices are pending?")["reply"]
    assert "INV-001" not in pending and "INV-002" in pending
    assert "No invoices" in say(db, "show failed invoices")["reply"]


def test_list_without_status_still_lists_everything(db):
    r = say(db, "list invoices")["reply"]
    assert all(f"INV-00{i}" in r for i in range(1, 6))


def test_pay_all_pending_runs_each_through_the_pipeline(db, spy, monkeypatch):
    monkeypatch.setattr("app.services.pipeline.get_paypal", lambda: spy)
    r = say(db, "pay all pending invoices")["reply"]
    lines = r.splitlines()
    assert any(l.startswith("INV-001") and "PAID" in l for l in lines)
    assert any(l.startswith("INV-003") and "AWAITING_APPROVAL" in l for l in lines)
    assert any(l.startswith("INV-004") and "BLOCKED" in l and "not verified" in l for l in lines)
    assert any(l.startswith("INV-005") and "BLOCKED" in l for l in lines)
    assert sorted(p[1] for p in spy.payouts) == ["abc@x.test", "tech@x.test"]  # only the two clean invoices were paid


def test_pay_all_with_nothing_pending(db):
    for n in ("INV-001", "INV-002", "INV-003", "INV-004", "INV-005"):
        submit_payment_request(db, n)
    assert "No pending" in say(db, "pay all pending")["reply"]


def test_list_invoices_accepts_a_null_status(db):
    # gpt-oss sends {"status": null} for "no filter"; Groq rejects the call unless the schema allows it
    from app.services.agent import TOOLS, run_tool
    schema = next(t for t in TOOLS if t["name"] == "list_invoices")["input_schema"]["properties"]["status"]
    assert "null" in schema["type"] and None in schema["enum"]
    assert len(run_tool(db, "list_invoices", {"status": None})["invoices"]) == len(run_tool(db, "list_invoices", {})["invoices"])
