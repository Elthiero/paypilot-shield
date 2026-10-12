import { money, when } from "../lib/format";
import type { Transaction } from "../lib/types";

const ts = (iso: string) => new Date(iso.endsWith("Z") ? iso : iso + "Z").getTime();  // the backend sends UTC without a Z

/** Running total of successful payouts over time, all suppliers. Inline SVG, no chart library. */
export default function TotalPaidChart({ txns }: { txns: Transaction[] }) {
  const pts = txns.filter((t) => t.status === "SUCCESS").sort((a, b) => ts(a.created_at) - ts(b.created_at))
    .reduce<{ t: number; total: number; label: string }[]>((acc, t) => {
      acc.push({ t: ts(t.created_at), total: (acc[acc.length - 1]?.total ?? 0) + t.amount, label: `${t.invoice ?? "Payout"} · ${when(t.created_at)}` });
      return acc;
    }, []);
  if (pts.length === 0) return null;

  const W = 640, H = 180, pl = 56, pr = 16, pt = 16, pb = 28;
  const t0 = pts[0].t, span = pts[pts.length - 1].t - t0 || 1;  // one point or identical times: avoid dividing by zero
  const max = pts[pts.length - 1].total * 1.1;
  const x = (t: number) => (pts.length === 1 ? (pl + W - pr) / 2 : pl + ((t - t0) / span) * (W - pl - pr));
  const y = (v: number) => H - pb - (v / max) * (H - pt - pb);
  const line = pts.map((p) => `${x(p.t)},${y(p.total)}`).join(" ");

  return (
    <div className="card mb-6">
      <p className="label text-ink-mute mb-2">Total paid over time</p>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img"
        aria-label={`Running total paid: ${pts.map((p) => `${money(p.total)} after ${p.label}`).join("; ")}`}>
        <line x1={pl} x2={W - pr} y1={H - pb} y2={H - pb} className="stroke-ink" />
        <line x1={pl} x2={pl} y1={pt} y2={H - pb} className="stroke-ink" />
        <text x={pl - 6} y={y(0) + 4} textAnchor="end" fontSize="11" className="fill-ink">{money(0)}</text>
        <text x={pl - 6} y={y(max / 1.1) + 4} textAnchor="end" fontSize="11" className="fill-ink">{money(max / 1.1)}</text>
        <text x={pl} y={H - 8} fontSize="11" className="fill-ink">{when(new Date(t0).toISOString())}</text>
        {pts.length > 1 && <text x={W - pr} y={H - 8} textAnchor="end" fontSize="11" className="fill-ink">{when(new Date(t0 + span).toISOString())}</text>}
        <polyline points={line} fill="none" strokeWidth="2" className="stroke-ink" />
        {pts.map((p, i) => (
          <circle key={i} cx={x(p.t)} cy={y(p.total)} r="5" className="fill-yellow stroke-ink"><title>{`${money(p.total)} after ${p.label}`}</title></circle>
        ))}
      </svg>
    </div>
  );
}
