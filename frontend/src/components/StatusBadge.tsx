import { Ban, BadgeCheck, CircleCheck, CircleHelp, CircleX, Clock, Gauge, Hourglass, PenLine, Send, ShieldAlert, ShieldCheck, ShieldX } from "lucide-react";
import type { LucideIcon } from "lucide-react";

// Exact mapping from DESIGN.md 2.4. Color is never the only signal: icon plus text.
const MAP: Record<string, { label: string; icon: LucideIcon; fill: string; text?: string }> = {
  AUTO_PAY: { label: "Auto pay", icon: CircleCheck, fill: "bg-green" },
  NEEDS_APPROVAL: { label: "Needs approval", icon: PenLine, fill: "bg-yellow" },
  BLOCKED: { label: "Blocked", icon: ShieldX, fill: "bg-pink" },
  PAID: { label: "Paid", icon: BadgeCheck, fill: "bg-green" },
  SUCCESS: { label: "Success", icon: BadgeCheck, fill: "bg-green" },
  SENT: { label: "Sent", icon: Send, fill: "bg-sky" },
  PENDING: { label: "Pending", icon: Clock, fill: "bg-sky" },
  AWAITING_APPROVAL: { label: "Awaiting approval", icon: Hourglass, fill: "bg-yellow" },
  ACTIVE: { label: "Active", icon: CircleCheck, fill: "bg-green" },
  REJECTED: { label: "Rejected", icon: Ban, fill: "bg-pink" },
  EXPIRED: { label: "Expired", icon: Clock, fill: "bg-butter" },
  FAILED: { label: "Failed", icon: CircleX, fill: "bg-pink" },
  LOW: { label: "Low risk", icon: Gauge, fill: "bg-mint" },
  MEDIUM: { label: "Medium risk", icon: Gauge, fill: "bg-butter" },
  HIGH: { label: "High risk", icon: Gauge, fill: "bg-ink", text: "text-white" },
  VERIFIED: { label: "Verified", icon: ShieldCheck, fill: "bg-green" },
  SIGNATURE_INVALID: { label: "Signature invalid", icon: ShieldAlert, fill: "bg-pink" },
};

const titleCase = (s: string) => s.toLowerCase().replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());

interface Props {
  value: string | null | undefined;
  /** degrees; only for hero and card headers. Table cells stay flat. */
  rotate?: number;
}

export default function StatusBadge({ value, rotate }: Props) {
  if (!value) return null;
  const m = MAP[value] ?? { label: titleCase(value), icon: CircleHelp, fill: "bg-card" };
  const Icon = m.icon;
  const sticker = rotate !== undefined;
  return (
    <span
      className={`label inline-flex items-center gap-1.5 border border-ink rounded px-2.5 py-1 whitespace-nowrap ${m.fill} ${m.text ?? "text-ink"} ${sticker ? "shadow-hard-sm" : ""}`}
      style={sticker ? { transform: `rotate(${rotate}deg)` } : undefined}
    >
      <Icon size={12} strokeWidth={3} aria-hidden />
      {m.label}
    </span>
  );
}
