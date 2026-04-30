"use client";

import { useMemo } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { getNavigationForRoles } from "@/shared/config/navigation";
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

export function AppSidebar() {
  const pathname = usePathname();
  const { hasPermission, roles } = usePermissions();
  const { t } = useLanguage();
  const navigation = getNavigationForRoles(roles);

  const visibleNavigation = useMemo(
    () =>
      navigation
        .map((group) => ({
          ...group,
          items: group.items.filter((item) =>
            item.permission ? hasPermission(item.permission) : true,
          ),
        }))
        .filter((group) => group.items.length > 0),
    [hasPermission, navigation],
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
    <aside className="flex h-screen w-60 flex-col border-r bg-sidebar">
      <div className="flex h-14 items-center gap-2 border-b px-4">
        <GraduationCap className="h-5 w-5 text-primary" />
        <span className="font-semibold text-sm">AI University Platform</span>
      </div>

      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-4">
        {visibleNavigation.map((group) => {
          return (
            <div key={group.label}>
              <p className="mb-1 px-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
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
                      "flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm transition-colors",
                      active
                        ? "bg-primary/10 text-primary font-medium"
                        : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    {tx(item.label)}
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
