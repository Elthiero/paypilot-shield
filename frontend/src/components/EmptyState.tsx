import { Inbox } from "lucide-react";
import type { ReactNode } from "react";

interface Props { note: string; text: string; action?: ReactNode; }

export default function EmptyState({ note, text, action }: Props) {
  return (
    <div className="card text-center py-10">
      <div className="mx-auto w-10 h-10 rounded-full bg-yellow border border-ink flex items-center justify-center mb-3"><Inbox size={20} aria-hidden /></div>
      <p className="note">{note}</p>
      <p className="text-[13px] text-ink-mute mt-1">{text}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
