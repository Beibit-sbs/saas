/**
 * Exam Governance Hooks
 * React Query hooks for exam lifecycle, scheduling, and proctoring management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  apiGet,
  apiPost,
  apiPut,
  apiDelete,
} from '@/shared/api/client';
import type {
  ExamDashboardSummary,
  ExamListItem,
  ExamMetadata,
  ExamSchedule,
  ExamSession,
  StudentExamRegistration,
  ProctorAssignment,
  ExamAccessibility,
  ExamStatistics,
  ExamCreatePayload,
  ExamUpdatePayload,
  ExamSessionCreatePayload,
} from './types';

const CACHE_KEYS = {
  DASHBOARD: ['exams:dashboard'],
  ALL_EXAMS: ['exams:all'],
  EXAM_DETAIL: (id: string) => ['exams:detail', id],
  EXAM_SESSIONS: (id: string) => ['exams:sessions', id],
  EXAM_REGISTRATIONS: (sessionId: string) => ['exams:registrations', sessionId],
  EXAM_STATISTICS: (id: string) => ['exams:statistics', id],
  PROCTOR_ASSIGNMENTS: (examId: string) => ['exams:proctors', examId],
  ACCOMMODATIONS: (examId: string) => ['exams:accommodations', examId],
  BY_TERM: (term: string) => ['exams:term', term],
  BY_FACULTY: (faculty: string) => ['exams:faculty', faculty],
};

/**
 * Fetch exam governance dashboard summary
 */
export function useExamDashboardSummary() {
  return useQuery({
    queryKey: CACHE_KEYS.DASHBOARD,
    queryFn: () =>
      apiGet<ExamDashboardSummary>(`/api/exams/dashboard/summary`),
    staleTime: 60000,
  });
}

/**
 * Fetch list of all exams
 */
export function useExamsList(filters?: { status?: string; term_id?: string }) {
  return useQuery({
    queryKey: [CACHE_KEYS.ALL_EXAMS, filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.term_id) params.append('term_id', filters.term_id);
      
      return apiGet<ExamListItem[]>(
        `/api/exams?${params.toString()}`
      );
    },
    staleTime: 60000,
  });
}

/**
 * Fetch detailed exam information with schedule and sessions
 */
export function useExamDetail(examId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.EXAM_DETAIL(examId),
    queryFn: () =>
      apiGet<{
        metadata: ExamMetadata;
        schedule: ExamSchedule;
      }>(`/api/exams/${examId}`),
    enabled: !!examId,
    staleTime: 30000,
  });
}

/**
 * Fetch all sessions for an exam
 */
export function useExamSessions(examId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.EXAM_SESSIONS(examId),
    queryFn: () =>
      apiGet<ExamSession[]>(`/api/exams/${examId}/sessions`),
    enabled: !!examId,
    staleTime: 30000,
  });
}

/**
 * Fetch student registrations for an exam session
 */
export function useStudentRegistrations(sessionId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.EXAM_REGISTRATIONS(sessionId),
    queryFn: () =>
      apiGet<StudentExamRegistration[]>(
        `/api/exams/sessions/${sessionId}/registrations`
      ),
    enabled: !!sessionId,
    staleTime: 30000,
  });
}

/**
 * Fetch exam statistics and analytics
 */
export function useExamStatistics(examId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.EXAM_STATISTICS(examId),
    queryFn: () =>
      apiGet<ExamStatistics>(`/api/exams/${examId}/statistics`),
    enabled: !!examId,
    staleTime: 60000,
  });
}

/**
 * Fetch proctor assignments for an exam
 */
export function useProctorAssignments(examId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.PROCTOR_ASSIGNMENTS(examId),
    queryFn: () =>
      apiGet<ProctorAssignment[]>(`/api/exams/${examId}/proctors`),
    enabled: !!examId,
    staleTime: 30000,
  });
}

/**
 * Fetch accessibility accommodations for an exam
 */
export function useExamAccommodations(examId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.ACCOMMODATIONS(examId),
    queryFn: () =>
      apiGet<ExamAccessibility[]>(`/api/exams/${examId}/accommodations`),
    enabled: !!examId,
    staleTime: 30000,
  });
}

/**
 * Fetch exams by term
 */
export function useExamsByTerm(termId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.BY_TERM(termId),
    queryFn: () =>
      apiGet<ExamListItem[]>(`/api/exams/term/${termId}`),
    enabled: !!termId,
    staleTime: 60000,
  });
}

/**
 * Fetch exams by faculty member
 */
export function useExamsByFaculty(facultyId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.BY_FACULTY(facultyId),
    queryFn: () =>
      apiGet<ExamListItem[]>(`/api/exams/faculty/${facultyId}`),
    enabled: !!facultyId,
    staleTime: 60000,
  });
}

/**
 * Create a new exam
 */
export function useCreateExam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ExamCreatePayload) =>
      apiPost<ExamMetadata>('/api/exams', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_EXAMS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

/**
 * Update exam information
 */
export function useUpdateExam(examId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ExamUpdatePayload) =>
      apiPut<ExamMetadata>(`/api/exams/${examId}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.EXAM_DETAIL(examId),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_EXAMS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

/**
 * Create exam session
 */
export function useCreateExamSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ExamSessionCreatePayload) =>
      apiPost<ExamSession>('/api/exams/sessions', payload),
    onSuccess: (_, payload) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.EXAM_SESSIONS(payload.exam_id),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

/**
 * Register student for exam session
 */
export function useRegisterStudent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sessionId,
      studentId,
    }: {
      sessionId: string;
      studentId: string;
    }) =>
      apiPost<StudentExamRegistration>(
        `/api/exams/sessions/${sessionId}/register`,
        { student_id: studentId }
      ),
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.EXAM_REGISTRATIONS(sessionId),
      });
    },
  });
}

/**
 * Check in student for exam session
 */
export function useCheckInStudent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      registrationId,
      sessionId,
    }: {
      registrationId: string;
      sessionId: string;
    }) =>
      apiPost<StudentExamRegistration>(
        `/api/exams/registrations/${registrationId}/check-in`,
        {}
      ),
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.EXAM_REGISTRATIONS(sessionId),
      });
    },
  });
}

/**
 * Assign proctor to exam session
 */
export function useAssignProctor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      examId,
      proctorId,
      roomId,
    }: {
      examId: string;
      proctorId: string;
      roomId?: string;
    }) =>
      apiPost<ProctorAssignment>(
        `/api/exams/${examId}/assign-proctor`,
        { proctor_id: proctorId, room_id: roomId }
      ),
    onSuccess: (_, { examId }) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.PROCTOR_ASSIGNMENTS(examId),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

/**
 * Create accessibility accommodation
 */
export function useCreateAccommodation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: Omit<ExamAccessibility, 'accommodation_id' | 'created_at'>) =>
      apiPost<ExamAccessibility>(
        '/api/exams/accommodations',
        payload
      ),
    onSuccess: (_, payload) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.ACCOMMODATIONS(payload.exam_id),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

/**
 * Cancel exam
 */
export function useCancelExam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (examId: string) =>
      apiDelete<void>(`/api/exams/${examId}/cancel`),
    onSuccess: (_, examId) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.EXAM_DETAIL(examId),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_EXAMS });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}
