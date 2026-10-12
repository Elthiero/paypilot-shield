import { FormEvent, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import Banner from "../components/Banner";
import Button from "../components/Button";
import Input from "../components/Input";
import { login } from "../hooks/useAuth";
import { ApiError } from "../lib/api";

export default function Login() {
  const nav = useNavigate();
  const [params] = useSearchParams();
  const [email, setEmail] = useState(import.meta.env.DEV ? "owner@paypilot.demo" : "");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(params.get("expired") ? "Your session expired. Sign in again to continue." : null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      nav("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not reach the server.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="flex gap-10 items-center flex-wrap justify-center max-w-4xl">
        <form onSubmit={submit} className="card w-[380px] max-w-full space-y-4">
          <p className="note -rotate-2 inline-block">welcome back!</p>
          <h1>Sign in</h1>
          {error && <Banner kind="error" title={error} />}
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="username" />
          <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
          <Button type="submit" loading={busy} className="w-full">Sign in</Button>
        </form>
        <div className="space-y-5">
          {[["AI proposes", "bg-sky", "-rotate-2"], ["Rules decide", "bg-yellow", "rotate-1.5"], ["You sign", "bg-pink", "-rotate-1"]].map(([t, c, r]) => (
            <div key={t} className={`relative ${c} ${r} border border-ink shadow-hard px-6 py-3 text-xl font-extrabold w-fit`}>
              <span className="tape -top-3 left-4 !w-12 !h-5 rotate-3" aria-hidden />{t}
            </div>
          ))}
          <p className="note">Sandbox demo. No real money moves.</p>
          <Link to="/privacy" className="label underline">Privacy and terms</Link>
        </div>
      </div>
    </div>
  );
}
