import { cookies } from "next/headers";

import { SESSION_COOKIE, SESSION_MAX_AGE, accessKey, safeEqual, sessionToken } from "@/lib/auth";

export async function POST(request: Request) {
  const key = accessKey();
  if (!key) return Response.json({ ok: true, enabled: false });

  const body = (await request.json().catch(() => null)) as { key?: unknown } | null;
  const typed = typeof body?.key === "string" ? body.key.trim() : "";

  // Compare session tokens (fixed length) rather than raw keys, in constant time.
  if (!typed || !safeEqual(await sessionToken(typed), await sessionToken(key))) {
    await new Promise((r) => setTimeout(r, 800)); // slow down guessing
    return Response.json({ detail: "That access key is not correct." }, { status: 401 });
  }

  const cookieStore = await cookies();
  cookieStore.set(SESSION_COOKIE, await sessionToken(key), {
    httpOnly: true, // page scripts can't read it
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE,
  });
  return Response.json({ ok: true, enabled: true });
}
