import { FormEvent, useState } from "react";
import type { Mandate, Rules } from "../lib/types";
import Banner from "./Banner";
import Button from "./Button";
import Card from "./Card";
import Input from "./Input";

export interface PolicyDraft { policy_text: string; rules: Rules; }

const inDays = (n: number) => new Date(Date.now() + n * 864e5).toISOString().slice(0, 10);

export default function PolicyEditor({ current, onSubmit }: { current: Mandate | null; onSubmit: (d: PolicyDraft) => void }) {
  const [text, setText] = useState(current?.policy_text ?? "Auto pay verified suppliers up to the limit. Ask me for anything above.");
  const [limit, setLimit] = useState(String(current?.rules.auto_limit ?? 500));
  const [budget, setBudget] = useState(String(current?.rules.monthly_budget ?? 5000));
  const [verified, setVerified] = useState(current?.rules.require_verified ?? true);
  const [until, setUntil] = useState(inDays(30));
  const [error, setError] = useState<string | null>(null);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const a = Number(limit), b = Number(budget);
    if (!(a > 0) || !(b > 0)) return setError("Limits must be numbers above zero.");
    if (a > b) return setError("The auto limit cannot be higher than the monthly budget.");
    setError(null);
    onSubmit({ policy_text: text, rules: { auto_limit: String(a), currency: "USD", monthly_budget: String(b), require_verified: verified, valid_until: until } });
  };

  const field = "block";
  return (
    <form onSubmit={submit}>
      <Card title="Edit policy" className="space-y-4">
      <label className={field}>
        <span className="label block mb-1">Policy in plain words</span>
        <textarea className="input !h-24 py-2" value={text} onChange={(e) => setText(e.target.value)} required />
      </label>
      <div className="grid grid-cols-2 gap-4">
        <Input label="Auto limit (USD)" className="money" inputMode="decimal" value={limit} onChange={(e) => setLimit(e.target.value)} required />
        <Input label="Monthly budget (USD)" className="money" inputMode="decimal" value={budget} onChange={(e) => setBudget(e.target.value)} required />
      </div>
      <Input label="Valid until" type="date" value={until} min={inDays(0)} onChange={(e) => setUntil(e.target.value)} required />
      <label className="flex items-center gap-2 text-[14px]">
        <input type="checkbox" className="w-4 h-4 accent-blue" checked={verified} onChange={(e) => setVerified(e.target.checked)} />
        Only pay verified suppliers
      </label>
      {error && <Banner kind="error" title={error} />}
      <Button type="submit" className="w-full">Review and sign</Button>
      </Card>
    </form>
  );
}
