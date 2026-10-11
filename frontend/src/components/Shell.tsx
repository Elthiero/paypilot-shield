import { CreditCard, FileText, LogOut, MessageSquare, PenLine, ScrollText, Users } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { logout, userEmail } from "../hooks/useAuth";
import { api } from "../lib/api";
import type { ApprovalItem, Mandate } from "../lib/types";
import Banner from "./Banner";
import Button from "./Button";

const TABS = [
  { to: "/", label: "Agent", icon: MessageSquare, end: true },
  { to: "/policy", label: "Policy", icon: ScrollText },
  { to: "/approvals", label: "Approvals", icon: PenLine },
  { to: "/payments", label: "Payments", icon: CreditCard },
  { to: "/invoices", label: "Invoices", icon: FileText },
  { to: "/suppliers", label: "Suppliers", icon: Users },
];

/** Pages call this after something that changes policy or approvals so the shell refreshes. */
export function refreshShell() {
  window.dispatchEvent(new Event("paypilot:refresh"));
}

export default function Shell() {
  const nav = useNavigate();
  const [mode, setMode] = useState<string>("");
  const [policy, setPolicy] = useState<Mandate | null | undefined>(undefined);
  const [pending, setPending] = useState(0);

  const load = useCallback(async () => {
    try {
      const [p, a] = await Promise.all([api<Mandate | null>("/mandates/active"), api<ApprovalItem[]>("/approvals")]);
      setPolicy(p);
      setPending(a.length);
    } catch { /* api() already handles 401 */ }
  }, []);

  useEffect(() => {
    api<{ paypal_mode: string }>("/health").then((h) => setMode(h.paypal_mode)).catch(() => undefined);
    void load();
    const t = setInterval(load, 30000);
    window.addEventListener("paypilot:refresh", load);
    return () => { clearInterval(t); window.removeEventListener("paypilot:refresh", load); };
  }, [load]);

  const invalid = !!policy && !policy.verified;
  return (
    <div className="min-h-screen">
      <header className="bg-card border-b border-ink h-12 flex items-stretch px-3 sm:px-4 sticky top-0 z-40">
        <div className="flex items-center gap-2 pr-3 sm:pr-6">
          <span className="w-[26px] h-[26px] rounded-full bg-pink border border-ink flex items-center justify-center" aria-hidden>
            <svg width="14" height="14" viewBox="0 0 14 14"><path d="M2 7.5l3.2 3.2L12 3.5" fill="none" stroke="#111" strokeWidth="3" /></svg>
          </span>
          <span className="font-pixel font-bold text-sm hidden sm:inline">PAYPILOT</span>
        </div>
        <nav className="flex items-stretch" aria-label="Main">
          {TABS.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end}
              title={label} aria-label={label}
              className={({ isActive }) => `label flex items-center gap-1.5 px-2.5 min-[1100px]:px-3.5 ${isActive ? "bg-yellow" : "hover:bg-butter"}`}>
              <Icon size={14} aria-hidden />
              <span className="hidden min-[1100px]:inline">{label}</span>
              {label === "Approvals" && pending > 0 && <span className="bg-blue text-white rounded px-1.5 text-[10px]" aria-label={`${pending} pending`}>{pending}</span>}
              {label === "Policy" && invalid && <span className="w-2 h-2 rounded-full bg-pink border border-ink" aria-label="Policy invalid" />}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2 sm:gap-3 pl-2">
          {mode && <span className="label hidden sm:flex bg-mint border border-ink rounded px-2 py-0.5 flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-ink" />{mode === "fake" ? "Fake" : "Sandbox"}</span>}
          <span className="font-mono text-[11px] hidden xl:inline">{userEmail()}</span>
          <Button variant="secondary" className="!h-8 !px-2.5" title="Sign out" aria-label="Sign out" onClick={() => { logout(); nav("/login"); }}><LogOut size={14} aria-hidden /><span className="hidden md:inline">Sign out</span></Button>
        </div>
      </header>
      <div className="px-4 sm:px-8 min-[1100px]:px-12 py-6">
        {invalid && (
          <div className="mb-6">
            <Banner kind="error" title="Policy signature is invalid" action={<Button variant="primary" onClick={() => nav("/policy")}>Review policy</Button>}>
              All payments are stopped until you sign a new policy.
            </Banner>
          </div>
        )}
        {policy === null && (
          <div className="mb-6">
            <Banner kind="warn" title="No active signed policy" action={<Button variant="primary" onClick={() => nav("/policy")}>Sign a policy</Button>}>
              Payments are refused until you sign one.
            </Banner>
          </div>
        )}
        <main className="page-in"><Outlet /></main>
      </div>
    </div>
  );
}
