"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { useToast } from "@/shared/ui/use-toast";
import { GraduationCap, Loader2 } from "lucide-react";
import { useLanguage } from "@/app/components/LanguageProvider";
import LanguageSwitcher from "@/app/components/LanguageSwitcher";
import {
  findTenantByDomain,
  findTenantById,
  getDefaultTenantId,
  LOGIN_LAST_TENANT_STORAGE_KEY,
  loadLoginTenantDirectory,
  type LoginTenantOption,
} from "./tenant-directory";

type FormData = {
  username: string;
  password: string;
  tenantId: string;
};

function isPlatformAdminUsername(value: string): boolean {
  const normalized = value.trim().toLowerCase();
  return normalized.startsWith("local/") || normalized === "platform_admin";
}

function extractLoginDomain(value: string): string | null {
  const normalized = value.trim().toLowerCase();
  if (!normalized || isPlatformAdminUsername(normalized)) {
    return null;
  }

  const atIndex = normalized.lastIndexOf("@");
  if (atIndex <= 0 || atIndex === normalized.length - 1) {
    return null;
  }

  const domain = normalized.slice(atIndex + 1).trim();
  return domain || null;
}

function orderTenantOptions(options: LoginTenantOption[], selectedTenantId: string): LoginTenantOption[] {
  const sorted = [...options].sort((left, right) => left.name.localeCompare(right.name));
  if (!selectedTenantId) {
    return sorted;
  }

  const selected = sorted.find((item) => item.tenantId === selectedTenantId);
  if (!selected) {
    return sorted;
  }

  return [selected, ...sorted.filter((item) => item.tenantId !== selectedTenantId)];
}

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const { t } = useLanguage();
  const [loading, setLoading] = useState(false);
  const [checkingSession, setCheckingSession] = useState(false);
  const [tenantDirectoryState, setTenantDirectoryState] = useState<"loading" | "ready" | "unavailable">("loading");
  const [tenantOptions, setTenantOptions] = useState<LoginTenantOption[]>([]);
  const [domainAutoDetectEnabled, setDomainAutoDetectEnabled] = useState(false);
  const [defaultTenantId] = useState(() => getDefaultTenantId());
  const [technicalTenantId, setTechnicalTenantId] = useState("");
  const [tenantError, setTenantError] = useState<string | null>(null);
  const [tenantSelectionState, setTenantSelectionState] = useState<"default" | "restored" | "manual">("default");
  const manualDomainLockRef = useRef<string | null>(null);
  const lastAutoAppliedDomainRef = useRef<string | null>(null);

  const schema = useMemo(() => z.object({
    username: z.string().min(1, t("auth.required")),
    password: z.string().min(1, t("auth.required")),
  }), [t]);

  const {
    control,
    getValues,
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      tenantId: defaultTenantId,
    },
  });

  const usernameValue = watch("username") || "";
  const selectedTenantId = watch("tenantId") || "";
  const isPlatformAdminLogin = isPlatformAdminUsername(usernameValue);
  const loginDomain = useMemo(() => (domainAutoDetectEnabled ? extractLoginDomain(usernameValue) : null), [domainAutoDetectEnabled, usernameValue]);
  const domainMatchedTenant = useMemo(
    () => (domainAutoDetectEnabled && loginDomain ? findTenantByDomain(tenantOptions, loginDomain) : null),
    [domainAutoDetectEnabled, loginDomain, tenantOptions],
  );
  const selectedTenant = useMemo(() => findTenantById(tenantOptions, selectedTenantId), [selectedTenantId, tenantOptions]);
  const orderedTenantOptions = useMemo(
    () => orderTenantOptions(tenantOptions, selectedTenantId),
    [selectedTenantId, tenantOptions],
  );

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      setTenantDirectoryState("loading");
      const result = await loadLoginTenantDirectory();
      if (cancelled) {
        return;
      }

      setDomainAutoDetectEnabled(false);
      setTenantOptions(result.tenants);

      if (result.state === "unavailable") {
        setTenantDirectoryState("unavailable");
        setValue("tenantId", "", { shouldDirty: false, shouldValidate: false });
        return;
      }

      setTenantDirectoryState("ready");

      const firstTenantId = result.tenants[0]?.tenantId ?? "";
      const currentTenant = findTenantById(result.tenants, getValues("tenantId") || "");
      if (!currentTenant && firstTenantId) {
        setValue("tenantId", firstTenantId, { shouldDirty: false, shouldValidate: false });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [getValues, setValue]);

  useEffect(() => {
    if (typeof window === "undefined" || tenantDirectoryState !== "ready") {
      return;
    }

    const rememberedTenantId = window.localStorage.getItem(LOGIN_LAST_TENANT_STORAGE_KEY);
    if (!rememberedTenantId) {
      return;
    }

    const rememberedTenant = findTenantById(tenantOptions, rememberedTenantId);
    if (!rememberedTenant) {
      return;
    }

    setValue("tenantId", rememberedTenant.tenantId, { shouldDirty: false, shouldValidate: false });
    setTenantSelectionState("restored");
  }, [setValue, tenantDirectoryState, tenantOptions]);

  useEffect(() => {
    if (!domainAutoDetectEnabled || isPlatformAdminLogin) {
      setTenantError(null);
      return;
    }

    if (!loginDomain || !domainMatchedTenant) {
      if (loginDomain !== manualDomainLockRef.current) {
        lastAutoAppliedDomainRef.current = null;
      }
      return;
    }

    if (manualDomainLockRef.current === loginDomain) {
      return;
    }

    if (lastAutoAppliedDomainRef.current === loginDomain && selectedTenantId === domainMatchedTenant.tenantId) {
      return;
    }

    setValue("tenantId", domainMatchedTenant.tenantId, { shouldDirty: true, shouldValidate: false });
    setTenantError(null);
    lastAutoAppliedDomainRef.current = loginDomain;
  }, [domainAutoDetectEnabled, domainMatchedTenant, isPlatformAdminLogin, loginDomain, selectedTenantId, setValue]);

  useEffect(() => {
    if (typeof window === "undefined" || isPlatformAdminLogin || tenantDirectoryState !== "ready") {
      return;
    }

    const tenant = findTenantById(tenantOptions, selectedTenantId);
    if (!tenant) {
      return;
    }

    window.localStorage.setItem(LOGIN_LAST_TENANT_STORAGE_KEY, tenant.tenantId);
  }, [isPlatformAdminLogin, selectedTenantId, tenantDirectoryState, tenantOptions]);

  const tenantHelperText = useMemo(() => {
    if (isPlatformAdminLogin) {
      return t("auth.platformAdminDetected");
    }
    if (tenantDirectoryState === "loading") {
      return t("auth.universityLoading");
    }
    if (tenantDirectoryState === "unavailable") {
      return t("auth.universityUnavailable");
    }
    if (orderedTenantOptions.length === 0) {
      return t("auth.universityUnavailable");
    }
    if (loginDomain && domainMatchedTenant && selectedTenantId === domainMatchedTenant.tenantId) {
      return t("auth.universityAutoDetected")
        .replace("{name}", domainMatchedTenant.name)
        .replace("{domain}", loginDomain);
    }
    if (loginDomain && !domainMatchedTenant) {
      return t("auth.universityManualRequired").replace("{domain}", loginDomain);
    }
    if (tenantSelectionState === "restored" && selectedTenant) {
      return t("auth.universityRemembered").replace("{name}", selectedTenant.name);
    }
    return t("auth.universityHelp");
  }, [domainMatchedTenant, isPlatformAdminLogin, loginDomain, orderedTenantOptions.length, selectedTenant, selectedTenantId, t, tenantDirectoryState, tenantSelectionState]);

  function handleTenantSelectionChange(nextTenantId: string) {
    setTenantError(null);
    setTenantSelectionState("manual");

    if (domainAutoDetectEnabled && loginDomain && domainMatchedTenant?.tenantId !== nextTenantId) {
      manualDomainLockRef.current = loginDomain;
    } else {
      manualDomainLockRef.current = null;
    }
  }

  useEffect(() => {
    const controller = new AbortController();

    void (async () => {
      try {
        const res = await fetch("/api/auth/me", {
          cache: "no-store",
          credentials: "include",
          signal: controller.signal,
        });
        if (!res.ok) {
          setCheckingSession(false);
          return;
        }

        const payload = (await res.json()) as { authenticated?: boolean };
        if (payload.authenticated) {
          const next = searchParams.get("next") ?? "/console";
          router.replace(next);
          router.refresh();
          return;
        }
      } catch {
        // If session probe fails, keep login form available.
      }

      setCheckingSession(false);
    })();

    return () => {
      controller.abort();
    };
  }, [router, searchParams]);

  async function fetchCsrfToken(): Promise<string> {
    const csrfRes = await fetch("/api/auth/csrf", {
      method: "GET",
      cache: "no-store",
      credentials: "include",
    });

    if (!csrfRes.ok) {
      throw new Error(t("auth.loginFailed"));
    }

    const csrfPayload = (await csrfRes.json().catch(() => ({}))) as { csrf_token?: unknown };
    const csrfToken = String(csrfPayload.csrf_token ?? "").trim();
    if (!csrfToken) {
      throw new Error(t("auth.loginFailed"));
    }
    return csrfToken;
  }

  async function onSubmit(data: FormData) {
    const platformAdminLogin = isPlatformAdminUsername(data.username);
    const selectedFormTenantId = String(data.tenantId ?? "").trim();
    const effectiveTenantId = platformAdminLogin
      ? null
      : (technicalTenantId.trim() || selectedFormTenantId || String(selectedTenantId).trim());

    if (!platformAdminLogin) {
      if (!effectiveTenantId) {
        setTenantError(t("auth.universityRequired"));
        return;
      }

      if (!/^\d+$/.test(effectiveTenantId)) {
        setTenantError(t("auth.technicalTenantInvalid"));
        return;
      }
    }

    setTenantError(null);
    setLoading(true);
    try {
      const csrfToken = await fetchCsrfToken();

      const payload: Record<string, unknown> = {
        username: data.username,
        password: data.password,
      };

      if (!platformAdminLogin && effectiveTenantId) {
        payload.tenant_id = Number.parseInt(effectiveTenantId, 10);
      }

      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken,
        },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? t("auth.loginFailed"));
      }

      const next = searchParams.get("next") ?? "/console";
      // Hard navigation avoids client-router race conditions while auth cookie is being persisted.
      if (typeof window !== "undefined") {
        window.location.assign(next);
        return;
      }
      router.replace(next);
      router.refresh();
    } catch (err: unknown) {
      toast({
        variant: "destructive",
        title: t("auth.loginFailed"),
        description: err instanceof Error ? err.message : t("auth.tryAgain"),
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-muted/30 px-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-2">
            <GraduationCap className="h-8 w-8 text-primary" />
          </div>
          <CardTitle>{t("auth.loginTitle")}</CardTitle>
          <CardDescription>{t("auth.loginSubtitle")}</CardDescription>
          <div className="pt-2 flex justify-center">
            <LanguageSwitcher variant="inline" />
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="username">{t("auth.username")}</Label>
              <Input id="username" autoComplete="username" {...register("username")} />
              {errors.username && <p className="text-xs text-destructive">{errors.username.message}</p>}
            </div>
            {!isPlatformAdminLogin ? (
              <div className="space-y-1.5">
                <Label htmlFor="tenantId">{t("auth.universityLabel")}</Label>
                <Controller
                  control={control}
                  name="tenantId"
                  render={({ field }) => (
                    <select
                      id="tenantId"
                      value={field.value ?? ""}
                      disabled={tenantDirectoryState !== "ready" || orderedTenantOptions.length === 0}
                      onChange={(event) => {
                        field.onChange(event.target.value);
                        handleTenantSelectionChange(event.target.value);
                      }}
                      className="flex h-10 w-full items-center rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                    >
                      {tenantDirectoryState === "loading" ? (
                        <option value="">{t("auth.universityLoading")}</option>
                      ) : null}
                      {tenantDirectoryState === "unavailable" ? (
                        <option value="">{t("auth.universityUnavailable")}</option>
                      ) : null}
                      {tenantDirectoryState === "ready" && orderedTenantOptions.length === 0 ? (
                        <option value="">{t("auth.universityUnavailable")}</option>
                      ) : null}
                      {tenantDirectoryState === "ready" && orderedTenantOptions.length > 0
                        ? orderedTenantOptions.map((option) => (
                          <option key={option.tenantId} value={option.tenantId}>
                            {option.name}
                          </option>
                        ))
                        : null}
                    </select>
                  )}
                />
                <p className="text-xs text-muted-foreground">{tenantHelperText}</p>
                {tenantError ? <p className="text-xs text-destructive">{tenantError}</p> : null}
                <details className="mt-1 text-xs text-muted-foreground">
                  <summary className="cursor-pointer select-none text-[11px] text-muted-foreground/80 hover:text-muted-foreground">
                    {t("auth.technicalTenantToggle")}
                  </summary>
                  <div className="mt-2 space-y-1.5 rounded-md border border-dashed border-muted-foreground/30 bg-muted/20 px-3 py-2">
                    <Label htmlFor="technical-tenant-id" className="text-xs text-muted-foreground">
                      {t("auth.technicalTenantLabel")}
                    </Label>
                    <Input
                      id="technical-tenant-id"
                      inputMode="numeric"
                      autoComplete="off"
                      value={technicalTenantId}
                      onChange={(event) => {
                        setTechnicalTenantId(event.target.value);
                        setTenantError(null);
                      }}
                    />
                    <p className="text-xs text-muted-foreground">{t("auth.technicalTenantHelp")}</p>
                  </div>
                </details>
              </div>
            ) : (
              <p className="rounded-md border border-dashed bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
                {t("auth.platformAdminDetected")}
              </p>
            )}
            <div className="space-y-1.5">
              <Label htmlFor="password">{t("auth.password")}</Label>
              <Input id="password" type="password" autoComplete="current-password" {...register("password")} />
              {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {t("auth.signIn")}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
