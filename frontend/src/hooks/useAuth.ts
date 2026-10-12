import { api } from "../lib/api";
import { registerKey } from "../lib/crypto";

/** The real session is an httpOnly cookie. The email in sessionStorage is only a hint for what to render; a stale
 *  hint ends at the first 401, which sends the user to the login page. */
export function isLoggedIn(): boolean {
  return !!sessionStorage.getItem("email");
}

export function userEmail(): string {
  return sessionStorage.getItem("email") ?? "";
}

export async function login(email: string, password: string): Promise<void> {
  const r = await api<{ email: string }>("/auth/login", { body: { email, password } });
  sessionStorage.setItem("email", r.email);
  try {
    await registerKey(password);  // same key again is a no-op on the server
  } catch { /* plain HTTP or blocked storage: signing screens explain it */ }
}

export function logout(): void {
  sessionStorage.removeItem("email");
  api("/auth/logout", { method: "POST", body: {} }).catch(() => {});  // clears the cookie; best effort
}
