import { useEffect, useState } from "react";
import { api } from "../lib/api";

export interface Health { ok: boolean; paypal_mode: string; dev_tools: boolean; }

let cached: Promise<Health> | null = null;
/** One /health call per page load, shared by everything that needs it. */
export const getHealth = (): Promise<Health> => (cached ??= api<Health>("/health").catch((e) => { cached = null; throw e; }));

export function useHealth(): Health | null {
  const [h, setH] = useState<Health | null>(null);
  useEffect(() => { getHealth().then(setH).catch(() => undefined); }, []);
  return h;
}
