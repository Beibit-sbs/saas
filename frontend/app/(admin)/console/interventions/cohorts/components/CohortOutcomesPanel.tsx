import type { ReactNode } from 'react';

import type { CohortOutcomeReadSchema } from '@/shared/hooks/useCohortOutcomes';

export type OutcomePanelStatus =
  | 'no_analysis_yet'
  | 'analysis_queued'
  | 'analyzing'
  | 'analyzed'
  | 'analysis_failed';

interface CohortOutcomesPanelProps {
  isLoading: boolean;
  error?: unknown;
  outcomes: CohortOutcomeReadSchema[];
  status: OutcomePanelStatus;
  onRefresh: () => void;
  onRerun: () => void;
  onRetry: () => void;
  actionPending?: boolean;
  cohortSize?: number;
}

interface SummaryMetrics {
  improved: number;
  unchanged: number;
  worse: number;
  confidence: 'High' | 'Medium' | 'Low';
}

function getSummaryMetrics(outcomes: CohortOutcomeReadSchema[]): SummaryMetrics {
  if (outcomes.length === 0) {
    return { improved: 0, unchanged: 0, worse: 0, confidence: 'Low' };
  }

  const improvedCount = outcomes.filter((item) => Number(item.uplift_pp) > 0).length;
  const worseCount = outcomes.filter((item) => Number(item.uplift_pp) < 0).length;
  const unchangedCount = outcomes.length - improvedCount - worseCount;

  const confidenceValues = outcomes
    .map((item) => item.measurement_completeness_pct)
    .filter((value): value is number => value != null);
  const averageCompleteness =
    confidenceValues.length > 0
      ? confidenceValues.reduce((sum, value) => sum + value, 0) / confidenceValues.length
      : 0;

  let confidence: SummaryMetrics['confidence'] = 'Low';
  if (averageCompleteness >= 0.8) {
    confidence = 'High';
  } else if (averageCompleteness >= 0.6) {
    confidence = 'Medium';
  }

  return {
    improved: Math.round((improvedCount / outcomes.length) * 100),
    unchanged: Math.round((unchangedCount / outcomes.length) * 100),
    worse: Math.round((worseCount / outcomes.length) * 100),
    confidence,
  };
}

function getInterpretation(metrics: SummaryMetrics): { verdict: string; meaning: string; recommendation: string } {
  if (metrics.improved >= 40 && metrics.worse <= 25) {
    return {
      verdict: 'Intervention shows positive effect',
      meaning: 'Positive outcome across the cohort.',
      recommendation: 'Recommend reviewing similar cohorts for scale-up.',
    };
  }

  if (metrics.improved > metrics.worse) {
    return {
      verdict: 'Mixed outcome detected',
      meaning: 'There is improvement, but part of the cohort regressed.',
      recommendation: 'Scale carefully and inspect segments with worse outcomes.',
    };
  }

  return {
    verdict: 'No meaningful improvement detected',
    meaning: 'Current intervention impact is not consistently positive.',
    recommendation: 'Re-run analysis after adjustments before wider rollout.',
  };
}

export function CohortOutcomesPanel({
  isLoading,
  error,
  outcomes,
  status,
  onRefresh,
  onRerun,
  onRetry,
  actionPending = false,
  cohortSize,
}: CohortOutcomesPanelProps) {
  const summary = getSummaryMetrics(outcomes);
  const interpretation = getInterpretation(summary);
  const analyzedAt = outcomes
    .map((item) => item.measured_at)
    .sort((a, b) => new Date(b).getTime() - new Date(a).getTime())[0];
  const notes = outcomes.map((item) => item.notes).filter((note): note is string => Boolean(note));

  const statusBadgeClass = {
    no_analysis_yet: 'bg-gray-100 text-gray-700',
    analysis_queued: 'bg-orange-100 text-orange-800',
    analyzing: 'bg-orange-100 text-orange-800',
    analyzed: 'bg-green-100 text-green-800',
    analysis_failed: 'bg-red-100 text-red-800',
  }[status];

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-bold text-gray-900">Outcomes</h2>
        <span className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium ${statusBadgeClass}`}>
          {status.replaceAll('_', ' ')}
        </span>
      </div>

      {isLoading && (
        <div className="space-y-3" data-testid="outcomes-loading">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-200" />
          ))}
        </div>
      )}

      {!isLoading && (status === 'analysis_queued' || status === 'analyzing') && (
        <div className="rounded-md border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">
          <p className="font-medium">Analysis started</p>
          <p>Processing cohort outcomes. Results will appear when processing completes.</p>
        </div>
      )}

      {!isLoading && (status === 'analysis_failed' || error) ? (
        <div className="space-y-3 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          <p className="font-medium">Failed to load analysis results</p>
          <p>{error instanceof Error ? error.message : 'Analysis failed. Please retry.'}</p>
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700"
            aria-label="Retry cohort outcomes analysis"
          >
            Retry
          </button>
        </div>
      ) : null}

      {!isLoading && status === 'no_analysis_yet' && outcomes.length === 0 && (
        <div className="space-y-3 rounded-md border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700">
          <p>No outcomes available yet.</p>
          <button
            type="button"
            onClick={onRerun}
            disabled={actionPending}
            className="inline-flex items-center rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-60"
            aria-label="Run outcomes analysis for this cohort"
          >
            {actionPending ? 'Starting...' : 'Run Analysis'}
          </button>
        </div>
      )}

      {!isLoading && status === 'analyzed' && outcomes.length > 0 && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-md bg-green-50 p-3">
              <p className="text-xs text-green-700">Improved</p>
              <p className="text-xl font-semibold text-green-900">{summary.improved}%</p>
            </div>
            <div className="rounded-md bg-gray-100 p-3">
              <p className="text-xs text-gray-700">Unchanged</p>
              <p className="text-xl font-semibold text-gray-900">{summary.unchanged}%</p>
            </div>
            <div className="rounded-md bg-red-50 p-3">
              <p className="text-xs text-red-700">Worse</p>
              <p className="text-xl font-semibold text-red-900">{summary.worse}%</p>
            </div>
            <div className="rounded-md bg-blue-50 p-3">
              <p className="text-xs text-blue-700">Confidence</p>
              <p className="text-xl font-semibold text-blue-900">{summary.confidence}</p>
            </div>
          </div>

          <div className="rounded-md border border-blue-200 bg-blue-50 px-4 py-3">
            <p className="font-medium text-blue-900">{interpretation.verdict}</p>
            <p className="text-sm text-blue-800">{interpretation.meaning}</p>
            <p className="mt-1 text-sm text-blue-800">{interpretation.recommendation}</p>
          </div>

          <div className="space-y-2 rounded-md border border-gray-200 p-4" data-testid="outcome-distribution-chart">
            <p className="text-sm font-medium text-gray-900">Outcome distribution</p>
            {[
              { label: 'Improved', value: summary.improved, className: 'bg-green-500' },
              { label: 'Unchanged', value: summary.unchanged, className: 'bg-gray-500' },
              { label: 'Worse', value: summary.worse, className: 'bg-red-500' },
            ].map((item) => (
              <div key={item.label} className="space-y-1">
                <div className="flex items-center justify-between text-xs text-gray-700">
                  <span>{item.label}</span>
                  <span>{item.value}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded bg-gray-100" role="progressbar" aria-valuenow={item.value} aria-valuemin={0} aria-valuemax={100} aria-label={`${item.label}: ${item.value}%`}>
                  <div className={`h-full ${item.className}`} style={{ width: `${item.value}%` }} />
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-md border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700">
            <p>Cohort size: {cohortSize ?? 'n/a'}</p>
            <p>Analyzed at: {analyzedAt ? new Date(analyzedAt).toLocaleString() : 'n/a'}</p>
            <p>Sample size: {outcomes.length}</p>
            <p>Model/version: n/a</p>
            <p>Notes/warnings: {notes[0] ?? 'No warnings'}</p>
            <p className="mt-2 text-xs text-gray-500">Confidence is based on available cohort outcome data.</p>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={onRefresh}
              className="inline-flex items-center rounded-md bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-800 hover:bg-gray-200"
              aria-label="Refresh cohort outcomes results"
            >
              Refresh results
            </button>
            <button
              type="button"
              onClick={onRerun}
              disabled={actionPending}
              className="inline-flex items-center rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-60"
              aria-label="Re-run outcomes analysis for this cohort"
            >
              {actionPending ? 'Starting...' : 'Re-run analysis'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}