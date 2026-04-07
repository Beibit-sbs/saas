export interface SafeAdminUser {
  sub: string;
  displayName: string;
  roles: string[];
  permissions: string[];
  tenantId?: number;
  language?: string;
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
  language?: string;
}

interface JwtPayload {
  sub?: string;
  display_name?: string;
  roles?: string[];
  permissions?: string[];
  scp?: string[];
  tenant_id?: number;
  tid?: number;
  exp?: number;
  language?: string;
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

  const permissions = normalizePermissions(payload.permissions ?? payload.scp);

  return {
    authenticated: true,
    user: {
      sub: payload.sub,
      displayName: payload.display_name ?? payload.sub,
      roles: payload.roles ?? [],
      permissions,
      tenantId: payload.tenant_id ?? payload.tid,
      language: typeof payload.language === "string" ? payload.language : undefined,
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

function normalizePermissions(input: unknown): string[] {
  if (!Array.isArray(input)) {
    return [];
  }
  return Array.from(
    new Set(input.map((value) => String(value).trim()).filter((value) => value.length > 0)),
  );
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
  const permissions = normalizePermissions(payload.permissions);

  return {
    authenticated: true,
    user: {
      sub: userId,
      displayName: String(payload.display_name ?? userId),
      roles,
      permissions,
      tenantId: typeof payload.tenant_id === "number" ? payload.tenant_id : undefined,
      language: typeof payload.language === "string" ? payload.language : undefined,
    },
  };
}
