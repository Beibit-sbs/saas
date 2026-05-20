'use client';

/**
 * Dashboard Analytics Widgets — A-031.5
 *
 * All widgets:
 * - Render ONLY from backend-provided data
 * - Show "unavailable" state when field is undefined (never substitute with 0)
 * - Must NOT be rendered if fake_metrics !== false or data_source guard fails
 * - No hardcoded KPIs, no mock data
 */

import React from 'react';
import type {
  DashboardSummaryExpanded,
  OverdueAgingBuckets,
  CompletionTrendPoint,
  UnitCompletionRow,
} from '../types';

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

function WidgetUnavailable({ name }: { name: string }) {
  return (
    <div
      className="rounded-lg border border-gray-200 bg-gray-50 p-6 text-center"
      data-testid={`widget-unavailable-${name}`}
    >
      <p className="text-sm text-gray-500">{name} data unavailable.</p>
    </div>
  );
}

function pct(n: number): string {
  return `${(n * 100).toFixed(1)}%`;
}

// ---------------------------------------------------------------------------
// Overdue Aging Widget
// ---------------------------------------------------------------------------

interface OverdueAgingWidgetProps {
  buckets: OverdueAgingBuckets | undefined;
}

export function OverdueAgingWidget({ buckets }: OverdueAgingWidgetProps) {
  if (!buckets) return <WidgetUnavailable name="Overdue aging" />;

  const items = [
    { label: '1–7 days', value: buckets.one_to_seven_days, color: 'bg-yellow-200 text-yellow-800' },
    { label: '8–14 days', value: buckets.eight_to_fourteen_days, color: 'bg-orange-200 text-orange-800' },
    { label: '15–30 days', value: buckets.fifteen_to_thirty_days, color: 'bg-red-200 text-red-800' },
    { label: '30+ days', value: buckets.over_thirty_days, color: 'bg-red-400 text-white' },
  ];

  const hasOverdue = items.some((i) => i.value > 0);

  return (
    <div
      className="rounded-lg border border-gray-200 bg-white p-5"
      data-testid="overdue-aging-widget"
    >
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Overdue Aging</h3>
      {!hasOverdue ? (
        <p className="text-sm text-green-600">No overdue assignments.</p>
      ) : (
        <div className="grid grid-cols-4 gap-3">
          {items.map((item) => (
            <div key={item.label} className={`rounded p-3 text-center ${item.color}`}>
              <p className="text-2xl font-bold" data-testid={`aging-bucket-${item.label.replace(/\s/g, '-')}`}>
                {item.value}
              </p>
              <p className="text-xs mt-1">{item.label}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Completion Trend Widget
// ---------------------------------------------------------------------------

interface CompletionTrendWidgetProps {
  trend: CompletionTrendPoint[] | undefined;
}

export function CompletionTrendWidget({ trend }: CompletionTrendWidgetProps) {
  if (!trend) return <WidgetUnavailable name="Completion trend" />;
  if (trend.length < 2) {
    return (
      <div
        className="rounded-lg border border-gray-200 bg-gray-50 p-6 text-center"
        data-testid="completion-trend-insufficient"
      >
        <p className="text-sm text-gray-500">Insufficient trend data (need ≥ 2 weeks).</p>
      </div>
    );
  }

  const max = Math.max(...trend.map((t) => t.completed_count), 1);

  return (
    <div
      className="rounded-lg border border-gray-200 bg-white p-5"
      data-testid="completion-trend-widget"
    >
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Weekly Completion Trend</h3>
      <div className="flex items-end gap-1 h-24">
        {trend.slice(-12).map((t) => {
          const heightPct = max > 0 ? (t.completed_count / max) * 100 : 0;
          return (
            <div
              key={t.week_start}
              className="flex-1 flex flex-col items-center gap-1"
              title={`${t.week_start}: ${t.completed_count}`}
            >
              <div
                className="w-full bg-blue-400 rounded-t"
                style={{ height: `${heightPct}%`, minHeight: t.completed_count > 0 ? '2px' : '0' }}
                data-testid={`trend-bar-${t.week_start}`}
              />
            </div>
          );
        })}
      </div>
      <p className="text-xs text-gray-400 mt-2">Last {Math.min(trend.length, 12)} weeks — Computed from assignments</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Report Compliance Widget
// ---------------------------------------------------------------------------

interface ReportComplianceWidgetProps {
  compliance: number | undefined;
  withoutRecent: number | undefined;
}

export function ReportComplianceWidget({ compliance, withoutRecent }: ReportComplianceWidgetProps) {
  if (compliance === undefined) return <WidgetUnavailable name="Report compliance" />;

  const color =
    compliance >= 0.8 ? 'text-green-700' : compliance >= 0.6 ? 'text-yellow-700' : 'text-red-700';

  return (
    <div
      className="rounded-lg border border-gray-200 bg-white p-5"
      data-testid="report-compliance-widget"
    >
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Report Submission Compliance</h3>
      <p className={`text-3xl font-bold ${color}`} data-testid="compliance-rate">
        {pct(compliance)}
      </p>
      {withoutRecent !== undefined && (
        <p className="text-sm text-gray-500 mt-2">
          {withoutRecent} assignment{withoutRecent !== 1 ? 's' : ''} without a recent report.
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Unit Performance Table
// ---------------------------------------------------------------------------

interface UnitPerformanceTableProps {
  units: UnitCompletionRow[] | undefined;
}

export function UnitPerformanceTable({ units }: UnitPerformanceTableProps) {
  if (!units) return <WidgetUnavailable name="Unit performance" />;
  if (units.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 text-center" data-testid="unit-table-empty">
        <p className="text-sm text-gray-500">No unit data available.</p>
      </div>
    );
  }

  const sorted = [...units].sort((a, b) => b.completion_rate - a.completion_rate);

  return (
    <div
      className="rounded-lg border border-gray-200 bg-white overflow-hidden"
      data-testid="unit-performance-table"
    >
      <div className="px-5 py-3 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700">Unit Performance</h3>
      </div>
      <table className="min-w-full divide-y divide-gray-100">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Unit</th>
            <th className="px-4 py-2 text-right text-xs font-medium text-gray-600 uppercase">Total</th>
            <th className="px-4 py-2 text-right text-xs font-medium text-gray-600 uppercase">Completed</th>
            <th className="px-4 py-2 text-right text-xs font-medium text-gray-600 uppercase">Overdue</th>
            <th className="px-4 py-2 text-right text-xs font-medium text-gray-600 uppercase">Rate</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {sorted.map((u) => (
            <tr key={u.unit_id} data-testid={`unit-row-${u.unit_id}`}>
              <td className="px-4 py-2 text-sm text-gray-800">{u.unit_name}</td>
              <td className="px-4 py-2 text-sm text-gray-700 text-right">{u.total}</td>
              <td className="px-4 py-2 text-sm text-green-700 text-right">{u.completed}</td>
              <td className="px-4 py-2 text-sm text-red-700 text-right">{u.overdue}</td>
              <td className="px-4 py-2 text-sm font-medium text-right">{pct(u.completion_rate)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Escalation Rate Widget
// ---------------------------------------------------------------------------

interface EscalationRateWidgetProps {
  rate: number | undefined;
  avgRevisionCycles: number | undefined;
}

export function EscalationRateWidget({ rate, avgRevisionCycles }: EscalationRateWidgetProps) {
  if (rate === undefined) return <WidgetUnavailable name="Escalation rate" />;

  return (
    <div
      className="rounded-lg border border-gray-200 bg-white p-5"
      data-testid="escalation-rate-widget"
    >
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Escalation Rate</h3>
      <p className="text-3xl font-bold text-orange-700" data-testid="escalation-rate-value">
        {pct(rate)}
      </p>
      {avgRevisionCycles !== undefined && (
        <p className="text-sm text-gray-500 mt-2">
          Avg revision cycles: {avgRevisionCycles.toFixed(1)}
        </p>
      )}
      <p
        className="mt-2 text-xs text-amber-700"
        data-testid="escalation-manual-label"
      >
        Manual confirmation required for all escalations.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Evidence Attachment Rate Widget
// ---------------------------------------------------------------------------

interface EvidenceAttachmentRateWidgetProps {
  rate: number | undefined;
}

export function EvidenceAttachmentRateWidget({ rate }: EvidenceAttachmentRateWidgetProps) {
  if (rate === undefined) return <WidgetUnavailable name="Evidence attachment rate" />;

  const color =
    rate >= 0.8 ? 'text-green-700' : rate >= 0.5 ? 'text-yellow-700' : 'text-red-700';

  return (
    <div
      className="rounded-lg border border-gray-200 bg-white p-5"
      data-testid="evidence-attachment-widget"
    >
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Evidence Attachment Rate</h3>
      <p className={`text-3xl font-bold ${color}`} data-testid="evidence-attachment-rate">
        {pct(rate)}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Analytics Section — rendered only when dashboard guard passes
// ---------------------------------------------------------------------------

interface DashboardAnalyticsSectionProps {
  dashboard: DashboardSummaryExpanded;
}

export function DashboardAnalyticsSection({ dashboard }: DashboardAnalyticsSectionProps) {
  return (
    <section data-testid="dashboard-analytics-section">
      <h2 className="text-lg font-semibold mb-4 text-gray-800">Analytics</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        <OverdueAgingWidget buckets={dashboard.overdue_aging_buckets} />
        <CompletionTrendWidget trend={dashboard.completion_trend_by_week} />
        <ReportComplianceWidget
          compliance={dashboard.report_submission_compliance}
          withoutRecent={dashboard.assignments_without_recent_report}
        />
        <EscalationRateWidget
          rate={dashboard.escalation_rate}
          avgRevisionCycles={dashboard.average_revision_cycles}
        />
        <EvidenceAttachmentRateWidget rate={dashboard.evidence_attachment_rate} />
        {dashboard.unit_completion_table && (
          <div className="md:col-span-2 xl:col-span-3">
            <UnitPerformanceTable units={dashboard.unit_completion_table} />
          </div>
        )}
      </div>
      <p className="mt-4 text-xs text-gray-400">
        Computed from assignments · Data source: {dashboard.data_source}
      </p>
    </section>
  );
}
