/** Text of a reason. Old rows may still hold a plain string. */
export const reasonText = (r: { message: string } | string): string => (typeof r === "string" ? r : r.message);

export function money(amount: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(amount);
}

const time = (iso: string) => new Date(iso.endsWith("Z") ? iso : iso + "Z").getTime();  // the backend sends UTC without a Z

export function when(iso: string | null): string {
  if (!iso) return "";
  return new Date(time(iso)).toLocaleString();
}

/** Elapsed time between two timestamps, e.g. "0.4 s" or "2 min 5 s". Empty when `to` is missing or before `from`. */
export function duration(from: string, to: string | null): string {
  if (!to) return "";
  const s = (time(to) - time(from)) / 1000;
  if (!(s >= 0)) return "";
  if (s < 60) return `${s.toFixed(1)} s`;
  return `${Math.floor(s / 60)} min ${Math.round(s % 60)} s`;
}

export function stepLabel(step: string): string {
  const s = step.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}
