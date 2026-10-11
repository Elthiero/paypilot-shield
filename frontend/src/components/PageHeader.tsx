import type { ReactNode } from "react";

interface Props { note: string; title: string; text: string; action?: ReactNode; }

export default function PageHeader({ note, title, text, action }: Props) {
  return (
    <div className="flex items-end justify-between gap-4 mb-6 flex-wrap">
      <div>
        <p className="note text-ink-soft -rotate-1 inline-block">{note}</p>
        <h1>{title}</h1>
        <p className="text-ink-mute text-[15px]">{text}</p>
      </div>
      {action}
    </div>
  );
}
