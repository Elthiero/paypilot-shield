// WebCrypto signing with a non-extractable ECDSA P-256 key stored in IndexedDB.
// See build guide section 8.4 for the full implementation.
import { get, set } from "idb-keyval";

export async function ensureKeypair(): Promise<CryptoKeyPair> {
  const existing = await get("paypilot-keypair");
  if (existing) return existing;
  const pair = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, false, ["sign", "verify"]);
  await set("paypilot-keypair", pair);
  return pair;
}
