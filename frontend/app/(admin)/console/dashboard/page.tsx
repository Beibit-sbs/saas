"use client";

import { useMemo } from "react";
import { Button } from "@/shared/ui/button";
import { EmptyState } from "@/shared/ui/empty-state";
import { ErrorState } from "@/shared/ui/error-state";
import { PageHeader } from "@/shared/ui/page-header";
import { Skeleton } from "@/shared/ui/skeleton";
import { formatDate, formatRelative } from "@/shared/utils/format";
import { PERMISSIONS } from "@/shared/config/permissions";
import { LayoutDashboard, RefreshCw, CalendarDays, BarChart3, FileText, GraduationCap, BookOpen, ClipboardCheck } from "lucide-react";
import { KpiCard } from "@/modules/platform/kpi/kpi-card";
import { useRectorDashboard } from "@/modules/platform/kpi/use-dashboard";
import { AutomationOverviewWidget } from "@/modules/platform/automation/automation-overview-widget";
import Link from "next/link";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { useAdminAuth } from "@/shared/auth/context";

function DashboardSkeletonGrid() {
  return (
    <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3" data-testid="kpi-loading-grid">
      {Array.from({ length: 6 }).map((_, idx) => (
        <div key={idx} className="rounded-lg border bg-card p-6">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="mt-3 h-8 w-24" />
          <Skeleton className="mt-4 h-8 w-full" />
        </div>
      ))}
    </div>
  );
}

export default function RectorDashboardPage() {
  const { user } = useAdminAuth();
  const tenantId = user?.tenantId ?? 0;
  const { roles, hasPermission } = usePermissions();
  const { data, isLoading, isError, refetch } = useRectorDashboard(tenantId);

  const generatedLabel = useMemo(() => {
    if (!data?.generated_at) return "n/a";
    return formatRelative(data.generated_at);
  }, [data?.generated_at]);

  // Student dashboard
  if (roles.includes("student")) {
    return (
      <div className="space-y-6" data-testid="student-dashboard">
        <PageHeader title="Dashboard" icon={LayoutDashboard} />
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
          <Link href="/console/scheduling" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <CalendarDays className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">Schedule</p>
            <p className="text-xs text-muted-foreground">View your course timetable</p>
          </Link>
          <Link href="/console/grades" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">Grades</p>
            <p className="text-xs text-muted-foreground">Check your current grades</p>
          </Link>
          <Link href="/console/transcripts" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <FileText className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">Transcript</p>
            <p className="text-xs text-muted-foreground">View or download your transcript</p>
          </Link>
        </div>
      </div>
    );
  }

  // Teacher dashboard
  if (roles.includes("teacher")) {
    return (
      <div className="space-y-6" data-testid="teacher-dashboard">
        <PageHeader title="Dashboard" icon={LayoutDashboard} />
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
          <Link href="/console/students" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <GraduationCap className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">Students</p>
            <p className="text-xs text-muted-foreground">Browse all enrolled students</p>
          </Link>
          <Link href="/console/grades" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">Grades</p>
            <p className="text-xs text-muted-foreground">Enter and manage grades</p>
          </Link>
          <Link href="/console/enrollments" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <ClipboardCheck className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">Requests</p>
            <p className="text-xs text-muted-foreground">Pending enrollment requests</p>
          </Link>
        </div>
      </div>
    );
  }

  // Dean dashboard
  if (roles.includes("dean")) {
    return (
      <div className="space-y-6" data-testid="dean-dashboard">
        <PageHeader title="Dashboard" icon={LayoutDashboard} />
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
          <Link href="/console/students" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <GraduationCap className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">Students</p>
            <p className="text-xs text-muted-foreground">Student records & status</p>
          </Link>
          <Link href="/console/enrollments" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">Enrollments</p>
            <p className="text-xs text-muted-foreground">Enrollment management</p>
          </Link>
          <Link href="/console/grades" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">Grades</p>
            <p className="text-xs text-muted-foreground">Faculty grade summary</p>
          </Link>
          <Link href="/console/scheduling" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <CalendarDays className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">Scheduling</p>
            <p className="text-xs text-muted-foreground">Course sections & timetable</p>
          </Link>
        </div>
        {hasPermission(PERMISSIONS.METRICS_READ) && (
          <div>
            {isLoading && <DashboardSkeletonGrid />}
            {!isLoading && !isError && data && data.cards.length > 0 && (
              <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
                {data.cards.map((card) => (
                  <KpiCard key={card.metric_key} title={card.title} value={card.value} trendPoints={card.trend_7d} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Admin / operator / viewer — full executive dashboard
  return (
    <div className="space-y-6" data-testid="rector-dashboard-page">
      <PageHeader
        title="University Executive Dashboard"
        description={`Data date: ${data?.snapshot_date ? formatDate(data.snapshot_date) : "—"} | Generated: ${generatedLabel}`}
        icon={LayoutDashboard}
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => { void refetch(); }}
            disabled={isLoading}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        }
      />

      {isLoading && <DashboardSkeletonGrid />}

      {isError && !isLoading && (
        <ErrorState
          title="Failed to load executive dashboard"
          message="KPI data is temporarily unavailable."
          onRetry={() => { void refetch(); }}
        />
      )}

      {!isLoading && !isError && (!data || data.cards.length === 0) && (
        <EmptyState
          title="No KPI data yet"
          description="No dashboard cards are available for the selected data interval."
          action={
            <Button variant="outline" onClick={() => { void refetch(); }}>
              Retry
            </Button>
          }
        />
      )}

      {!isLoading && !isError && data && data.cards.length > 0 && (
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3" data-testid="kpi-cards-grid">
          {data.cards.map((card) => (
            <KpiCard key={card.metric_key} title={card.title} value={card.value} trendPoints={card.trend_7d} />
          ))}
        </div>
      )}

      <AutomationOverviewWidget tenantId={tenantId} />
    </div>
  );
}
