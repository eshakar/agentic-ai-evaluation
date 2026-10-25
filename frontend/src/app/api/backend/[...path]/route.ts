/**
 * Relay from the browser to the FastAPI backend: /api/backend/<path> -> BACKEND_URL/<path>.
 *
 * The browser only ever talks to this website. This server checks the login cookie and adds
 * the secret X-API-Key header, so the key never reaches the browser (and no CORS is needed).
 */
import { cookies } from "next/headers";
import type { NextRequest } from "next/server";

import { SESSION_COOKIE, accessKey, backendUrl, isAuthorized } from "@/lib/auth";

// Whole-dataset evaluations can take minutes; let this function wait for them.
export const maxDuration = 300;

/** Only the backend paths the app uses: never an open relay to anything else. */
const ALLOWED = /^(health|api\/v1\/[A-Za-z0-9._~\-/]+)$/;

async function relay(request: NextRequest, ctx: RouteContext<"/api/backend/[...path]">) {
  const cookieStore = await cookies();
  if (!(await isAuthorized(cookieStore.get(SESSION_COOKIE)?.value))) {
    return Response.json({ detail: "Not logged in." }, { status: 401 });
  }

  const { path } = await ctx.params;
  const target = path.join("/");
  if (!ALLOWED.test(target) || target.includes("..")) {
    return Response.json({ detail: "Not found." }, { status: 404 });
  }

  const headers: Record<string, string> = { Accept: "application/json" };
  const contentType = request.headers.get("content-type");
  if (contentType) headers["Content-Type"] = contentType;
  const key = accessKey();
  if (key) headers["X-API-Key"] = key;

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  let upstream: Response;
  try {
    upstream = await fetch(`${backendUrl()}/${target}${request.nextUrl.search}`, {
      method: request.method,
      headers,
      body: hasBody ? await request.text() : undefined,
      cache: "no-store",
      signal: AbortSignal.timeout(maxDuration * 1000),
    });
  } catch {
    return Response.json(
      { detail: "The backend is unreachable. Is it running, and is BACKEND_URL correct?" },
      { status: 502 },
    );
  }

  if (upstream.status === 401) {
    // The backend refused our key: a server configuration problem, not the visitor's fault.
    return Response.json(
      { detail: "The backend rejected the access key. ACCESS_KEY here must equal API_ACCESS_KEY there." },
      { status: 502 },
    );
  }
  if (upstream.status === 204) return new Response(null, { status: 204 });
  return new Response(await upstream.text(), {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
  });
}

export { relay as GET, relay as POST, relay as DELETE };
