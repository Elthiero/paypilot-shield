import { api } from "../lib/api";
import { registerKey } from "../lib/crypto";

export function isLoggedIn(): boolean {
  return !!sessionStorage.getItem("token");
}

export function userEmail(): string {
  return sessionStorage.getItem("email") ?? "";
}

export async function login(email: string, password: string): Promise<void> {
  const r = await api<{ token: string; email: string }>("/auth/login", { body: { email, password } });
  sessionStorage.setItem("token", r.token);
  sessionStorage.setItem("email", r.email);
  try {
    await registerKey();  // same key again is a no-op on the server
  } catch { /* plain HTTP or blocked storage: signing screens explain it */ }
}

export function logout(): void {
  sessionStorage.removeItem("token");
  sessionStorage.removeItem("email");
}
