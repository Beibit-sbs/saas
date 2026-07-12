"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useAdminAuth } from "@/shared/auth/hooks";
import { useLanguage } from "@/app/components/LanguageProvider";
import { findTenantById, loadLoginTenantDirectory } from "@/app/login/tenant-directory";
import LanguageSwitcher from "@/app/components/LanguageSwitcher";
import { Button } from "./button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./dropdown-menu";
import { ChevronDown, LogOut, User } from "lucide-react";

function normalizeTenantId(value: unknown): string | null {
  if (typeof value === "number" && Number.isInteger(value) && value > 0) {
    return String(value);
  }
  if (typeof value === "string" && /^\d+$/.test(value.trim())) {
    const normalized = String(Number(value.trim()));
    return normalized === "0" ? null : normalized;
  }
  return null;
}

export function AppTopbar() {
  const { user, logout } = useAdminAuth();
  const { t } = useLanguage();
  const [universityName, setUniversityName] = useState<string | null>(null);
  const userName = user?.displayName ?? user?.sub ?? "";
  const normalizedTenantId = normalizeTenantId(user?.tenantId);
  const isPlatformContext = Boolean(user?.roles?.includes("superadmin") && !normalizedTenantId);

  useEffect(() => {
    let cancelled = false;

    if (!normalizedTenantId || isPlatformContext) {
      setUniversityName(null);
      return;
    }

    loadLoginTenantDirectory()
      .then((result) => {
        if (cancelled || result.state !== "ready") {
          return;
        }
        const match = findTenantById(result.tenants, normalizedTenantId);
        setUniversityName(match?.name ?? null);
      })
      .catch(() => {
        if (!cancelled) {
          setUniversityName(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [isPlatformContext, normalizedTenantId]);

  const contextLabel = useMemo(() => {
    if (!user) {
      return null;
    }
    if (isPlatformContext) {
      return t("ui.platformContext");
    }
    if (universityName) {
      return universityName;
    }
    if (normalizedTenantId) {
      return t("ui.universityIdFallback").replace("{id}", normalizedTenantId);
    }
    return null;
  }, [isPlatformContext, normalizedTenantId, t, universityName, user]);

  const initials = userName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((item) => item[0]?.toUpperCase() ?? "")
    .join("") || "U";

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-end gap-3 border-b border-border/70 bg-background/88 px-4 backdrop-blur-xl">
      <LanguageSwitcher variant="inline" />
      {user && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-11 rounded-full border border-border/70 bg-card/75 px-2 shadow-sm transition hover:bg-accent/80">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/12 text-xs font-semibold text-primary">
                {initials}
              </span>
              <span className="max-w-[13rem] truncate text-sm font-medium text-foreground">{userName}</span>
              {contextLabel && (
                <span className="max-w-[12rem] truncate rounded-full bg-secondary px-2 py-0.5 text-xs font-medium text-secondary-foreground" title={contextLabel}>
                  {contextLabel}
                </span>
              )}
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem asChild>
              <Link href="/console/profile">{t("ui.profile")}</Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/console/preferences">{t("ui.preferences")}</Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/console/security">{t("ui.security")}</Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={logout} className="text-destructive focus:text-destructive">
              <LogOut className="mr-2 h-4 w-4" />
              {t("ui.signOut")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
      {!user && (
        <Button variant="ghost" size="sm" onClick={logout} className="gap-1.5 rounded-full border border-border/70 bg-card/75 text-foreground shadow-sm">
          <User className="h-4 w-4" />
          {t("ui.signOut")}
        </Button>
      )}
    </header>
  );
}
