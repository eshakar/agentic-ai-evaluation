/**
 * First, quick check on every request: without a valid login cookie, pages redirect to /login
 * and the backend relay answers 401. (The relay route checks again itself, and the backend
 * checks the API key, so this is not the only guard.)
 */
import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE, isAuthorized } from "@/lib/auth";

export async function proxy(request: NextRequest) {
  if (await isAuthorized(request.cookies.get(SESSION_COOKIE)?.value)) {
    return NextResponse.next();
  }
  const { pathname, search } = request.nextUrl;
  if (pathname.startsWith("/api/")) {
    return NextResponse.json({ detail: "Not logged in." }, { status: 401 });
  }
  const login = new URL("/login", request.url);
  if (pathname !== "/") login.searchParams.set("next", pathname + search);
  return NextResponse.redirect(login);
}

export const config = {
  // Everything except the login page, the login API, Next.js assets and the tab icon.
  matcher: ["/((?!login|api/auth|_next/static|_next/image|icon.svg).*)"],
};
