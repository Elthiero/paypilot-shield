// WebCrypto signing with a non-extractable ECDSA P-256 key kept in IndexedDB.
// The server builds the exact string to sign. The browser signs it unchanged.
import { del, get, set } from "idb-keyval";
import { api } from "./api";

const KEY = "paypilot-keypair";
const b64 = (buf: ArrayBuffer) => btoa(String.fromCharCode(...new Uint8Array(buf)));

export function secureCryptoAvailable(): boolean {
  return typeof crypto !== "undefined" && !!crypto.subtle;
}

function requireCrypto() {
  if (!secureCryptoAvailable()) {
    throw new Error("Signing needs a secure connection (HTTPS). Open the app over HTTPS.");
  }
}

export async function hasKeypair(): Promise<boolean> {
  return !!(await get<CryptoKeyPair>(KEY));
}

export async function ensureKeypair(): Promise<CryptoKeyPair> {
  requireCrypto();
  const existing = await get<CryptoKeyPair>(KEY);
  if (existing) return existing;
  const pair = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, false, ["sign", "verify"]);
  await set(KEY, pair);
  return pair;
}

/** Public key as base64 SPKI DER, the format the server loads. */
export async function exportPublicKey(pair: CryptoKeyPair): Promise<string> {
  return b64(await crypto.subtle.exportKey("spki", pair.publicKey));
}

export async function registerKey(): Promise<void> {
  const pair = await ensureKeypair();
  await api("/auth/register-key", { body: { public_key: await exportPublicKey(pair) } });
}

/** Makes a fresh key. The server then deactivates the active policy, so the owner must sign a new one. */
export async function resetKey(): Promise<void> {
  requireCrypto();
  await del(KEY);
  await registerKey();
}

/** Returns base64 of the raw 64 byte r||s signature. */
export async function signPayload(payload: string): Promise<string> {
  const pair = await ensureKeypair();
  const sig = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, pair.privateKey, new TextEncoder().encode(payload));
  return b64(sig);
}
