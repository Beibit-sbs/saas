import { useQuery } from '@tanstack/react-query';
import { academicOperationsApi } from './api';
import {
  AcademicOperationsDataQualityError,
  assertTrustedAcademicOperationsDashboard,
  assertTrustedAcademicOperationsHealth,
  assertTrustedAcademicOperationsMatrixSummary,
} from './guards';

const CACHE_KEYS = {
  health: ['academic-operations:health'] as const,
  dashboard: ['academic-operations:dashboard'] as const,
  matrixSummary: ['academic-operations:matrix-summary'] as const,
  canonicalReuseSummary: ['academic-operations:canonical-reuse-summary'] as const,
  academicGroups: ['academic-operations:academic-groups'] as const,
  cohorts: ['academic-operations:cohorts'] as const,
  courseRegistration: ['academic-operations:course-registration'] as const,
  gradebookMetadata: ['academic-operations:gradebook-metadata'] as const,
  retakes: ['academic-operations:retakes'] as const,
  summerSemesters: ['academic-operations:summer-semesters'] as const,
  advisorTutor: ['academic-operations:advisor-tutor'] as const,
  bridges: ['academic-operations:bridges'] as const,
  bridgeStudentLifecycle: ['academic-operations:bridges-student-lifecycle'] as const,
  bridgeDocumentWorkflow: ['academic-operations:bridges-document-workflow'] as const,
  bridgeExecutiveGovernance: ['academic-operations:bridges-executive-governance'] as const,
  bridgeQualityAccreditation: ['academic-operations:bridges-quality-accreditation'] as const,
  audit: ['academic-operations:audit'] as const,
  evidence: ['academic-operations:evidence'] as const,
};

function buildTrustedQueryResult<T>(query: {
  data: T | undefined;
  error: unknown;
  isPending: boolean;
  isLoading: boolean;
}) {
  return {
    ...query,
    isTrusted: Boolean(query.data),
    isUntrusted: query.error instanceof AcademicOperationsDataQualityError,
  };
}

export function useAcademicOperationsHealth() {
  const query = useQuery({
    queryKey: CACHE_KEYS.health,
    queryFn: async () => {
      const payload = await academicOperationsApi.getAcademicOperationsHealth();
      assertTrustedAcademicOperationsHealth(payload);
      return payload;
    },
    staleTime: 60000,
  });
  return buildTrustedQueryResult(query);
}

export function useAcademicOperationsDashboard() {
  const query = useQuery({
    queryKey: CACHE_KEYS.dashboard,
    queryFn: async () => {
      const payload = await academicOperationsApi.getAcademicOperationsDashboard();
      assertTrustedAcademicOperationsDashboard(payload);
      return payload;
    },
    staleTime: 60000,
  });
  return buildTrustedQueryResult(query);
}

export function useAcademicOperationsMatrixSummary() {
  const query = useQuery({
    queryKey: CACHE_KEYS.matrixSummary,
    queryFn: async () => {
      const payload = await academicOperationsApi.getAcademicOperationsMatrixSummary();
      assertTrustedAcademicOperationsMatrixSummary(payload);
      return payload;
    },
    staleTime: 60000,
  });
  return buildTrustedQueryResult(query);
}

export function useAcademicOperationsCanonicalReuseSummary() {
  return useQuery({
    queryKey: CACHE_KEYS.canonicalReuseSummary,
    queryFn: () => academicOperationsApi.getAcademicOperationsCanonicalReuseSummary(),
    staleTime: 60000,
  });
}

export function useAcademicGroups() {
  return useQuery({ queryKey: CACHE_KEYS.academicGroups, queryFn: async () => (await academicOperationsApi.listAcademicGroups()).items, staleTime: 30000 });
}

export function useCohorts() {
  return useQuery({ queryKey: CACHE_KEYS.cohorts, queryFn: async () => (await academicOperationsApi.listCohorts()).items, staleTime: 30000 });
}

export function useCourseRegistrationMetadata() {
  return useQuery({ queryKey: CACHE_KEYS.courseRegistration, queryFn: async () => (await academicOperationsApi.listCourseRegistrationMetadata()).items, staleTime: 30000 });
}

export function useGradebookMetadata() {
  return useQuery({ queryKey: CACHE_KEYS.gradebookMetadata, queryFn: async () => (await academicOperationsApi.listGradebookMetadata()).items, staleTime: 30000 });
}

export function useRetakePlans() {
  return useQuery({ queryKey: CACHE_KEYS.retakes, queryFn: async () => (await academicOperationsApi.listRetakePlans()).items, staleTime: 30000 });
}

export function useSummerSemesterTerms() {
  return useQuery({ queryKey: CACHE_KEYS.summerSemesters, queryFn: async () => (await academicOperationsApi.listSummerSemesterTerms()).items, staleTime: 30000 });
}

export function useAdvisorTutorAssignments() {
  return useQuery({ queryKey: CACHE_KEYS.advisorTutor, queryFn: async () => (await academicOperationsApi.listAdvisorTutorAssignments()).items, staleTime: 30000 });
}

export function useBridges() {
  return useQuery({ queryKey: CACHE_KEYS.bridges, queryFn: async () => (await academicOperationsApi.listBridges()).items, staleTime: 30000 });
}

export function useStudentLifecycleBridgeSummary() {
  return useQuery({ queryKey: CACHE_KEYS.bridgeStudentLifecycle, queryFn: () => academicOperationsApi.getStudentLifecycleBridgeSummary(), staleTime: 30000 });
}

export function useDocumentWorkflowBridgeSummary() {
  return useQuery({ queryKey: CACHE_KEYS.bridgeDocumentWorkflow, queryFn: () => academicOperationsApi.getDocumentWorkflowBridgeSummary(), staleTime: 30000 });
}

export function useExecutiveGovernanceBridgeSummary() {
  return useQuery({ queryKey: CACHE_KEYS.bridgeExecutiveGovernance, queryFn: () => academicOperationsApi.getExecutiveGovernanceBridgeSummary(), staleTime: 30000 });
}

export function useQualityAccreditationBridgeSummary() {
  return useQuery({ queryKey: CACHE_KEYS.bridgeQualityAccreditation, queryFn: () => academicOperationsApi.getQualityAccreditationBridgeSummary(), staleTime: 30000 });
}

export function useAcademicOperationsAudit() {
  return useQuery({ queryKey: CACHE_KEYS.audit, queryFn: () => academicOperationsApi.listAuditEvents(), staleTime: 30000 });
}

export function useAcademicOperationsEvidence() {
  return useQuery({ queryKey: CACHE_KEYS.evidence, queryFn: async () => (await academicOperationsApi.listEvidence()).items, staleTime: 30000 });
}