import { useState } from "react";
import type { FormEvent } from "react";
import { ApiError, api } from "../lib/api";
import type { Supplier } from "../lib/types";
import Banner from "./Banner";
import Button from "./Button";
import Drawer from "./Drawer";

export default function AddSupplierDrawer({ onClose, onCreated }: { onClose: () => void; onCreated: (s: Supplier) => void }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [country, setCountry] = useState("US");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      onCreated(await api<Supplier>("/suppliers", { body: { name: name.trim(), paypal_email: email.trim(), country: country.toUpperCase() } }));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not reach the server.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Drawer title="Add supplier" onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        <label className="block"><span className="label block mb-1">Name</span>
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} required maxLength={255} /></label>
        <label className="block"><span className="label block mb-1">PayPal email</span>
          <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required maxLength={255} /></label>
        <label className="block"><span className="label block mb-1">Country (2 letters)</span>
          <input className="input" value={country} onChange={(e) => setCountry(e.target.value)} required pattern="[A-Za-z]{2}" maxLength={2} /></label>
        <p className="text-[14px] text-ink-mute">New suppliers start unverified. Open one to verify it.</p>
        {error && <Banner kind="error" title={error} />}
        <Button type="submit" loading={busy}>Add supplier</Button>
      </form>
    </Drawer>
  );
}
