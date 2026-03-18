"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { buildCsrfHeaders, clearCsrfToken, ensureCsrfToken } from "./csrf";

export type SessionUser = {
  user_id: string;
  display_name: string;
  roles: string[];
  language: string;
  access_token?: string;
};

type AuthContextValue = {
  user: SessionUser | null;
  loginDemo: (userId: string) => Promise<{ ok: boolean; error?: string }>;
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
    localStorage.setItem("app.session", JSON.stringify(session));
    localStorage.setItem("app.userId", session.user_id);
    localStorage.setItem("app.language", session.language);
    if (session.access_token) {
      localStorage.setItem("app.token", session.access_token);
    }
    emitAuthChanged();
  }, []);

  useEffect(() => {
    const raw = localStorage.getItem("app.session");
    if (!raw) return;

    try {
      const parsed = JSON.parse(raw) as SessionUser;
      setUser(parsed);
      localStorage.setItem("app.userId", parsed.user_id);
    } catch {
      localStorage.removeItem("app.session");
    }
  }, []);

  const loginDemo = useCallback(async (userId: string) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/auth/demo-login`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", ...csrfHeaders },
        body: JSON.stringify({ user_id: userId }),
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

  const loginWithCredentials = useCallback(async (login: string, password: string) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/auth/mock-login`, {
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
    localStorage.removeItem("app.session");
    localStorage.removeItem("app.userId");
    localStorage.removeItem("app.token");
    clearCsrfToken();
    emitAuthChanged();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, loginDemo, loginWithCredentials, loginWithLdap, logout }),
    [user, loginDemo, loginWithCredentials, loginWithLdap, logout],
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
