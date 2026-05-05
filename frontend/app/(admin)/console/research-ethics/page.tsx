"use client";

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
  useResearchEthicsBrainContext,
  useResearchEthicsReviews,
} from "@/modules/research-ethics/hooks";
import type { ResearchEthicsReviewRecord } from "@/modules/research-ethics/types";

const KPI_KEYS = [
  "research_ethics_review_cases_count",
  "research_ethics_high_risk_count",
  "research_ethics_missing_documents_count",
  "research_ethics_requires_approval_count",
] as const;

const KPI_LABELS: Record<string, string> = {
  research_ethics_review_cases_count: "Ethics Review Cases",
  research_ethics_high_risk_count: "Ethics High Risk",
  research_ethics_missing_documents_count: "Missing Documents",
  research_ethics_requires_approval_count: "Approval Needed",
};

function formatDate(value?: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString();
}

function statusVariant(status?: string | null): "success" | "warning" | "info" | "outline" {
  switch (String(status || "").trim().toLowerCase()) {
    case "approved":
      return "success";
    case "pending":
    case "under_review":
    case "revision_requested":
      return "warning";
    case "rejected":
      return "outline";
    default:
      return "info";
  }
}

function riskVariant(riskLevel?: string | null): "destructive" | "warning" | "success" | "outline" {
  switch (String(riskLevel || "").trim().toLowerCase()) {
    case "critical":
    case "high":
      return "destructive";
    case "medium":
      return "warning";
    case "minimal":
    case "low":
      return "success";
    default:
      return "outline";
  }
}

function safeErrorMessage(error: unknown): string {
  if (error instanceof ApiRequestError && (error.status === 401 || error.status === 403)) {
    return "Access to research ethics data is restricted for this account.";
  }
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }
  return "Unable to load research ethics data.";
}

function SummaryCard({ label, value, testId }: { label: string; value: number | string; testId: string }) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm" data-testid={testId}>
      <p className="text-sm text-gray-600">{label}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

function ResearchEthicsTable({ records }: { records: ResearchEthicsReviewRecord[] }) {
  return (
    <div className="overflow-hidden rounded-lg border bg-white shadow-sm">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">Review</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">PI</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">Type</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">Status</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">Risk</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">Committee</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">Submitted</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700">Decision</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {records.map((record) => (
            <tr key={record.id} data-testid={`research-ethics-row-${record.id}`}>
              <td className="px-4 py-4 align-top">
                <div className="flex flex-col gap-1">
                  <span className="text-sm font-medium text-gray-900">{record.review_code || "—"}</span>
                  <span className="text-sm text-gray-600">{record.project_title || "Untitled project"}</span>
                </div>
              </td>
              <td className="px-4 py-4 text-sm text-gray-700">{record.principal_investigator_id || "—"}</td>
              <td className="px-4 py-4 text-sm text-gray-700">{record.review_type || "—"}</td>
              <td className="px-4 py-4">
                <Badge variant={statusVariant(record.status)} data-testid={`status-badge-${record.id}`}>
                  {record.status || "unknown"}
                </Badge>
              </td>
              <td className="px-4 py-4">
                <Badge variant={riskVariant(record.risk_level)} data-testid={`risk-badge-${record.id}`}>
                  {record.risk_level || "unknown"}
                </Badge>
              </td>
              <td className="px-4 py-4 text-sm text-gray-700">{record.committee_name || "—"}</td>
              <td className="px-4 py-4 text-sm text-gray-700">{formatDate(record.submission_date)}</td>
              <td className="px-4 py-4 text-sm text-gray-700">{formatDate(record.decision_date)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ResearchEthicsPage() {
  const [status, setStatus] = useState<string>("all");
  const [riskLevel, setRiskLevel] = useState<string>("all");

  const reviews = useResearchEthicsReviews({
    status: status !== "all" ? status : undefined,
    risk_level: riskLevel !== "all" ? riskLevel : undefined,
  });
  const brainContext = useResearchEthicsBrainContext();

  const records = useMemo(() => reviews.data?.records ?? [], [reviews.data?.records]);
  const error = reviews.error ?? brainContext.error;

  if (error instanceof ApiRequestError && (error.status === 401 || error.status === 403)) {
    return <AccessDenied message="Research ethics data requires research.read access." />;
  }

  if ((reviews.isLoading && !reviews.data) || (brainContext.isLoading && !brainContext.data)) {
    return <LoadingState title="Loading research ethics" message="Fetching review queue, compliance status, and KPI visibility." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Failed to load research ethics"
        message={safeErrorMessage(error)}
        onRetry={() => {
          void reviews.refetch();
          void brainContext.refetch();
        }}
      />
    );
  }

  const context = brainContext.data;

  return (
    <RequirePermission permission={PERMISSIONS.RESEARCH_READ}>
      <div className="space-y-6" data-testid="research-ethics-page">
        <PageHeader
          title="Research Ethics"
          description="Review human-governed ethics submissions, risk signals, and compliance readiness without automating final outcomes."
          icon={ShieldCheck}
        />

        <section data-testid="wave4-research-ethics-kpi-section">
          <Wave1KpiBar metricKeys={[...KPI_KEYS]} labels={KPI_LABELS} />
        </section>

        <section data-testid="research-ethics-human-review-note" className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          Final ethics approval, rejection, sanctions, and research suspension remain human-reviewed. This page surfaces status, risk, and actionability only.
        </section>

        <section data-testid="research-ethics-summary-section" className="grid gap-4 md:grid-cols-5">
          <SummaryCard label="Total Reviews" value={context?.total_reviews ?? 0} testId="summary-total-reviews" />
          <SummaryCard label="Pending" value={context?.pending_reviews ?? 0} testId="summary-pending-reviews" />
          <SummaryCard label="Approved" value={context?.approved_reviews ?? 0} testId="summary-approved-reviews" />
          <SummaryCard label="Rejected" value={context?.rejected_reviews ?? 0} testId="summary-rejected-reviews" />
          <SummaryCard label="High Risk" value={context?.high_risk_reviews ?? 0} testId="summary-high-risk-reviews" />
        </section>

        <section data-testid="research-ethics-compliance-section" className="rounded-lg border bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Compliance Snapshot</h2>
              <p className="text-sm text-gray-600">Brain-context snapshot from existing research ethics backend contract.</p>
            </div>
            <Badge variant={statusVariant(context?.compliance_status)} data-testid="compliance-status-badge">
              {context?.compliance_status || "unknown"}
            </Badge>
          </div>
        </section>

        <section data-testid="research-ethics-filters-section" className="rounded-lg border bg-white p-4 shadow-sm">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label htmlFor="status-filter" className="mb-2 block text-sm font-medium text-gray-700">Status</label>
              <select
                id="status-filter"
                data-testid="status-filter"
                value={status}
                onChange={(event) => setStatus(event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2"
              >
                <option value="all">All statuses</option>
                <option value="pending">Pending</option>
                <option value="under_review">Under review</option>
                <option value="revision_requested">Revision requested</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
            <div>
              <label htmlFor="risk-filter" className="mb-2 block text-sm font-medium text-gray-700">Risk level</label>
              <select
                id="risk-filter"
                data-testid="risk-filter"
                value={riskLevel}
                onChange={(event) => setRiskLevel(event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2"
              >
                <option value="all">All risk levels</option>
                <option value="minimal">Minimal</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>
        </section>

        <section data-testid="research-ethics-list-section">
          <div className="mb-4">
            <h2 className="text-lg font-semibold">Ethics Review Queue</h2>
            <p className="text-sm text-gray-600">Tenant-scoped review records from the existing `/api/admin/research-ethics/reviews` contract.</p>
          </div>

          {records.length === 0 ? (
            <EmptyState
              title="No research ethics reviews found"
              description="No review records match the current filters for this tenant."
            />
          ) : (
            <ResearchEthicsTable records={records} />
          )}
        </section>
      </div>
    </RequirePermission>
  );
}
