/**
 * Syllabus Governance Hooks
 * React Query hooks for syllabus lifecycle and approval workflow management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  apiGet,
  apiPost,
  apiPut,
  apiDelete,
} from '@/shared/api/client';
import type {
  SyllabusMetadata,
  SyllabusContent,
  ApprovalWorkflow,
  SyllabusDashboardSummary,
  SyllabusListItem,
  SyllabusCreatePayload,
  SyllabusUpdatePayload,
} from './types';

const CACHE_KEYS = {
  ALL_SYLLABI: ['syllabi:all'],
  SYLLABUS_DETAIL: (id: string) => ['syllabi:detail', id],
  SYLLABUS_APPROVAL: (id: string) => ['syllabi:approval', id],
  DASHBOARD: ['syllabi:dashboard'],
  BY_DEPARTMENT: (dept: string) => ['syllabi:department', dept],
  BY_FACULTY: (faculty: string) => ['syllabi:faculty', faculty],
};

/**
 * Fetch list of all syllabi for current tenant
 */
export function useSyllabusList(filters?: { status?: string; department_id?: string }) {
  return useQuery({
    queryKey: [CACHE_KEYS.ALL_SYLLABI, filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.department_id) params.append('department_id', filters.department_id);
      
      return apiGet<SyllabusListItem[]>(
        `/api/admin/syllabus-governance?${params.toString()}`
      );
    },
    staleTime: 60000,
  });
}

/**
 * Fetch detailed syllabus information including content and metadata
 */
export function useSyllabusDetail(syllabusId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.SYLLABUS_DETAIL(syllabusId),
    queryFn: () =>
      apiGet<{
        metadata: SyllabusMetadata;
        content: SyllabusContent;
      }>(`/api/admin/syllabus-governance/${syllabusId}`),
    enabled: !!syllabusId,
    staleTime: 30000,
  });
}

/**
 * Fetch approval workflow for a syllabus
 */
export function useApprovalWorkflow(syllabusId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.SYLLABUS_APPROVAL(syllabusId),
    queryFn: () =>
      apiGet<ApprovalWorkflow>(`/api/admin/syllabus-governance/${syllabusId}/approval-workflow`),
    enabled: !!syllabusId,
    staleTime: 30000,
  });
}

/**
 * Fetch syllabus governance dashboard summary
 */
export function useSyllabusDashboardSummary() {
  return useQuery({
    queryKey: CACHE_KEYS.DASHBOARD,
    queryFn: () =>
      apiGet<SyllabusDashboardSummary>(`/api/admin/syllabus-governance/dashboard/summary`),
    staleTime: 60000,
  });
}

/**
 * Fetch syllabi by department
 */
export function useSyllabusByDepartment(departmentId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.BY_DEPARTMENT(departmentId),
    queryFn: () =>
      apiGet<SyllabusListItem[]>(`/api/admin/syllabus-governance/department/${departmentId}`),
    enabled: !!departmentId,
    staleTime: 60000,
  });
}

/**
 * Fetch syllabi by faculty member
 */
export function useSyllabusByFaculty(facultyId: string) {
  return useQuery({
    queryKey: CACHE_KEYS.BY_FACULTY(facultyId),
    queryFn: () =>
      apiGet<SyllabusListItem[]>(`/api/admin/syllabus-governance/faculty/${facultyId}`),
    enabled: !!facultyId,
    staleTime: 60000,
  });
}

/**
 * Create a new syllabus
 */
export function useCreateSyllabus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: SyllabusCreatePayload) =>
      apiPost<SyllabusMetadata>('/api/admin/syllabus-governance', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_SYLLABI });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

/**
 * Update syllabus content
 */
export function useUpdateSyllabus(syllabusId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: SyllabusUpdatePayload) =>
      apiPut<SyllabusContent>(
        `/api/admin/syllabus-governance/${syllabusId}/content`,
        payload
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.SYLLABUS_DETAIL(syllabusId),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_SYLLABI });
    },
  });
}

/**
 * Submit syllabus for approval workflow
 */
export function useSubmitForApproval() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (syllabusId: string) =>
      apiPost<ApprovalWorkflow>(
        `/api/admin/syllabus-governance/${syllabusId}/submit-for-approval`,
        {}
      ),
    onSuccess: (_, syllabusId) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.SYLLABUS_DETAIL(syllabusId),
      });
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.SYLLABUS_APPROVAL(syllabusId),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_SYLLABI });
    },
  });
}

/**
 * Approve syllabus in workflow
 */
export function useApproveSyllabus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      syllabusId,
      feedback,
    }: {
      syllabusId: string;
      feedback?: string;
    }) =>
      apiPost<ApprovalWorkflow>(
        `/api/admin/syllabus-governance/${syllabusId}/approve`,
        { feedback }
      ),
    onSuccess: (_, { syllabusId }) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.SYLLABUS_APPROVAL(syllabusId),
      });
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.SYLLABUS_DETAIL(syllabusId),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

/**
 * Reject syllabus with feedback
 */
export function useRejectSyllabus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      syllabusId,
      reason,
    }: {
      syllabusId: string;
      reason: string;
    }) =>
      apiPost<ApprovalWorkflow>(
        `/api/admin/syllabus-governance/${syllabusId}/reject`,
        { reason }
      ),
    onSuccess: (_, { syllabusId }) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.SYLLABUS_APPROVAL(syllabusId),
      });
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.SYLLABUS_DETAIL(syllabusId),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

/**
 * Publish approved syllabus
 */
export function usePublishSyllabus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (syllabusId: string) =>
      apiPost<SyllabusMetadata>(
        `/api/admin/syllabus-governance/${syllabusId}/publish`,
        {}
      ),
    onSuccess: (_, syllabusId) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.SYLLABUS_DETAIL(syllabusId),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_SYLLABI });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

/**
 * Archive syllabus
 */
export function useArchiveSyllabus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (syllabusId: string) =>
      apiDelete<void>(`/api/admin/syllabus-governance/${syllabusId}/archive`),
    onSuccess: (_, syllabusId) => {
      queryClient.invalidateQueries({
        queryKey: CACHE_KEYS.SYLLABUS_DETAIL(syllabusId),
      });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ALL_SYLLABI });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}
