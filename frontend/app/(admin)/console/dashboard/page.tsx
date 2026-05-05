"use client";

import { useMemo } from "react";
import { Button } from "@/shared/ui/button";
import { EmptyState } from "@/shared/ui/empty-state";
import { ErrorState } from "@/shared/ui/error-state";
import { PageHeader } from "@/shared/ui/page-header";
import { Skeleton } from "@/shared/ui/skeleton";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { formatDate, formatRelative } from "@/shared/utils/format";
import { PERMISSIONS } from "@/shared/config/permissions";
import { LayoutDashboard, RefreshCw, CalendarDays, BarChart3, FileText, GraduationCap, BookOpen, ClipboardCheck } from "lucide-react";
import { KpiCard } from "@/modules/platform/kpi/kpi-card";
import { Wave1KpiBar } from "@/modules/platform/kpi/wave1-kpi-bar";
import { useRectorDashboard } from "@/modules/platform/kpi/use-dashboard";
import { AutomationOverviewWidget } from "@/modules/platform/automation/automation-overview-widget";
import Link from "next/link";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { useAdminAuth } from "@/shared/auth/context";
import { useLanguage } from "@/app/components/LanguageProvider";

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
  const { t } = useLanguage();
  const tenantId = user?.tenantId ?? 0;
  const { roles, hasPermission } = usePermissions();
  const { data, isLoading, isError, refetch } = useRectorDashboard(tenantId);

  const generatedLabel = useMemo(() => {
    if (!data?.generated_at) return t("ui.na");
    return formatRelative(data.generated_at);
  }, [data?.generated_at, t]);

  // Student dashboard
  if (roles.includes("student")) {
    return (
      <div className="space-y-6" data-testid="student-dashboard">
        <PageHeader title={t("nav.dashboard")} icon={LayoutDashboard} />
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
          <Link href="/console/scheduling" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <CalendarDays className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.student.scheduleTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.student.scheduleDescription")}</p>
          </Link>
          <Link href="/console/grades" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.student.gradesTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.student.gradesDescription")}</p>
          </Link>
          <Link href="/console/transcripts" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <FileText className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.student.transcriptTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.student.transcriptDescription")}</p>
          </Link>
        </div>
      </div>
    );
  }

  // Teacher dashboard
  if (roles.includes("teacher")) {
    return (
      <div className="space-y-6" data-testid="teacher-dashboard">
        <PageHeader title={t("nav.dashboard")} icon={LayoutDashboard} />
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
          <Link href="/console/students" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <GraduationCap className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.teacher.studentsTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.teacher.studentsDescription")}</p>
          </Link>
          <Link href="/console/grades" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.teacher.gradesTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.teacher.gradesDescription")}</p>
          </Link>
          <Link href="/console/enrollments" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <ClipboardCheck className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.teacher.requestsTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.teacher.requestsDescription")}</p>
          </Link>
        </div>
      </div>
    );
  }

  // Dean dashboard
  if (roles.includes("dean")) {
    return (
      <div className="space-y-6" data-testid="dean-dashboard">
        <PageHeader title={t("nav.dashboard")} icon={LayoutDashboard} />
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
          <Link href="/console/students" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <GraduationCap className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.dean.studentsTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.dean.studentsDescription")}</p>
          </Link>
          <Link href="/console/enrollments" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.dean.enrollmentsTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.dean.enrollmentsDescription")}</p>
          </Link>
          <Link href="/console/grades" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.dean.gradesTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.dean.gradesDescription")}</p>
          </Link>
          <Link href="/console/scheduling" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <CalendarDays className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.dean.schedulingTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.dean.schedulingDescription")}</p>
          </Link>
        </div>
        {hasPermission(PERMISSIONS.METRICS_READ) && (
          <div>
            {isLoading && <DashboardSkeletonGrid />}
            {!isLoading && !isError && data && data.cards.length > 0 && (
              <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
                {data.cards.map((card) => (
                  <KpiCard key={card.metric_key} title={card.title} value={card.value} trendPoints={card.trend_7d} severityLevel={(card.metadata_json?.severity_level as "warning" | "critical" | null) ?? null} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Admin / operator / viewer — full executive dashboard
  if (!hasPermission(PERMISSIONS.DASHBOARD_READ)) return <AccessDenied />;

  return (
    <div className="space-y-6" data-testid="rector-dashboard-page">
      <PageHeader
        title={t("dashboard.executive.title")}
        description={t("dashboard.executive.dataDate")
          .replace("{date}", data?.snapshot_date ? formatDate(data.snapshot_date) : "-")
          .replace("{generated}", generatedLabel)}
        icon={LayoutDashboard}
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => { void refetch(); }}
            disabled={isLoading}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            {t("dashboard.executive.refresh")}
          </Button>
        }
      />

      {isLoading && <DashboardSkeletonGrid />}

      {isError && !isLoading && (
        <ErrorState
          title={t("dashboard.executive.loadFailedTitle")}
          message={t("dashboard.executive.loadFailedMessage")}
          onRetry={() => { void refetch(); }}
        />
      )}

      {!isLoading && !isError && (!data || data.cards.length === 0) && (
        <EmptyState
          title={t("dashboard.executive.noDataTitle")}
          description={t("dashboard.executive.noDataDescription")}
          action={
            <Button variant="outline" onClick={() => { void refetch(); }}>
              {t("dashboard.executive.retry")}
            </Button>
          }
        />
      )}

      {!isLoading && !isError && data && data.cards.length > 0 && (
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3" data-testid="kpi-cards-grid">
          {data.cards.map((card) => (
            <KpiCard key={card.metric_key} title={card.title} value={card.value} trendPoints={card.trend_7d} severityLevel={(card.metadata_json?.severity_level as "warning" | "critical" | null) ?? null} />
          ))}
        </div>
      )}

      <section data-testid="wave3-finance-kpi-section">
        <Wave1KpiBar
          metricKeys={["budget_overrun_risk_count","budget_review_actions_count","active_finance_risk_signals_count","finance_operations_actionability_count","asset_conversion_gap_count","inventory_low_stock_items_count","critical_supply_risk_count","supply_risk_actions_count"]}
          labels={{
            budget_overrun_risk_count: "Budget Overrun Risk",
            budget_review_actions_count: "Budget Review Actions",
            active_finance_risk_signals_count: "Finance Risk Signals",
            finance_operations_actionability_count: "Finance Actionability",
            asset_conversion_gap_count: "Asset Conversion Gap",
            inventory_low_stock_items_count: "Low Stock Items",
            critical_supply_risk_count: "Critical Supply Risk",
            supply_risk_actions_count: "Supply Risk Actions",
          }}
        />
      </section>

      <AutomationOverviewWidget tenantId={tenantId} />
    </div>
  );
}
