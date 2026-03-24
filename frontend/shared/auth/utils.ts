// JWT decode utilities (client-side only — JWTs are not encrypted)

export interface JwtPayload {
  sub: string;
  roles: string[];
  permissions?: string[];
  tenant_id?: number;
  display_name?: string;
  exp?: number;
  iat?: number;
}

export function decodeJwt(token: string): JwtPayload | null {
  try {
    const [, payload] = token.split(".");
    const decoded = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decoded) as JwtPayload;
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string): boolean {
  const payload = decodeJwt(token);
  if (!payload?.exp) return false;
  return Date.now() / 1000 > payload.exp;
}

export function getTokenFromCookie(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|; )admin_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

export function setTokenCookie(token: string): void {
  if (typeof document === "undefined") return;
  document.cookie = `admin_token=${encodeURIComponent(token)}; path=/; SameSite=Strict; max-age=${60 * 60 * 8}`;
}

export function clearTokenCookie(): void {
  if (typeof document === "undefined") return;
  document.cookie = "admin_token=; path=/; max-age=0";
}
