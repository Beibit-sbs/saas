import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/login", "/api/auth/login"];

function isTokenExpired(token: string): boolean {
  try {
    const [, payload] = token.split(".");
    const decoded = JSON.parse(Buffer.from(payload, "base64url").toString());
    if (!decoded.exp) return false;
    return Date.now() / 1000 > decoded.exp;
  } catch {
    return true;
  }
}

function readAuthToken(request: NextRequest): string | undefined {
  return request.cookies.get("app_access_token")?.value ?? request.cookies.get("admin_token")?.value;
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname === "/admin" || pathname.startsWith("/admin/")) {
    return NextResponse.redirect(new URL("/console/platform", request.url));
  }

  if (pathname.startsWith("/login")) {
    const token = readAuthToken(request);
    if (token && !isTokenExpired(token)) {
      const next = request.nextUrl.searchParams.get("next") ?? "/console";
      const target = next.startsWith("/login") ? "/console" : next;
      return NextResponse.redirect(new URL(target, request.url));
    }
    return NextResponse.next();
  }

  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  if (!pathname.startsWith("/console") && !pathname.startsWith("/student") && !pathname.startsWith("/faculty") && !pathname.startsWith("/registrar") && !pathname.startsWith("/profile")) {
    return NextResponse.next();
  }

  const token = readAuthToken(request);

  if (!token || isTokenExpired(token)) {
    const loginUrl = new URL("/login", request.url);
    const search = request.nextUrl.search;
    loginUrl.searchParams.set("next", search ? `${pathname}${search}` : pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/login",
    "/console/:path*",
    "/admin",
    "/admin/:path*",
    "/student",
    "/student/:path*",
    "/faculty",
    "/faculty/:path*",
    "/registrar",
    "/registrar/:path*",
    "/profile",
    "/profile/:path*",
  ],
};
