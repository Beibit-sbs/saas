"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  getRolePortalConfig,
  getRolePortalNavItems,
  getRolePortalSection,
  type RolePortalKey,
  type RolePortalResource,
} from "@/app/components/role-portal-registry";
import { findTenantById, loadLoginTenantDirectory } from "@/app/login/tenant-directory";

type SessionPayload = {
  authenticated?: boolean;
  user?: {
    sub?: string;
    displayName?: string;
    roles?: string[];
    permissions?: string[];
    tenantId?: number;
    language?: string;
  };
};

type DashboardSnapshot = {
  generated_at: string | null;
  kpis: Array<{
    key: string;
    value: number;
    source_status?: string | null;
  }>;
};

type ResourceState = {
  title: string;
  kind: "list" | "object";
  fields: Array<{ key: string; label: string }>;
  total?: number | null;
  items?: Record<string, unknown>[];
  object?: Record<string, unknown> | null;
  emptyMessage: string;
  error?: string | null;
};

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return "[object]";
    }
  }
  return String(value);
}

async function fetchResource(resource: RolePortalResource): Promise<ResourceState> {
  try {
    const res = await fetch(resource.endpoint, {
      method: "GET",
      cache: "no-store",
      credentials: "include",
    });
    if (!res.ok) {
      return {
        title: resource.title,
        kind: resource.kind,
        fields: resource.previewFields,
        emptyMessage: resource.emptyMessage,
        error: `Source unavailable (${res.status})`,
      };
    }

    const payload = (await res.json().catch(() => null)) as unknown;
    if (resource.kind === "list") {
      const raw = payload && typeof payload === "object"
        ? payload as { items?: unknown[]; events?: unknown[]; total?: number }
        : {};
      const items = Array.isArray(raw.items)
        ? raw.items
        : Array.isArray(raw.events)
          ? raw.events
          : Array.isArray(payload)
            ? payload
            : [];
      return {
        title: resource.title,
        kind: resource.kind,
        fields: resource.previewFields,
        total: typeof raw.total === "number" ? raw.total : items.length,
        items: items.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object").slice(0, 4),
        emptyMessage: resource.emptyMessage,
      };
    }

    return {
      title: resource.title,
      kind: resource.kind,
      fields: resource.previewFields,
      object: payload && typeof payload === "object" ? payload as Record<string, unknown> : null,
      emptyMessage: resource.emptyMessage,
    };
  } catch {
    return {
      title: resource.title,
      kind: resource.kind,
      fields: resource.previewFields,
      emptyMessage: resource.emptyMessage,
      error: "Source unavailable",
    };
  }
}

export function RolePortalSectionView({ roleKey, sectionKey }: { roleKey: RolePortalKey; sectionKey: string }) {
  const config = getRolePortalConfig(roleKey);
  const section = getRolePortalSection(roleKey, sectionKey);
  const navItems = getRolePortalNavItems(roleKey);

  const [session, setSession] = useState<SessionPayload | null>(null);
  const [tenantName, setTenantName] = useState<string | null>(null);
  const [resources, setResources] = useState<ResourceState[]>([]);
  const [analytics, setAnalytics] = useState<DashboardSnapshot | null>(null);

  useEffect(() => {
    let active = true;

    void (async () => {
      const sessionRes = await fetch("/api/auth/me", {
        method: "GET",
        cache: "no-store",
        credentials: "include",
      }).catch(() => null);

      const sessionPayload = sessionRes?.ok
        ? await sessionRes.json().catch(() => null) as SessionPayload | null
        : null;

      if (!active) {
        return;
      }

      setSession(sessionPayload);

      const tenantId = Number(sessionPayload?.user?.tenantId ?? 0);
      if (tenantId > 0) {
        const directory = await loadLoginTenantDirectory().catch(() => null);
        if (active && directory?.state === "ready") {
          setTenantName(findTenantById(directory.tenants, String(tenantId))?.name ?? null);
        }
      }

      const analyticsRes = await fetch("/api/bff/analytics/kpis", {
        method: "GET",
        cache: "no-store",
        credentials: "include",
      }).catch(() => null);
      if (active && analyticsRes?.ok) {
        const payload = await analyticsRes.json().catch(() => null) as DashboardSnapshot | null;
        if (payload) {
          setAnalytics(payload);
        }
      }

      if (section?.resources?.length) {
        const loaded = await Promise.all(section.resources.map((resource) => fetchResource(resource)));
        if (active) {
          setResources(loaded);
        }
      } else if (active) {
        setResources([]);
      }
    })();

    return () => {
      active = false;
    };
  }, [section?.resources, roleKey]);

  const kpiPreview = useMemo(() => {
    if (!analytics) {
      return [] as Array<{ label: string; value: string }>;
    }
    const metricMap = new Map(analytics.kpis.map((item) => [item.key, item.value]));
    return [
      { label: "Total students", value: String(Number(metricMap.get("total_students") ?? 0).toLocaleString()) },
      { label: "Total enrollments", value: String(Number(metricMap.get("total_enrollments") ?? 0).toLocaleString()) },
      { label: "Grades submitted", value: String(Number(metricMap.get("total_grades_submitted") ?? 0).toLocaleString()) },
    ];
  }, [analytics]);

  if (!section) {
    return null;
  }

  const permissionList = session?.user?.permissions ?? [];
  const roleList = session?.user?.roles ?? [];
  const relatedLinks = navItems.filter((item) => item.href !== `/${roleKey}/${section.key}` && item.href !== `/${roleKey}`).slice(0, 3);

  return (
    <main className="min-h-screen bg-transparent px-4 py-8 sm:px-6">
      <section className="mx-auto max-w-5xl space-y-6">
        <div className="overflow-hidden rounded-[28px] border border-border/70 bg-card/80 shadow-[0_24px_70px_rgba(15,23,42,0.08)] backdrop-blur">
          <div className="bg-[linear-gradient(135deg,rgba(8,145,178,0.12),rgba(15,23,42,0.02)_55%,rgba(29,78,216,0.08))] px-6 py-8 sm:px-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-primary/80">
              {config.roleLabel}
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-foreground">{section.title}</h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-muted-foreground sm:text-base">
              {section.subtitle}
            </p>
          </div>

          <div className="grid gap-4 px-6 py-6 sm:px-8 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="space-y-4">
              <div className="rounded-3xl border border-border/70 bg-background/75 p-5 shadow-sm">
                <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">What you can do here</h2>
                <ul className="mt-4 space-y-3 text-sm leading-7 text-foreground">
                  {section.bullets.map((bullet) => (
                    <li key={bullet} className="flex gap-3">
                      <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-primary" />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {resources.map((resource) => (
                <div key={resource.title} className="rounded-3xl border border-border/70 bg-background/75 p-5 shadow-sm">
                  <div className="flex items-center justify-between gap-3">
                    <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">{resource.title}</h2>
                    {typeof resource.total === "number" ? <span className="text-xs font-medium text-muted-foreground">{resource.total} records</span> : null}
                  </div>

                  {resource.error ? (
                    <p className="mt-3 text-sm text-destructive">{resource.error}</p>
                  ) : resource.kind === "list" ? (
                    resource.items && resource.items.length > 0 ? (
                      <div className="mt-4 space-y-3">
                        {resource.items.map((item, index) => (
                          <div key={`${resource.title}-${index}`} className="rounded-2xl border border-border/60 bg-card px-4 py-3">
                            {resource.fields.map((field) => (
                              <div key={field.key} className="flex items-start justify-between gap-4 py-1 text-sm">
                                <span className="text-muted-foreground">{field.label}</span>
                                <span className="text-right font-medium text-foreground">{formatValue(item[field.key])}</span>
                              </div>
                            ))}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="mt-3 text-sm text-muted-foreground">{resource.emptyMessage}</p>
                    )
                  ) : resource.object ? (
                    <div className="mt-4 rounded-2xl border border-border/60 bg-card px-4 py-3">
                      {resource.fields.map((field) => (
                        <div key={field.key} className="flex items-start justify-between gap-4 py-1 text-sm">
                          <span className="text-muted-foreground">{field.label}</span>
                          <span className="text-right font-medium text-foreground">{formatValue(resource.object?.[field.key])}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-3 text-sm text-muted-foreground">{resource.emptyMessage}</p>
                  )}
                </div>
              ))}
            </div>

            <div className="space-y-4 rounded-3xl border border-border/70 bg-secondary/45 p-5 shadow-sm">
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Live account context</h2>
                <div className="mt-3 space-y-2 text-sm">
                  <div className="flex items-start justify-between gap-4"><span className="text-muted-foreground">Signed in as</span><span className="text-right font-medium text-foreground">{session?.user?.displayName ?? "-"}</span></div>
                  <div className="flex items-start justify-between gap-4"><span className="text-muted-foreground">User ID</span><span className="text-right font-medium text-foreground">{session?.user?.sub ?? "-"}</span></div>
                  <div className="flex items-start justify-between gap-4"><span className="text-muted-foreground">Roles</span><span className="text-right font-medium text-foreground">{roleList.join(", ") || "-"}</span></div>
                  <div className="flex items-start justify-between gap-4"><span className="text-muted-foreground">Tenant</span><span className="text-right font-medium text-foreground">{tenantName ?? session?.user?.tenantId ?? "-"}</span></div>
                  <div className="flex items-start justify-between gap-4"><span className="text-muted-foreground">Language</span><span className="text-right font-medium text-foreground">{session?.user?.language ?? "-"}</span></div>
                </div>
              </div>

              <div>
                <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Current access snapshot</h2>
                <p className="mt-2 text-sm leading-7 text-foreground">
                  {permissionList.length > 0
                    ? `This account currently exposes ${permissionList.length} permission(s) through the session.`
                    : "This account currently has no explicit frontend-visible permissions in the session payload."}
                </p>
                {permissionList.length > 0 ? (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {permissionList.slice(0, 8).map((permission) => (
                      <span key={permission} className="rounded-full border border-border/70 bg-card px-2.5 py-1 text-xs font-medium text-foreground">
                        {permission}
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>

              <div>
                <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Live KPI snapshot</h2>
                {kpiPreview.length > 0 ? (
                  <div className="mt-3 space-y-2">
                    {kpiPreview.map((kpi) => (
                      <div key={kpi.label} className="flex items-start justify-between gap-4 rounded-2xl border border-border/70 bg-card px-4 py-3 text-sm">
                        <span className="text-muted-foreground">{kpi.label}</span>
                        <span className="font-semibold text-foreground">{kpi.value}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="mt-2 text-sm text-muted-foreground">KPI snapshot is currently unavailable.</p>
                )}
              </div>

              <div>
                <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Next actions</h2>
                <div className="mt-3 space-y-2">
                  {relatedLinks.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      className="flex items-center justify-between rounded-2xl border border-border/70 bg-card px-4 py-3 text-sm font-medium text-foreground transition hover:border-primary/35 hover:bg-accent"
                    >
                      <span>{item.label}</span>
                      <span className="text-xs uppercase tracking-[0.14em] text-muted-foreground">Open</span>
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}