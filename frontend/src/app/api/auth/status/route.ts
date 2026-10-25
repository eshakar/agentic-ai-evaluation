import { cookies } from "next/headers";

import { SESSION_COOKIE, accessKey, isAuthorized } from "@/lib/auth";

/** Lets the UI know whether login is on and whether this browser is logged in. */
export async function GET() {
  const cookieStore = await cookies();
  return Response.json({
    enabled: Boolean(accessKey()),
    authenticated: await isAuthorized(cookieStore.get(SESSION_COOKIE)?.value),
  });
}
