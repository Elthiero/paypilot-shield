/** Text of a reason. Old rows may still hold a plain string. */
export const reasonText = (r: { message: string } | string): string => (typeof r === "string" ? r : r.message);

export function money(amount: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(amount);
}

export function when(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso.endsWith("Z") ? iso : iso + "Z").toLocaleString();
}

export function stepLabel(step: string): string {
  const s = step.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}
