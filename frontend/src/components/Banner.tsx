import { CircleAlert, CircleCheck, Info, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";

const KIND = {
  error: { fill: "bg-pink", icon: CircleAlert },
  warn: { fill: "bg-yellow", icon: TriangleAlert },
  success: { fill: "bg-mint", icon: CircleCheck },
  info: { fill: "bg-sky", icon: Info },
} as const;

interface Props { kind: keyof typeof KIND; title: string; children?: ReactNode; action?: ReactNode; }

export default function Banner({ kind, title, children, action }: Props) {
  const { fill, icon: Icon } = KIND[kind];
  return (
    <div role={kind === "error" ? "alert" : "status"} className={`${fill} text-ink border border-ink rounded shadow-hard-sm px-4 py-3 flex flex-wrap items-start gap-3`}>
      <Icon size={20} className="mt-0.5 shrink-0" aria-hidden />
      <div className="flex-1 min-w-[180px]">
        <p className="font-bold">{title}</p>
        {children && <p className="text-[13px] leading-5">{children}</p>}
      </div>
      {action}
    </div>
  );
}
