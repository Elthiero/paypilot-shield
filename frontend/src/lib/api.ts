// BASE_URL is "/" or "/paypilot/", so the API follows the app to its base path
const BASE = import.meta.env.VITE_API_URL || `${import.meta.env.BASE_URL}api`;

export class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(detail);
  }
}

export function apiBase(): string {
  return BASE;
}

export async function api<T>(path: string, options: { method?: string; body?: unknown } = {}): Promise<T> {
  const token = sessionStorage.getItem("token");
  const hasBody = options.body !== undefined;
  const res = await fetch(BASE + path, {
    method: options.method ?? (hasBody ? "POST" : "GET"),
    headers: {
      ...(hasBody ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: hasBody ? JSON.stringify(options.body) : undefined,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch { /* keep statusText */ }
    if (res.status === 401 && path !== "/auth/login") {
      sessionStorage.removeItem("token");
      window.location.assign(import.meta.env.BASE_URL + "login?expired=1");
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}
