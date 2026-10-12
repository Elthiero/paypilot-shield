import { useState } from "react";
import Banner from "../components/Banner";
import Button from "../components/Button";
import ErrorState from "../components/ErrorState";
import PageHeader from "../components/PageHeader";
import PasswordPrompt from "../components/PasswordPrompt";
import PolicyEditor from "../components/PolicyEditor";
import type { PolicyDraft } from "../components/PolicyEditor";
import { refreshShell } from "../components/Shell";
import SigningModal from "../components/SigningModal";
import Skeleton from "../components/Skeleton";
import StatusBadge from "../components/StatusBadge";
import useApi from "../hooks/useApi";
import { ApiError, api } from "../lib/api";
import { useHealth } from "../hooks/useHealth";
import { resetKey } from "../lib/crypto";
import { money } from "../lib/format";
import type { Mandate } from "../lib/types";


function Rules({ m }: { m: Mandate }) {
  const cur = m.rules.currency;
  const rows: [string, string][] = [
    ["Auto limit", money(Number(m.rules.auto_limit), cur)],
    ["Monthly budget", money(Number(m.rules.monthly_budget), cur)],
    ["Verified suppliers only", m.rules.require_verified ? "Yes" : "No"],
    ["Valid until", m.valid_until ?? ""],
  ];
  return (
    <dl className="grid grid-cols-[1fr_auto] gap-y-2 text-[14px]">
      {rows.map(([k, v]) => (<div key={k} className="contents"><dt className="text-ink-mute">{k}</dt><dd className="font-bold money text-right">{v}</dd></div>))}
    </dl>
  );
}

export default function Policy() {
  const health = useHealth();
  const active = useApi<Mandate | null>("/mandates/active");
  const history = useApi<Mandate[]>("/mandates");
  const [draft, setDraft] = useState<PolicyDraft | null>(null);
  const [prep, setPrep] = useState<{ mandate_id: number; payload: string } | null>(null);
  const [prepError, setPrepError] = useState<string | null>(null);
  const [askPassword, setAskPassword] = useState(false);
  const [notice, setNotice] = useState<{ kind: "info" | "error"; text: string } | null>(null);

  const reloadAll = () => { active.reload(); history.reload(); refreshShell(); };

  const start = async (d: PolicyDraft) => {
    setDraft(d); setPrep(null); setPrepError(null);
    try {
      setPrep(await api<{ mandate_id: number; payload: string }>("/mandates/prepare", { body: d }));
    } catch (e) {
      setPrepError(e instanceof ApiError ? e.detail : "Could not prepare the policy.");
    }
  };

  const confirm = async (signature: string) => {
    const m = await api<Mandate>(`/mandates/${prep!.mandate_id}/sign`, { body: { signature } });
    reloadAll();
    return <p>Policy {m.id} is active until {m.valid_until}. Payments now follow these rules.</p>;
  };

  const tamper = async () => {
    if (!active.data) return;
    try {
      await api(`/dev/mandates/${active.data.id}/tamper`, { method: "POST", body: {} });
      setNotice({ kind: "error", text: "Policy tampered. Payments are now refused until you sign a new one." });
      reloadAll();
    } catch (e) {
      setNotice({ kind: "error", text: e instanceof ApiError ? e.detail : "Tamper helper unavailable." });
    }
  };

  const reset = async (password: string) => {
    await resetKey(password);
    setNotice({ kind: "info", text: "New signing key created. Sign the policy again." });
    reloadAll();
  };

  const m = active.data;
  return (
    <div>
      <PageHeader note="your rules" title="Policy" text="The spending rules you signed. Nothing is paid outside them." />
      {notice && <div className="mb-4"><Banner kind={notice.kind} title={notice.text} /></div>}
      <div className="flex gap-6 flex-wrap items-start">
        <div className="flex-1 min-w-[320px] space-y-6">
          <section className="card space-y-4" aria-labelledby="active-h">
            <div className="flex items-center justify-between"><h2 id="active-h">Active policy</h2>{m && <StatusBadge value={m.verified ? "VERIFIED" : "SIGNATURE_INVALID"} />}</div>
            {active.loading && !m && <Skeleton rows={2} />}
            {active.error && <ErrorState message={active.error} onRetry={active.reload} />}
            {m && (<><p className="text-[14px]">{m.policy_text}</p><Rules m={m} /></>)}
            {!active.loading && !active.error && !m && <p className="note">no signed policy yet</p>}
          </section>
          <section className="card space-y-3" aria-labelledby="hist-h">
            <h2 id="hist-h">History</h2>
            {history.data?.length === 0 && <p className="text-[13px] text-ink-mute">No policies signed yet.</p>}
            <ul className="space-y-2">
              {history.data?.map((h) => (
                <li key={h.id} className="flex items-center justify-between text-[13px] border-b border-[1px] border-rule pb-2">
                  <span>Policy {h.id}, limit {money(Number(h.rules.auto_limit))}</span>
                  <span className="flex gap-2">{h.active && <StatusBadge value="ACTIVE" />}<StatusBadge value={h.verified ? "VERIFIED" : "SIGNATURE_INVALID"} /></span>
                </li>
              ))}
            </ul>
          </section>
          <details className="card">
            <summary className="label cursor-pointer">Demo tools</summary>
            <div className="mt-3 flex gap-3 flex-wrap">
              <Button variant="secondary" onClick={() => setAskPassword(true)}>Reset signing key</Button>
              {health?.dev_tools && <Button variant="danger" onClick={tamper} disabled={!m}>Simulate tampering</Button>}
            </div>
          </details>
        </div>
        <div className="w-[380px] max-w-full"><PolicyEditor current={m ?? null} onSubmit={start} /></div>
      </div>
      {draft && (
        <SigningModal
          confirmLabel="Sign policy"
          payload={prep?.payload ?? null}
          prepError={prepError}
          onClose={() => setDraft(null)}
          onConfirm={confirm}
          summary={
            <dl className="space-y-1 text-[14px]">
              <p>{draft.policy_text}</p>
              <p><span className="label">Auto limit</span> <b className="money">{money(Number(draft.rules.auto_limit))}</b></p>
              <p><span className="label">Monthly budget</span> <b className="money">{money(Number(draft.rules.monthly_budget))}</b></p>
              <p><span className="label">Valid until</span> {draft.rules.valid_until}</p>
            </dl>
          }
        />
      )}
      {askPassword && <PasswordPrompt title="Replace the signing key" onSubmit={reset} onClose={() => setAskPassword(false)} />}
    </div>
  );
}
