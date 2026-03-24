import { ROLE_PERMISSIONS, type Permission } from "@/shared/config/permissions";

export interface SafeAdminUser {
  sub: string;
  displayName: string;
  roles: string[];
  permissions: string[];
  tenantId?: number;
}

export interface SessionResponse {
  authenticated: boolean;
  user: SafeAdminUser | null;
}

interface BackendProfilePayload {
  user_id?: string;
  display_name?: string;
  roles?: string[];
  permissions?: string[];
  tenant_id?: number;
}

interface JwtPayload {
  sub?: string;
  display_name?: string;
  roles?: string[];
  permissions?: string[];
  tenant_id?: number;
  exp?: number;
}

export function decodeJwtPayload(token: string): JwtPayload | null {
  try {
    const [, payloadPart] = token.split(".");
    const payload = JSON.parse(Buffer.from(payloadPart, "base64url").toString("utf-8")) as JwtPayload;
    return payload;
  } catch {
    return null;
  }
}

export function isJwtExpired(token: string): boolean {
  const payload = decodeJwtPayload(token);
  if (!payload?.exp) return false;
  return Date.now() / 1000 > payload.exp;
}

export function toSafeSession(token: string): SessionResponse | null {
  const payload = decodeJwtPayload(token);
  if (!payload?.sub) return null;

  return {
    authenticated: true,
    user: {
      sub: payload.sub,
      displayName: payload.display_name ?? payload.sub,
      roles: payload.roles ?? [],
      permissions: payload.permissions ?? [],
      tenantId: payload.tenant_id,
    },
  };
}

function normalizeRoles(input: unknown): string[] {
  if (!Array.isArray(input)) {
    return [];
  }
  return input
    .map((value) => String(value).trim())
    .filter((value) => value.length > 0);
}

function normalizePermissions(input: unknown, roles: string[]): string[] {
  const rolePermissions = roles.flatMap((role) => ROLE_PERMISSIONS[role] ?? []);
  const explicitPermissions = Array.isArray(input)
    ? input.map((value) => String(value).trim()).filter((value) => value.length > 0)
    : [];
  return Array.from(new Set<Permission | string>([...rolePermissions, ...explicitPermissions]));
}

export function toSafeSessionFromProfile(profile: unknown): SessionResponse | null {
  if (!profile || typeof profile !== "object") {
    return null;
  }

  const payload = profile as BackendProfilePayload;
  const userId = String(payload.user_id ?? "").trim();
  if (!userId) {
    return null;
  }

  const roles = normalizeRoles(payload.roles);
  const permissions = normalizePermissions(payload.permissions, roles);

  return {
    authenticated: true,
    user: {
      sub: userId,
      displayName: String(payload.display_name ?? userId),
      roles,
      permissions,
      tenantId: typeof payload.tenant_id === "number" ? payload.tenant_id : undefined,
    },
  };
}
