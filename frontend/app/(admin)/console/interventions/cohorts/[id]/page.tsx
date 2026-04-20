'use client';

import { Suspense } from 'react';
import { useMemo } from 'react';
import { useState } from 'react';
import Link from 'next/link';
import { useAdminAuth } from '@/shared/auth/context';
import { useCohortDetail, useFinalizeExistingCohortMutation } from '@/shared/hooks/useInterventionCohorts';
import { parseAnalysisStatus, useCohortAnalysisMutation } from '@/shared/hooks/useCohortAnalysis';
import { useCohortOutcomesQuery } from '@/shared/hooks/useCohortOutcomes';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';
import { CohortDetailsCard } from '../components/CohortDetailsCard';
import { CohortOutcomesPanel } from '../components/CohortOutcomesPanel';

/**
 * Intervention Cohort Detail Page
 *
 * Displays a single cohort with:
 * - Cohort metadata (name, size, date range)
 * - Analysis outcomes with visualization
 * - Actions (edit, analyze, delete)
 *
 * @route /console/interventions/cohorts/[id]
 */
export default function CohortDetailPage({ params }: { params: { id: string } }) {
  const cohortId = parseInt(params.id, 10);
  const { user, isLoading } = useAdminAuth();

  if (isLoading) {
    return <LoadingState title="Loading cohort" message="Resolving your tenant context." />;
  }

  if (!Number.isFinite(cohortId) || cohortId <= 0) {
    return (
      <div className="p-6">
        <ErrorState title="Invalid cohort" message="The cohort identifier in the URL is not valid." />
      </div>
    );
  }

  if (user?.tenantId === undefined) {
    return (
      <div className="p-6">
        <ErrorState
          title="Tenant context unavailable"
          message="This page requires a tenant-scoped admin session before cohort details can be loaded."
        />
      </div>
    );
  }

  return (
    <Suspense fallback={<LoadingState />}>
      <CohortDetailContent cohortId={cohortId} tenantId={user.tenantId} />
    </Suspense>
  );
}

function CohortDetailContent({ cohortId, tenantId }: { cohortId: number; tenantId: number }) {
  const { data: cohort, isLoading, error } = useCohortDetail(cohortId, tenantId);
  const analyzeMutation = useCohortAnalysisMutation(cohortId, tenantId);
  const finalizeMutation = useFinalizeExistingCohortMutation(cohortId, tenantId);
  const [analysisState, setAnalysisState] = useState<'idle' | 'queued' | 'analyzing' | 'failed'>('idle');
  const [analysisNotice, setAnalysisNotice] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const {
    data: outcomesResponse,
    isLoading: outcomesLoading,
    refetch: refetchOutcomes,
    error: outcomesError,
  } = useCohortOutcomesQuery(cohortId, tenantId);

  const panelStatus = useMemo(() => {
    if (analysisState === 'failed' || analysisError || outcomesError) {
      return 'analysis_failed' as const;
    }
    if (analysisState === 'queued') {
      return 'analysis_queued' as const;
    }
    if (analysisState === 'analyzing' || analyzeMutation.isPending) {
      return 'analyzing' as const;
    }
    if ((outcomesResponse?.items?.length ?? 0) > 0) {
      return 'analyzed' as const;
    }
    return 'no_analysis_yet' as const;
  }, [analysisState, analysisError, outcomesError, analyzeMutation.isPending, outcomesResponse?.items?.length]);

  const handleFinalize = () => {
    setAnalysisError(null);
    setAnalysisNotice(null);

    finalizeMutation.mutate(undefined, {
      onSuccess: () => {
        setAnalysisNotice('Cohort finalized successfully. Analysis is now available.');
      },
      onError: (mutationError) => {
        setAnalysisError(
          mutationError instanceof Error ? mutationError.message : 'Failed to finalize cohort.',
        );
      },
    });
  };

  const handleRunAnalysis = () => {
    if (!cohort || cohort.status === 'draft') {
      setAnalysisError('Finalize cohort before running analysis.');
      return;
    }

    setAnalysisState('analyzing');
    setAnalysisError(null);
    setAnalysisNotice(null);

    analyzeMutation.mutate(
      { segment_keys: [] },
      {
        onSuccess: (response) => {
          const parsed = parseAnalysisStatus(response);
          setAnalysisNotice(parsed.message);
          if (parsed.status === 'analysis_queued' || parsed.status === 'in_progress') {
            setAnalysisState('queued');
            return;
          }
          setAnalysisState('idle');
          void refetchOutcomes();
        },
        onError: (mutationError) => {
          setAnalysisState('failed');
          setAnalysisError(
            mutationError instanceof Error ? mutationError.message : 'Failed to start analysis.',
          );
        },
      },
    );
  };

  if (isLoading) {
    return <LoadingState />;
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorState error={error} />
      </div>
    );
  }

  if (!cohort) {
    return (
      <div className="p-6 rounded-md bg-gray-50">
        <p className="text-gray-600">Cohort not found</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header with back button */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Link href="/console/interventions/cohorts" className="text-blue-600 hover:text-blue-700">
              ← Back to cohorts
            </Link>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">{cohort.cohort_name}</h1>
        </div>
        <div className="flex gap-2">
          <Link
            href={`/console/interventions/cohorts/${cohortId}/edit`}
            aria-disabled={cohort.status !== 'draft'}
            className={`inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              cohort.status === 'draft'
                ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                : 'cursor-not-allowed bg-gray-100 text-gray-400 pointer-events-none'
            }`}
          >
            Edit
          </Link>
          <button
            type="button"
            onClick={handleFinalize}
            disabled={cohort.status !== 'draft' || finalizeMutation.isPending}
            className="inline-flex items-center justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors disabled:cursor-not-allowed disabled:opacity-70"
          >
            {finalizeMutation.isPending ? 'Finalizing...' : 'Finalize Cohort'}
          </button>
          <button
            type="button"
            onClick={handleRunAnalysis}
            disabled={analyzeMutation.isPending || cohort.status === 'draft'}
            className="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors disabled:cursor-not-allowed disabled:opacity-70"
          >
            {analyzeMutation.isPending ? 'Starting Analysis...' : 'Run Analysis'}
          </button>
        </div>
      </div>

      {analysisNotice && (
        <div className="rounded-md border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">
          {analysisNotice}
        </div>
      )}

      {analysisError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {analysisError}
        </div>
      )}

      <CohortDetailsCard cohort={cohort} />

      <CohortOutcomesPanel
        isLoading={outcomesLoading}
        error={outcomesError}
        status={panelStatus}
        outcomes={outcomesResponse?.items ?? []}
        onRefresh={() => {
          void refetchOutcomes();
        }}
        onRerun={handleRunAnalysis}
        onRetry={() => {
          setAnalysisState('idle');
          setAnalysisError(null);
          void refetchOutcomes();
        }}
        actionPending={analyzeMutation.isPending}
        cohortSize={cohort.student_count}
      />
    </div>
  );
}
