"use client";

import { useMemo } from "react";
import { AlertCircle, AlertTriangle, Clock, User } from "lucide-react";
import { Skeleton } from "@/shared/ui/skeleton";
import { useLanguage } from "@/app/components/LanguageProvider";
import { useAdminAuth } from "@/shared/auth/context";
import { useInterventionCases } from "./hooks";

export function InterventionsSummaryStats() {
  const { t } = useLanguage();
  const { user } = useAdminAuth();

  // Fetch with different filters in parallel
  const openQuery = useInterventionCases({ status: "open", page_size: 1 });
  const overdueQuery = useInterventionCases({ overdue_only: true, page_size: 1 });
  const highSeverityQuery = useInterventionCases({ severity: "high", page_size: 1 });
  const assignedToMeQuery = useInterventionCases({ assignee_ref: user?.sub ?? "", page_size: 1 });

  const stats = useMemo(
    () => [
      {
        id: "open",
        label: t("intervention.stat.open"),
        value: openQuery.data?.total ?? 0,
        isLoading: openQuery.isLoading,
        icon: AlertTriangle,
        color: "text-blue-600",
        bgColor: "bg-blue-50 dark:bg-blue-900/20",
      },
      {
        id: "overdue",
        label: t("intervention.stat.overdue"),
        value: overdueQuery.data?.total ?? 0,
        isLoading: overdueQuery.isLoading,
        icon: Clock,
        color: "text-red-600",
        bgColor: "bg-red-50 dark:bg-red-900/20",
      },
      {
        id: "high_severity",
        label: t("intervention.stat.highSeverity"),
        value: highSeverityQuery.data?.total ?? 0,
        isLoading: highSeverityQuery.isLoading,
        icon: AlertCircle,
        color: "text-orange-600",
        bgColor: "bg-orange-50 dark:bg-orange-900/20",
      },
      {
        id: "assigned_to_me",
        label: t("intervention.stat.assignedToMe"),
        value: assignedToMeQuery.data?.total ?? 0,
        isLoading: assignedToMeQuery.isLoading,
        icon: User,
        color: "text-purple-600",
        bgColor: "bg-purple-50 dark:bg-purple-900/20",
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [
      t,
      openQuery.data?.total,
      overdueQuery.data?.total,
      highSeverityQuery.data?.total,
      assignedToMeQuery.data?.total,
      openQuery.isLoading,
      overdueQuery.isLoading,
      highSeverityQuery.isLoading,
      assignedToMeQuery.isLoading,
    ],
  );

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <div key={stat.id} className={`rounded-lg border p-4 ${stat.bgColor}`}>
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
                {stat.isLoading ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-3xl font-bold tabular-nums">{stat.value}</p>
                )}
              </div>
              <Icon className={`h-5 w-5 ${stat.color}`} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
