"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { buildCsrfHeaders, clearCsrfToken, ensureCsrfToken } from "./csrf";

export type SessionUser = {
  user_id: string;
  display_name: string;
  roles: string[];
  language?: string;
};

type AuthContextValue = {
  user: SessionUser | null;
  loginWithCredentials: (login: string, password: string) => Promise<{ ok: boolean; error?: string }>;
  loginWithLdap: (login: string, password: string) => Promise<{ ok: boolean; error?: string }>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function emitAuthChanged() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("app-auth-changed"));
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<SessionUser | null>(null);

  const persistSession = useCallback((session: SessionUser) => {
    setUser(session);
    emitAuthChanged();
  }, []);

  useEffect(() => {
    void (async () => {
      try {
        // Use the BFF route so the httpOnly admin_token cookie is read server-side.
        const res = await fetch(`/api/auth/me`, {
          credentials: "include",
          cache: "no-store",
        });
        if (!res.ok) {
          setUser(null);
          emitAuthChanged();
          return;
        }

        // BFF /api/auth/me returns SessionResponse: { authenticated, user: { sub, displayName, ... } }
        const json = await res.json() as {
          authenticated?: boolean;
          user?: { sub?: string; displayName?: string; roles?: string[]; language?: string };
        };
        if (json.authenticated && json.user?.sub) {
          setUser({
            user_id: json.user.sub,
            display_name: json.user.displayName ?? json.user.sub,
            roles: json.user.roles ?? [],
            language: json.user.language,
          });
        } else {
          setUser(null);
        }
        emitAuthChanged();
      } catch {
        setUser(null);
      }
    })();
  }, []);

  const loginWithCredentials = useCallback(async (login: string, password: string) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", ...csrfHeaders },
        body: JSON.stringify({ login, password }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        return { ok: false, error: String(err.detail || res.status) };
      }

      const json = (await res.json()) as SessionUser;
      persistSession(json);
      await ensureCsrfToken(baseUrl);
      return { ok: true };
    } catch (error) {
      return { ok: false, error: String(error) };
    }
  }, [persistSession]);

  const loginWithLdap = useCallback(async (login: string, password: string) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/auth/ldap-login`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", ...csrfHeaders },
        body: JSON.stringify({ login, password }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        return { ok: false, error: String(err.detail || res.status) };
      }

      const json = (await res.json()) as SessionUser;
      persistSession(json);
      await ensureCsrfToken(baseUrl);
      return { ok: true };
    } catch (error) {
      return { ok: false, error: String(error) };
    }
  }, [persistSession]);

  const logout = useCallback(() => {
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
    void (async () => {
      try {
        const csrfHeaders = await buildCsrfHeaders(baseUrl);
        await fetch(`${baseUrl}/auth/logout`, {
          method: "POST",
          credentials: "include",
          headers: csrfHeaders,
        });
      } catch {
        // Keep local logout behavior even if backend logout request fails.
      }
    })();

    setUser(null);
    clearCsrfToken();
    emitAuthChanged();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, loginWithCredentials, loginWithLdap, logout }),
    [user, loginWithCredentials, loginWithLdap, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return ctx;
}
