"use client";

import { useMemo } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { getNavigationForRoles } from "@/shared/config/navigation";
import { canAccessPlatformBillingForRoles } from "@/shared/config/role-catalog";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { useLanguage } from "@/app/components/LanguageProvider";
import { cn } from "@/shared/utils/cn";
import { GraduationCap } from "lucide-react";

const NAV_LABEL_KEY: Record<string, string> = {
  Overview: "nav.overview",
  Platform: "nav.platform",
  Academic: "nav.academic",
  Dashboard: "nav.dashboard",
  Tenants: "nav.tenants",
  "Feature Flags": "nav.featureFlags",
  Jobs: "nav.jobs",
  Notifications: "nav.notifications",
  "Health & Metrics": "nav.healthMetrics",
  "Platform Ops": "nav.platformOps",
  Automation: "nav.automation",
  "AI Copilot": "nav.aiCopilot",
  "Brain Core": "nav.brainCore",
  "Policy Settings": "nav.brainPolicySettings",
  Federation: "nav.federation",
  "Developer Apps": "nav.developerApps",
  Students: "nav.students",
  Enrollments: "nav.enrollments",
  Grades: "nav.grades",
  Transcripts: "nav.transcripts",
  Thesis: "nav.thesis",
  "Degree Progress": "nav.degreeProgress",
  Scheduling: "nav.scheduling",
  "My Space": "nav.mySpace",
  "My Work": "nav.myWork",
  Faculty: "nav.faculty",
  "Identity & Access": "nav.identityAccess",
  Profiles: "nav.profiles",
  Operations: "nav.operations",
  "Users & Roles": "nav.usersRoles",
  "Platform Management": "nav.platformManagement",
  "Control Plane": "nav.controlPlane",
  Languages: "nav.languages",
  "Local Users": "nav.localUsers",
  RBAC: "nav.rbac",
  Integrations: "nav.integrations",
  Backups: "nav.backups",
  Audit: "nav.audit",
  System: "nav.system",
  University: "nav.university",
  Rules: "nav.rules",
  Executions: "nav.executions",
  Schedule: "nav.schedule",
  Transcript: "nav.transcript",
  Requests: "nav.requests",
  Admissions: "nav.admissions",
  Interventions: "nav.interventions",
  "Expense Controls": "nav.expenseControls",
};

function normalizePath(path: string): string {
  if (path.length > 1 && path.endsWith("/")) {
    return path.slice(0, -1);
  }
  return path;
}

function matchesNavItem(pathname: string, href: string): boolean {
  const currentPath = normalizePath(pathname);
  const itemPath = normalizePath(href);

  if (itemPath === "/console") {
    return currentPath === "/console";
  }

  return currentPath === itemPath || currentPath.startsWith(itemPath + "/");
}

function isPlatformOnlyBillingNav(href: string): boolean {
  return href === "/console/platform/billing-plans" || href === "/console/platform/usage-quotas";
}

export function AppSidebar() {
  const pathname = usePathname();
  const { hasPermission, roles } = usePermissions();
  const { t } = useLanguage();
  const navigation = getNavigationForRoles(roles);
  const canAccessPlatformBilling = canAccessPlatformBillingForRoles(roles);

  const visibleNavigation = useMemo(
    () =>
      navigation
        .map((group) => ({
          ...group,
          items: group.items.filter((item) =>
            (canAccessPlatformBilling || !isPlatformOnlyBillingNav(item.href))
            && (item.permission ? hasPermission(item.permission) : true),
          ),
        }))
        .filter((group) => group.items.length > 0),
    [canAccessPlatformBilling, hasPermission, navigation],
  );

  const activeHref = useMemo(() => {
    const matchedItems = visibleNavigation
      .flatMap((group) => group.items)
      .filter((item) => matchesNavItem(pathname, item.href));

    if (matchedItems.length === 0) {
      return null;
    }

    // Prefer the most specific route to avoid multiple highlighted items.
    return [...matchedItems].sort(
      (left, right) => right.href.length - left.href.length,
    )[0].href;
  }, [pathname, visibleNavigation]);

  const tx = (label: string) => {
    const key = NAV_LABEL_KEY[label];
    return key ? t(key as never) : label;
  };

  return (
    <aside className="flex h-screen w-72 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground shadow-[16px_0_40px_rgba(15,23,42,0.18)]">
      <div className="relative overflow-hidden border-b border-sidebar-border px-5 py-4">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(56,189,248,0.22),transparent_48%),linear-gradient(180deg,rgba(255,255,255,0.05),transparent)]" />
        <div className="relative flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-white/12 backdrop-blur">
            <GraduationCap className="h-5 w-5 text-sidebar-accent" />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-sidebar-foreground/55">
              University OS
            </p>
            <span className="block truncate text-sm font-semibold text-sidebar-foreground">
              AI University Platform
            </span>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
        {visibleNavigation.map((group) => {
          return (
            <div key={group.label}>
              <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-sidebar-foreground/45">
                {tx(group.label)}
              </p>
              {group.items.map((item) => {
                const Icon = item.icon;
                const active = item.href === activeHref;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "group mb-1.5 flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm transition-all duration-200",
                      active
                        ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-[0_14px_30px_rgba(8,145,178,0.28)]"
                        : "text-sidebar-foreground/82 hover:bg-white/8 hover:text-sidebar-foreground",
                    )}
                  >
                    <span
                      className={cn(
                        "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ring-1 transition-colors",
                        active
                          ? "bg-white/14 ring-white/15"
                          : "bg-white/5 ring-white/8 group-hover:bg-white/10 group-hover:ring-white/12",
                      )}
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                    </span>
                    <span className="truncate font-medium">{tx(item.label)}</span>
                  </Link>
                );
              })}
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
