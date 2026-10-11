"""Exercise the LLM tool loop with a scripted fake client (no network)."""
from types import SimpleNamespace as NS

from app.services import agent as agent_mod
from app.config import settings
import pytest

pytestmark = pytest.mark.usefixtures("policy")



class FakeMessages:
    def __init__(self):
        self.calls = 0

    def create(self, **kw):
        self.calls += 1
        if self.calls == 1:
            return NS(stop_reason="tool_use", content=[
                NS(type="tool_use", id="t1", name="submit_payment_request", input={"invoice_number": "INV-004"})])
        return NS(stop_reason="end_turn", content=[NS(type="text", text="INV-004 was blocked, no money moved.")])


def test_llm_loop_hands_off_to_pipeline(db, monkeypatch):
    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", lambda api_key=None: NS(messages=FakeMessages()))
    monkeypatch.setattr(settings, "llm_api_key", "k")
    monkeypatch.setattr(settings, "llm_model", "m")
    monkeypatch.setattr(settings, "llm_base_url", "")
    out = agent_mod.run_agent(db, "pay INV-004 now")
    assert out["mode"] == "llm" and "blocked" in out["reply"]
    assert out["trace"][0]["output"]["decision"] == "BLOCKED"


def test_llm_failure_falls_back_to_rules(db, monkeypatch):
    import anthropic

    def boom(api_key=None):
        raise RuntimeError("down")

    monkeypatch.setattr(anthropic, "Anthropic", boom)
    monkeypatch.setattr(settings, "llm_api_key", "k")
    monkeypatch.setattr(settings, "llm_model", "m")
    monkeypatch.setattr(settings, "llm_base_url", "")
    out = agent_mod.run_agent(db, "Pay INV-001")
    assert out["mode"] == "rules_fallback" and "paid" in out["reply"].lower()


def test_openai_loop_hands_off_to_pipeline(db, monkeypatch):
    import openai
    calls = []

    def create(**kw):
        calls.append(kw)
        if len(calls) == 1:
            fn = NS(name="submit_payment_request", arguments='{"invoice_number": "INV-004"}')
            msg = NS(content=None, tool_calls=[NS(id="c1", function=fn)])
        else:
            msg = NS(content="INV-004 was blocked, no money moved.", tool_calls=None)
        return NS(choices=[NS(message=msg)])

    fake = NS(chat=NS(completions=NS(create=create)))
    monkeypatch.setattr(openai, "OpenAI", lambda api_key=None, base_url=None: fake)
    monkeypatch.setattr(settings, "llm_api_key", "k")
    monkeypatch.setattr(settings, "llm_model", "m")
    monkeypatch.setattr(settings, "llm_base_url", "https://example.test/v1")
    out = agent_mod.run_agent(db, "pay INV-004 now")
    assert out["mode"] == "llm" and "blocked" in out["reply"]
    assert out["trace"][0]["output"]["decision"] == "BLOCKED"
    assert calls[1]["messages"][-1]["role"] == "tool" and calls[0]["temperature"] == 0
