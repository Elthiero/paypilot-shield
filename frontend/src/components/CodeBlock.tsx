import { Check, Copy } from "lucide-react";
import { useState } from "react";
import Button from "./Button";

export default function CodeBlock({ text, label = "Copy" }: { text: string; label?: string }) {
  const [done, setDone] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setDone(true);
      setTimeout(() => setDone(false), 1500);
    } catch { /* clipboard blocked */ }
  };
  return (
    <div className="relative bg-card border border-ink rounded p-3 pr-24">
      <Button variant="secondary" className="absolute top-2 right-2 !h-8" onClick={copy} aria-label={label}>
        {done ? <Check size={12} /> : <Copy size={12} />}{done ? "Copied" : label}
      </Button>
      <pre className="font-mono text-[13px] leading-5 overflow-x-auto whitespace-pre-wrap break-all">{text}</pre>
    </div>
  );
}
