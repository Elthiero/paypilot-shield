import { Check, PenLine, Send } from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import Banner from "../components/Banner";
import Button from "../components/Button";
import SectionTag from "../components/SectionTag";
import StatusBadge from "../components/StatusBadge";
import DecisionCard from "../components/DecisionCard";
import StepBlock from "../components/StepBlock";
import { refreshShell } from "../components/Shell";
import { ApiError, api } from "../lib/api";
import { money } from "../lib/format";
import type { AgentReply, AgentToolCall, PaymentSummary } from "../lib/types";

interface Msg { role: "user" | "agent"; text: string; reply?: AgentReply; error?: boolean; }

const STARTERS: [string, string, string][] = [
  ["Pay INV-001", "bg-yellow", "-rotate-2"],
  ["Pay INV-003", "bg-mint", "rotate-1.5"],
  ["Why was INV-004 blocked?", "bg-rose", "-rotate-1"],
  ["List invoices", "bg-yellow", "rotate-1"],
];
const asRec = (v: unknown): Record<string, unknown> => (v && typeof v === "object" ? (v as Record<string, unknown>) : {});

/** One plain line per tool result, so the side panel says what the tool found. */
function toolSummary(t: AgentToolCall): string {
  if (typeof t.output === "string") return t.output;
  const o = asRec(t.output);
  if (typeof o.error === "string") return o.error;
  switch (t.tool) {
    case "get_invoice": return `${o.supplier}, ${money(Number(o.amount))}, ${o.status}${o.supplier_verified === false ? ", supplier not verified" : ""}`;
    case "list_invoices": return `${Array.isArray(o.invoices) ? o.invoices.length : 0} invoices`;
    case "get_supplier": return `${o.name}, ${o.verified ? "verified" : "not verified"}, ${o.country}`;
    case "get_policy": return `Auto limit ${money(Number(o.auto_limit))}, budget ${money(Number(o.monthly_budget))}, ${o.signed ? "signed" : "not signed"}`;
    case "explain_request": return `${Array.isArray(o.events) ? o.events.length : 0} audit steps`;
    case "submit_payment_request": return o.note ? String(o.note) : `${o.decision}: ${o.status}`;
    default: return "Done.";
  }
}

/** Models answer in Markdown. Only **bold** is rendered, as React elements, never as HTML. */
function Bold({ text }: { text: string }) {
  return <>{text.split(/(\*\*[^*\n]+\*\*)/).map((part, i) => part.startsWith("**") && part.endsWith("**") && part.length > 4
    ? <strong key={i}>{part.slice(2, -2)}</strong> : part)}</>;
}

const MODE = { rules: "Rules mode", llm: "AI mode", rules_fallback: "AI fallback to rules" } as const;

export default function AgentChat() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ block: "nearest" }); }, [msgs]);

  const send = async (message: string) => {
    if (!message.trim() || busy) return;
    setMsgs((m) => [...m, { role: "user", text: message }]);
    setText("");
    setBusy(true);
    try {
      const reply = await api<AgentReply>("/agent/chat", { body: { message } });
      setMsgs((m) => [...m, { role: "agent", text: reply.reply, reply }]);
      refreshShell();
    } catch (e) {
      setMsgs((m) => [...m, { role: "agent", error: true, text: e instanceof ApiError ? e.detail : "I could not reach the server." }]);
    } finally {
      setBusy(false);
    }
  };

  const last = [...msgs].reverse().find((m) => m.reply)?.reply;
  const submit: PaymentSummary | undefined = last?.trace.find((t: AgentToolCall) => t.tool === "submit_payment_request")?.output as PaymentSummary | undefined;

  return (
    <div>
      <section className="text-center pt-4 pb-8">
        <p className="note -rotate-2 inline-block text-[22px]">hi owner, what are we paying today?</p>
        <h1 className="!text-[44px] !leading-[50px] tracking-[-0.02em]">The AI asks. The rules decide.</h1>
        <div className="flex gap-4 justify-center mt-4">
          <StatusBadge value="AUTO_PAY" rotate={-2} />
          <span className="label inline-flex items-center gap-1.5 bg-yellow border border-ink rounded shadow-hard-sm px-2.5 py-1 rotate-1.5"><PenLine size={12} strokeWidth={3} aria-hidden />You sign</span>
          <StatusBadge value="BLOCKED" rotate={-1} /> 
        </div>
      </section>
      <div className="flex gap-8 flex-wrap items-start">
        <section className="flex-1 min-w-[320px]" aria-labelledby="chat-h">
          <div className="mb-4"><SectionTag id="chat-h">chat</SectionTag></div>
          <div className="space-y-4 min-h-[200px]" aria-live="polite">
            {msgs.map((m, i) => m.role === "user" ? (
              <div key={i} className="flex justify-end"><p className="bg-blue text-white border border-ink rounded shadow-hard px-4 py-3 max-w-[420px]">{m.text}</p></div>
            ) : m.error ? (
              <div key={i} className="max-w-[640px]"><Banner kind="error" title="The agent could not answer">{m.text}</Banner></div>
            ) : (
              <div key={i} className="flex gap-3">
                <span className="w-[34px] h-[34px] shrink-0 rounded-full bg-pink border border-ink flex items-center justify-center"><Check size={18} strokeWidth={3} aria-hidden /></span>
                <div>
                  <p className="bg-card border border-ink rounded shadow-hard px-4 py-3 max-w-[640px] whitespace-pre-wrap"><Bold text={m.text} /></p>
                  {m.reply && (
                    <p className="label text-ink-mute mt-2">
                      {MODE[m.reply.mode]}
                      {m.reply.payment_request_id && <> <Link className="text-blue underline ml-2" to={`/replay/${m.reply.payment_request_id}`}>View decision</Link></>}
                    </p>
                  )}
                </div>
              </div>
            ))}
            {busy && <p className="label text-ink-mute">Agent is working...</p>}
            <div ref={end} />
          </div>
          <div className="flex gap-3 flex-wrap my-5">
            {STARTERS.map(([s, c, r]) => (
              <Button key={s} variant="chip" onClick={() => send(s)} disabled={busy} className={`${c} ${r}`}>{s}</Button>
            ))}
          </div>
          <form onSubmit={(e: FormEvent) => { e.preventDefault(); void send(text); }} className="flex gap-3">
            <label className="flex-1"><span className="sr-only">Message to the agent</span>
              <input className="input !h-[50px]" value={text} onChange={(e) => setText(e.target.value)} placeholder="Ask the agent, e.g. Pay INV-003" /></label>
            <Button type="submit" loading={busy} className="!h-[50px]"><Send size={14} aria-hidden />Send</Button>
          </form>
          <p className="note text-[18px] mt-3">The agent can only request payments. A rules engine decides.</p>
        </section>
        <aside className="w-[412px] max-w-full min-[1100px]:sticky min-[1100px]:top-16 min-[1100px]:self-start min-[1100px]:max-h-[calc(100vh-5rem)] min-[1100px]:overflow-y-auto p-4 -m-4 space-y-4" aria-labelledby="did-h">
          <SectionTag id="did-h">what the agent did</SectionTag>
          {!last && <p className="text-[14px] text-ink-mute">Tool calls and the rules decision show up here.</p>}
          {submit?.decision && (
            <div className="pt-3"><DecisionCard invoice={submit.invoice} amount={submit.amount} decision={submit.decision} risk={submit.risk} reasons={submit.reasons} tilt={0.6} /></div>
          )}
          {last?.trace.map((t, i) => (
            <StepBlock key={i} index={i} tab={t.tool} failed={t.tool === "llm_error"}>
              <p className="font-mono text-[13px] break-all">{JSON.stringify(t.input ?? {})}</p>
              <p className="text-[13px] text-step mt-1 break-words">{toolSummary(t)}</p>
            </StepBlock>
          ))}
        </aside>
      </div>
    </div>
  );
}
