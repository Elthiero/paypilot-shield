export type Decision = "AUTO_PAY" | "NEEDS_APPROVAL" | "BLOCKED";
export type Risk = "LOW" | "MEDIUM" | "HIGH";

export interface Supplier { id: number; name: string; paypal_email: string; verified: boolean;
  last_payout_email: string | null; country: string; }

export interface Invoice { id: number; number: string; supplier: string | null;
  supplier_verified: boolean | null; description: string; amount: number; currency: string;
  payee_email: string; status: string; }

export interface PaymentRequest { id: number; invoice: string; amount: number;
  decision: Decision | null; risk: Risk | null; reasons: string[] | null; status: string; created_at: string; }

export interface Transaction { id: number; payment_request_id: number; invoice: string | null;
  payout_batch_id: string | null; paypal_txn_id: string | null; amount: number; currency: string;
  status: string; created_at: string; completed_at: string | null; }

export interface TraceEvent { id: number; step: string; detail: Record<string, unknown>; at: string; }

export interface AgentToolCall { tool: string; input?: Record<string, unknown>; output?: unknown; }
export interface AgentReply { reply: string; payment_request_id?: number | null;
  mode: "rules" | "llm" | "rules_fallback"; trace: AgentToolCall[]; }

export interface Rules { auto_limit: number | string; currency: string; monthly_budget: number | string;
  require_verified: boolean; valid_until: string; }
export interface Mandate { id: number; rules: Rules; policy_text: string; payload: string;
  signature: string | null; valid_until: string | null; active: boolean; verified: boolean; }
export interface ApprovalItem { id: number; invoice: string; supplier: string; amount: number;
  currency: string; reasons: string[]; risk: Risk; created_at: string; cart_payload: string; }
export interface PaymentSummary { ok: boolean; payment_request_id: number; invoice: string; amount: number;
  decision: Decision; risk: Risk; reasons: string[]; status: string; note?: string;
  transaction: { id: number; status: string; payout_batch_id: string | null; paypal_txn_id: string | null } | null; }
export interface PaymentDetail extends PaymentSummary { supplier: string; currency: string; created_at: string; }
