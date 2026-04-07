"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { Permission } from "../config/permissions";
import type { SessionResponse } from "@/shared/server/auth-session";
import { onSessionInvalid } from "./session-events";

export interface AdminUser {
  sub: string;
  displayName: string;
  roles: string[];
  permissions: Permission[];
  tenantId?: number;
}

interface AuthContextValue {
  user: AdminUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  refreshSession: () => Promise<void>;
  logout: () => void;
  hasPermission: (permission: Permission) => boolean;
  hasAnyPermission: (permissions: Permission[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AdminAuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [user, setUser] = useState<AdminUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const redirectToLogin = useCallback(() => {
    const next = pathname === "/login" ? null : `${pathname}${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;
    const loginUrl = next ? `/login?next=${encodeURIComponent(next)}` : "/login";
    router.replace(loginUrl);
  }, [pathname, router, searchParams]);

  const refreshSession = useCallback(async () => {
    const res = await fetch("/api/auth/me", { cache: "no-store", credentials: "include" });
    if (!res.ok) {
      setUser(null);
      if (res.status === 401 && pathname.startsWith("/console")) {
        redirectToLogin();
      }
      return;
    }
    const data = (await res.json()) as SessionResponse;
    if (!data?.authenticated || !data.user) {
      setUser(null);
      return;
    }
    setUser({
      sub: data.user.sub,
      displayName: data.user.displayName,
      roles: data.user.roles,
      permissions: data.user.permissions as Permission[],
      tenantId: data.user.tenantId,
    });
  }, [pathname, redirectToLogin]);

  useEffect(() => {
    refreshSession()
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false));
  }, [refreshSession]);

  useEffect(() =>
    onSessionInvalid(() => {
      setUser(null);
      setIsLoading(false);
      if (pathname.startsWith("/console")) {
        redirectToLogin();
      }
    }),
  [pathname, redirectToLogin]);

  const logout = useCallback(() => {
    fetch("/api/auth/logout", { method: "POST" }).catch(() => {});
    setUser(null);
    router.replace("/login");
  }, [router]);

  const hasPermission = useCallback(
    (permission: Permission) => {
      if (!user) return false;
      if (user.roles.includes("superadmin")) return true;
      return user.permissions.includes(permission);
    },
    [user],
  );

  const hasAnyPermission = useCallback(
    (perms: Permission[]) => perms.some((p) => hasPermission(p)),
    [hasPermission],
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        refreshSession,
        logout,
        hasPermission,
        hasAnyPermission,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAdminAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAdminAuth must be used within AdminAuthProvider");
  return ctx;
}
