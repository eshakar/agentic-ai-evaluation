/**
 * Website login, server side only (never import this from a client component).
 *
 * ACCESS_KEY is the one secret: you type it on /login, and the website's server sends it to
 * the backend as X-API-Key. The browser never receives it. After login the browser holds a
 * cookie with an HMAC of the key (not the key itself), checked on every request.
 * With no ACCESS_KEY set (local development) the site is open and needs no login.
 */

export const SESSION_COOKIE = "agent_eval_session";
export const SESSION_MAX_AGE = 60 * 60 * 24 * 30; // 30 days

export const accessKey = (): string | null => process.env.ACCESS_KEY || null;

export const backendUrl = (): string =>
  (process.env.BACKEND_URL || "http://localhost:8000").replace(/\/+$/, "");

const encoder = new TextEncoder();

/** Session token = HMAC-SHA256(key, label), hex. Web Crypto, so it works in proxy.ts too. */
export async function sessionToken(key: string): Promise<string> {
  const cryptoKey = await crypto.subtle.importKey(
    "raw",
    encoder.encode(key),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", cryptoKey, encoder.encode("agent-eval-session:v1"));
  return Array.from(new Uint8Array(sig), (b) => b.toString(16).padStart(2, "0")).join("");
}

/** Constant-time string comparison (length is not secret here: tokens are fixed-length). */
export function safeEqual(a: string, b: string): boolean {
  const x = encoder.encode(a);
  const y = encoder.encode(b);
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) diff |= (x[i] ?? 0) ^ (y[i] ?? 0);
  return diff === 0;
}

/** True when login is disabled, or the cookie holds a valid session token. */
export async function isAuthorized(cookieValue: string | undefined): Promise<boolean> {
  const key = accessKey();
  if (!key) return true;
  if (!cookieValue) return false;
  return safeEqual(cookieValue, await sessionToken(key));
}
