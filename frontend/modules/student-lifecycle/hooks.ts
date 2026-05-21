import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { studentLifecycleApi } from './api';
import {
  StudentLifecycleDataQualityError,
  assertTrustedDegreeProgress,
  assertTrustedStudentLifecycleDashboard,
  assertTrustedStudentLifecycleHealth,
} from './guards';
import type {
  AcademicRecordCreateRequest,
  ApplicantCreateRequest,
  ApplicantStatusUpdateRequest,
  DegreeProgressSnapshotCreateRequest,
  EnrollmentReviewRequest,
  GraduationReadinessReviewRequest,
  InterventionFollowupRequest,
  InterventionPlanCreateRequest,
  StudentAppealCreateRequest,
  StudentAppealReviewRequest,
  StudentEnrollmentCreateRequest,
  StudentLifecycleEvidenceMetadataRequest,
  StudentProfileCreateRequest,
  StudentRequestCreateRequest,
  StudentRequestReviewRequest,
  StudentStatusUpdateRequest,
  TranscriptPreviewCreateRequest,
} from './types';

const CACHE_KEYS = {
  dashboard: ['student-lifecycle:dashboard'] as const,
  health: ['student-lifecycle:health'] as const,
  applicants: ['student-lifecycle:applicants'] as const,
  applicant: (applicantId: string | number) => ['student-lifecycle:applicant', String(applicantId)] as const,
  applicantHistory: (applicantId: string | number) => ['student-lifecycle:applicant-history', String(applicantId)] as const,
  students: ['student-lifecycle:students'] as const,
  student: (studentId: string | number) => ['student-lifecycle:student', String(studentId)] as const,
  studentHistory: (studentId: string | number) => ['student-lifecycle:student-history', String(studentId)] as const,
  enrollments: ['student-lifecycle:enrollment'] as const,
  enrollment: (enrollmentId: string | number) => ['student-lifecycle:enrollment', String(enrollmentId)] as const,
  academicRecords: ['student-lifecycle:academic-records'] as const,
  transcripts: ['student-lifecycle:transcripts'] as const,
  degreeProgress: (studentId: string | number) => ['student-lifecycle:degree-progress', String(studentId)] as const,
  requests: ['student-lifecycle:requests'] as const,
  request: (requestId: string | number) => ['student-lifecycle:request', String(requestId)] as const,
  appeals: ['student-lifecycle:appeals'] as const,
  appeal: (appealId: string | number) => ['student-lifecycle:appeal', String(appealId)] as const,
  interventions: ['student-lifecycle:interventions'] as const,
  intervention: (planId: string | number) => ['student-lifecycle:intervention', String(planId)] as const,
  audit: ['student-lifecycle:audit'] as const,
  evidence: ['student-lifecycle:evidence'] as const,
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
    isUntrusted: query.error instanceof StudentLifecycleDataQualityError,
  };
}

function invalidateLists(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: CACHE_KEYS.dashboard });
  queryClient.invalidateQueries({ queryKey: CACHE_KEYS.health });
  queryClient.invalidateQueries({ queryKey: CACHE_KEYS.applicants });
  queryClient.invalidateQueries({ queryKey: CACHE_KEYS.students });
  queryClient.invalidateQueries({ queryKey: CACHE_KEYS.enrollments });
  queryClient.invalidateQueries({ queryKey: CACHE_KEYS.academicRecords });
  queryClient.invalidateQueries({ queryKey: CACHE_KEYS.transcripts });
  queryClient.invalidateQueries({ queryKey: CACHE_KEYS.requests });
  queryClient.invalidateQueries({ queryKey: CACHE_KEYS.appeals });
  queryClient.invalidateQueries({ queryKey: CACHE_KEYS.interventions });
  queryClient.invalidateQueries({ queryKey: CACHE_KEYS.audit });
  queryClient.invalidateQueries({ queryKey: CACHE_KEYS.evidence });
}

export function useStudentLifecycleDashboard() {
  const query = useQuery({
    queryKey: CACHE_KEYS.dashboard,
    queryFn: async () => {
      const payload = await studentLifecycleApi.getStudentLifecycleDashboard();
      assertTrustedStudentLifecycleDashboard(payload);
      return payload;
    },
    staleTime: 60000,
  });

  return buildTrustedQueryResult(query);
}

export function useStudentLifecycleHealth() {
  const query = useQuery({
    queryKey: CACHE_KEYS.health,
    queryFn: async () => {
      const payload = await studentLifecycleApi.getStudentLifecycleHealth();
      assertTrustedStudentLifecycleHealth(payload);
      return payload;
    },
    staleTime: 60000,
  });

  return buildTrustedQueryResult(query);
}

export function useApplicants() {
  return useQuery({ queryKey: CACHE_KEYS.applicants, queryFn: () => studentLifecycleApi.listApplicants(), staleTime: 30000 });
}

export function useApplicant(applicantId: string | number) {
  return useQuery({
    queryKey: CACHE_KEYS.applicant(applicantId),
    queryFn: () => studentLifecycleApi.getApplicant(applicantId),
    enabled: Boolean(applicantId),
    staleTime: 30000,
  });
}

export function useStudents() {
  return useQuery({ queryKey: CACHE_KEYS.students, queryFn: () => studentLifecycleApi.listStudents(), staleTime: 30000 });
}

export function useStudentProfile(studentId: string | number) {
  return useQuery({
    queryKey: CACHE_KEYS.student(studentId),
    queryFn: () => studentLifecycleApi.getStudentProfile(studentId),
    enabled: Boolean(studentId),
    staleTime: 30000,
  });
}

export function useEnrollments() {
  return useQuery({ queryKey: CACHE_KEYS.enrollments, queryFn: () => studentLifecycleApi.listEnrollments(), staleTime: 30000 });
}

export function useAcademicRecords() {
  return useQuery({ queryKey: CACHE_KEYS.academicRecords, queryFn: () => studentLifecycleApi.listAcademicRecords(), staleTime: 30000 });
}

export function useTranscriptPreviews() {
  return useQuery({ queryKey: CACHE_KEYS.transcripts, queryFn: () => studentLifecycleApi.listTranscriptPreviews(), staleTime: 30000 });
}

export function useDegreeProgress(studentId: string | number) {
  const query = useQuery({
    queryKey: CACHE_KEYS.degreeProgress(studentId),
    queryFn: async () => {
      const payload = await studentLifecycleApi.getDegreeProgress(studentId);
      assertTrustedDegreeProgress(payload);
      return payload;
    },
    enabled: Boolean(studentId),
    staleTime: 30000,
  });

  return buildTrustedQueryResult(query);
}

export function useStudentRequests() {
  return useQuery({ queryKey: CACHE_KEYS.requests, queryFn: () => studentLifecycleApi.listStudentRequests(), staleTime: 30000 });
}

export function useStudentAppeals() {
  return useQuery({ queryKey: CACHE_KEYS.appeals, queryFn: () => studentLifecycleApi.listStudentAppeals(), staleTime: 30000 });
}

export function useInterventionPlans() {
  return useQuery({ queryKey: CACHE_KEYS.interventions, queryFn: () => studentLifecycleApi.listInterventionPlans(), staleTime: 30000 });
}

export function useStudentLifecycleAudit() {
  return useQuery({ queryKey: CACHE_KEYS.audit, queryFn: () => studentLifecycleApi.listStudentLifecycleAuditEvents(), staleTime: 30000 });
}

export function useStudentLifecycleEvidence() {
  return useQuery({ queryKey: CACHE_KEYS.evidence, queryFn: () => studentLifecycleApi.listStudentLifecycleEvidence(), staleTime: 30000 });
}

export function useCreateApplicant() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: (payload: ApplicantCreateRequest) => studentLifecycleApi.createApplicant(payload), onSuccess: () => invalidateLists(queryClient) });
}

export function useSubmitApplicant() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: (applicantId: string | number) => studentLifecycleApi.submitApplicant(applicantId), onSuccess: () => invalidateLists(queryClient) });
}

export function useUpdateApplicantStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ applicantId, payload }: { applicantId: string | number; payload: ApplicantStatusUpdateRequest }) =>
      studentLifecycleApi.updateApplicantStatus(applicantId, payload),
    onSuccess: () => invalidateLists(queryClient),
  });
}

export function useCreateStudentProfile() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: (payload: StudentProfileCreateRequest) => studentLifecycleApi.createStudentProfile(payload), onSuccess: () => invalidateLists(queryClient) });
}

export function useUpdateStudentStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ studentId, payload }: { studentId: string | number; payload: StudentStatusUpdateRequest }) =>
      studentLifecycleApi.updateStudentStatus(studentId, payload),
    onSuccess: () => invalidateLists(queryClient),
  });
}

export function useCreateEnrollment() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: (payload: StudentEnrollmentCreateRequest) => studentLifecycleApi.createEnrollment(payload), onSuccess: () => invalidateLists(queryClient) });
}

export function useReviewEnrollment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ enrollmentId, payload }: { enrollmentId: string | number; payload: EnrollmentReviewRequest }) =>
      studentLifecycleApi.reviewEnrollment(enrollmentId, payload),
    onSuccess: () => invalidateLists(queryClient),
  });
}

export function useCreateAcademicRecord() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: (payload: AcademicRecordCreateRequest) => studentLifecycleApi.createAcademicRecord(payload), onSuccess: () => invalidateLists(queryClient) });
}

export function useCreateTranscriptPreview() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: (payload: TranscriptPreviewCreateRequest) => studentLifecycleApi.createTranscriptPreview(payload), onSuccess: () => invalidateLists(queryClient) });
}

export function useCreateDegreeProgressSnapshot() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ studentId, payload }: { studentId: string | number; payload: DegreeProgressSnapshotCreateRequest }) =>
      studentLifecycleApi.createDegreeProgressSnapshot(studentId, payload),
    onSuccess: () => invalidateLists(queryClient),
  });
}

export function useReviewGraduationReadiness() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ studentId, payload }: { studentId: string | number; payload: GraduationReadinessReviewRequest }) =>
      studentLifecycleApi.reviewGraduationReadiness(studentId, payload),
    onSuccess: () => invalidateLists(queryClient),
  });
}

export function useCreateStudentRequest() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: (payload: StudentRequestCreateRequest) => studentLifecycleApi.createStudentRequest(payload), onSuccess: () => invalidateLists(queryClient) });
}

export function useReviewStudentRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ requestId, payload }: { requestId: string | number; payload: StudentRequestReviewRequest }) =>
      studentLifecycleApi.reviewStudentRequest(requestId, payload),
    onSuccess: () => invalidateLists(queryClient),
  });
}

export function useCreateStudentAppeal() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: (payload: StudentAppealCreateRequest) => studentLifecycleApi.createStudentAppeal(payload), onSuccess: () => invalidateLists(queryClient) });
}

export function useReviewStudentAppeal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ appealId, payload }: { appealId: string | number; payload: StudentAppealReviewRequest }) =>
      studentLifecycleApi.reviewStudentAppeal(appealId, payload),
    onSuccess: () => invalidateLists(queryClient),
  });
}

export function useCreateInterventionPlan() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: (payload: InterventionPlanCreateRequest) => studentLifecycleApi.createInterventionPlan(payload), onSuccess: () => invalidateLists(queryClient) });
}

export function useRecordInterventionFollowup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ planId, payload }: { planId: string | number; payload: InterventionFollowupRequest }) =>
      studentLifecycleApi.recordInterventionFollowup(planId, payload),
    onSuccess: () => invalidateLists(queryClient),
  });
}

export function useAttachEvidenceMetadata() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: StudentLifecycleEvidenceMetadataRequest) => studentLifecycleApi.attachStudentLifecycleEvidenceMetadata(payload),
    onSuccess: () => invalidateLists(queryClient),
  });
}