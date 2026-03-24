"use client";

import Link from "next/link";
import { Bot, ChevronRight, CheckCircle2, AlertCircle, Activity } from "lucide-react";

import { PermissionGate } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import { Skeleton } from "@/shared/ui/skeleton";

import { useAutomationRules } from "@/modules/platform/automation/use-rules";
import { useAutomationExecutions } from "@/modules/platform/automation/use-executions";

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatCard({
  icon: Icon,
  label,
  value,
  iconClassName,
}: {
  icon: React.ElementType;
  label: string;
  value: number | string;
  iconClassName?: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-muted">
        <Icon className={`h-4 w-4 ${iconClassName ?? "text-muted-foreground"}`} />
      </div>
      <div>
        <div className="text-xl font-semibold tabular-nums">{value}</div>
        <div className="text-xs text-muted-foreground">{label}</div>
      </div>
    </div>
  );
}

function StatSkeleton() {
  return (
    <div className="flex items-center gap-3">
      <Skeleton className="h-9 w-9 rounded-md" />
      <div className="space-y-1.5">
        <Skeleton className="h-5 w-12" />
        <Skeleton className="h-3 w-20" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Widget
// ---------------------------------------------------------------------------

function AutomationOverviewWidgetInner({ tenantId }: { tenantId: number }) {
  const { data: rules, isLoading: rulesLoading } = useAutomationRules(tenantId);
  const { data: executions, isLoading: execLoading } = useAutomationExecutions(tenantId);

  const isLoading = rulesLoading || execLoading;

  const activeRules = rules ? rules.filter((r) => r.is_active).length : 0;

  const today = new Date().toDateString();
  const todayExecutions = executions
    ? executions.filter((e) => new Date(e.executed_at).toDateString() === today).length
    : 0;

  const failedExecutions = executions ? executions.filter((e) => e.status === "failed").length : 0;

  return (
    <div
      className="rounded-lg border bg-card p-5 space-y-4"
      data-testid="automation-overview-widget"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Automation</span>
        </div>
        <Link
          href="/console/automation"
          className="flex items-center gap-0.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          data-testid="automation-widget-link"
        >
          View rules
          <ChevronRight className="h-3 w-3" />
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {isLoading ? (
          <>
            <StatSkeleton />
            <StatSkeleton />
            <StatSkeleton />
          </>
        ) : (
          <>
            <StatCard
              icon={CheckCircle2}
              label="Active rules"
              value={activeRules}
              iconClassName="text-success"
            />
            <StatCard
              icon={Activity}
              label="Runs today"
              value={todayExecutions}
            />
            <StatCard
              icon={AlertCircle}
              label="Failed"
              value={failedExecutions}
              iconClassName={failedExecutions > 0 ? "text-destructive" : "text-muted-foreground"}
            />
          </>
        )}
      </div>

      {/* Quick link to executions */}
      <div className="border-t pt-3">
        <Link
          href="/console/automation/executions"
          className="text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
        >
          <Activity className="h-3 w-3" />
          View execution log
        </Link>
      </div>
    </div>
  );
}

export function AutomationOverviewWidget({ tenantId = 1 }: { tenantId?: number }) {
  return (
    <PermissionGate permission={PERMISSIONS.AUTOMATION_READ}>
      <AutomationOverviewWidgetInner tenantId={tenantId} />
    </PermissionGate>
  );
}
