"use client";

/**
 * Exam Proctoring Admin Page
 * Provides oversight of AI-camera proctoring sessions, violation signals, and integrity KPIs.
 * Final academic sanctions and session terminations remain human-reviewed.
 */

import { useMemo, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { ApiRequestError } from "@/shared/api/client";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission, AccessDenied } from "@/shared/ui/permission-gate";
import { LoadingState, ErrorState } from "@/shared/ui/page-states";
import { EmptyState } from "@/shared/ui/empty-state";
import { Badge } from "@/shared/ui/badge";
import { PERMISSIONS } from "@/shared/config/permissions";
import { Wave1KpiBar } from "@/modules/platform/kpi/wave1-kpi-bar";
import {
  useExamProctoringDashboard,
  useProctoredExamsList,
} from "@/modules/exam-proctoring/hooks";
import type { ProctoredExamItem } from "@/modules/exam-proctoring/types";

const KPI_KEYS = [
  "exam_proctoring_violations_count",
  "exam_integrity_reviews_count",
  "exam_integrity_high_risk_count",
  "exam_integrity_requires_approval_count",
] as const;

const KPI_LABELS: Record<string, string> = {
  exam_proctoring_violations_count: "Proctoring Violations",
  exam_integrity_reviews_count: "Integrity Reviews",
  exam_integrity_high_risk_count: "High Risk",
  exam_integrity_requires_approval_count: "Approval Needed",
};

type StatusFilter = "all" | "active" | "in_progress" | "scheduled" | "completed";

function statusVariant(
  status?: string | null,
): "success" | "warning" | "info" | "outline" | "destructive" {
  switch (String(status ?? "").trim().toLowerCase()) {
    case "active":
    case "in_progress":
      return "warning";
    case "completed":
    case "ended":
      return "success";
    case "aborted":
    case "cancelled":
      return "destructive";
    default:
      return "info";
  }
}

function proctoringModeLabel(mode?: string | null): string {
  switch (String(mode ?? "").toLowerCase()) {
    case "remote":
      return "Remote";
    case "hybrid":
      return "Hybrid";
    case "in_person":
      return "In-person";
    default:
      return mode ?? "Unknown";
  }
}

function safeErrorMessage(error: unknown): string {
  if (error instanceof ApiRequestError && (error.status === 401 || error.status === 403)) {
    return "Access to exam proctoring data is restricted for this account.";
  }
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }
  return "Unable to load exam proctoring data.";
}

function SummaryCard({
  label,
  value,
  testId,
}: {
  label: string;
  value: number | string;
  testId: string;
}) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm" data-testid={testId}>
      <p className="text-sm text-gray-600">{label}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

function ProctoredExamsTable({ items }: { items: ProctoredExamItem[] }) {
  return (
    <div className="overflow-hidden rounded-lg border bg-white shadow-sm">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">
              Course
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">
              Proctoring Mode
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">
              Scheduled
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {items.map((item) => (
            <tr key={item.id} data-testid={`proctored-exam-row-${item.id}`}>
              <td className="px-4 py-4 align-top">
                <div className="flex flex-col gap-1">
                  <span className="text-sm font-medium text-gray-900">{item.course_code}</span>
                  <span className="text-sm text-gray-600">{item.course_title}</span>
                </div>
              </td>
              <td className="px-4 py-4">
                <Badge
                  variant={statusVariant(item.status)}
                  data-testid={`status-badge-${item.id}`}
                >
                  {item.status}
                </Badge>
              </td>
              <td className="px-4 py-4 text-sm text-gray-700">
                {proctoringModeLabel(item.proctoring_mode)}
              </td>
              <td className="px-4 py-4 text-sm text-gray-700">
                {item.scheduled_date
                  ? `${item.scheduled_date}${item.scheduled_time ? ` ${item.scheduled_time}` : ""}`
                  : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ExamProctoringPage() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  const proctoredExams = useProctoredExamsList({
    status: statusFilter !== "all" ? statusFilter : undefined,
  });
  const dashboard = useExamProctoringDashboard();

  const error = proctoredExams.error ?? dashboard.error;

  const items = useMemo(
    () => proctoredExams.data?.items ?? [],
    [proctoredExams.data?.items],
  );

  const totalExams = dashboard.data?.total_exams ?? 0;
  const breakdown = dashboard.data?.status_breakdown ?? {};

  if (error instanceof ApiRequestError && (error.status === 401 || error.status === 403)) {
    return (
      <AccessDenied message="Exam proctoring data requires exams.read access." />
    );
  }

  if (
    (proctoredExams.isLoading && !proctoredExams.data) ||
    (dashboard.isLoading && !dashboard.data)
  ) {
    return (
      <LoadingState
        title="Loading exam proctoring"
        message="Fetching proctoring session data, violation signals, and KPI visibility."
      />
    );
  }

  if (error) {
    return (
      <ErrorState
        title="Failed to load exam proctoring"
        message={safeErrorMessage(error)}
        onRetry={() => {
          void proctoredExams.refetch();
          void dashboard.refetch();
        }}
      />
    );
  }

  return (
    <RequirePermission permission={PERMISSIONS.DASHBOARD_READ}>
      <div className="space-y-6" data-testid="exam-proctoring-page">
        <PageHeader
          title="Exam Proctoring"
          description="Monitor AI-camera proctoring sessions, flag violations for review, and track integrity signals. Session terminations and academic sanctions remain human-reviewed."
          icon={ShieldCheck}
        />

        <section data-testid="wave4-exam-proctoring-kpi-section">
          <Wave1KpiBar metricKeys={[...KPI_KEYS]} labels={KPI_LABELS} />
        </section>

        <section
          data-testid="exam-proctoring-human-review-note"
          className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900"
        >
          Final exam proctoring decisions — including session suspension, violation escalation, and
          academic sanctions — remain human-reviewed. This page surfaces status, signals, and
          actionability only.
        </section>

        <section
          data-testid="exam-proctoring-summary-section"
          className="grid gap-4 md:grid-cols-4"
        >
          <SummaryCard
            label="Total Exams"
            value={totalExams}
            testId="summary-total-exams"
          />
          <SummaryCard
            label="Scheduled"
            value={breakdown.scheduled ?? 0}
            testId="summary-scheduled"
          />
          <SummaryCard
            label="In Progress"
            value={breakdown.in_progress ?? 0}
            testId="summary-in-progress"
          />
          <SummaryCard
            label="Completed"
            value={breakdown.completed ?? 0}
            testId="summary-completed"
          />
        </section>

        <section data-testid="exam-proctoring-sessions-section">
          <div className="mb-4 flex items-center gap-3">
            <h2 className="text-xl font-semibold text-gray-900">Proctored Exams</h2>
            <select
              data-testid="status-filter"
              className="rounded border border-gray-300 px-3 py-1 text-sm"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
            >
              <option value="all">All Statuses</option>
              <option value="scheduled">Scheduled</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>
          </div>

          {items.length === 0 ? (
            <EmptyState
              title="No proctored exams found"
              description="No proctored exams match the current filter criteria."
            />
          ) : (
            <ProctoredExamsTable items={items} />
          )}
        </section>
      </div>
    </RequirePermission>
  );
}
