/**
 * Rector Assignment Hooks
 * TanStack Query hooks for rector assignment workflow lifecycle.
 * All API calls go through the existing BFF catch-all proxy.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from '@/shared/api/client';
import type {
  AssignmentAuditEvent,
  AssignmentComment,
  AssignmentCreatePayload,
  AssignmentDetailResponse,
  AssignmentEscalation,
  AssignmentEvidence,
  AssignmentListFilters,
  AssignmentListResponse,
  AssignmentReport,
  AssignmentReportCreatePayload,
  AssignmentStatusHistory,
  AssignmentTemplate,
  AssignmentTemplateCreatePayload,
  AssignmentTemplateUpdatePayload,
  AssignmentUpdatePayload,
  CommentCreatePayload,
  DashboardSummary,
  DashboardSummaryExpanded,
  EvidenceCreatePayload,
  OutboxEventFilters,
  OutboxEventListResponse,
  RectorAssignment,
  RectorAssignmentOutboxEvent,
  RectorAssignmentSlaPolicy,
  RectorAssignmentEscalationPolicy,
  SlaPolicyCreatePayload,
  SlaPolicyUpdatePayload,
  EscalationPolicyCreatePayload,
  EscalationPolicyUpdatePayload,
  StatusActionPayload,
} from './types';

const RECTOR_BASE = '/api/admin/rector-assignments';

// ---------------------------------------------------------------------------
// Cache keys
// ---------------------------------------------------------------------------

const CACHE_KEYS = {
  DASHBOARD: ['rector-assignments:dashboard'] as const,
  ALL: (filters?: AssignmentListFilters) => ['rector-assignments:all', filters] as const,
  DETAIL: (id: string | number) => ['rector-assignments:detail', String(id)] as const,
  REPORTS: (id: string | number) => ['rector-assignments:reports', String(id)] as const,
  EVIDENCE: (id: string | number) => ['rector-assignments:evidence', String(id)] as const,
  COMMENTS: (id: string | number) => ['rector-assignments:comments', String(id)] as const,
  STATUS_HISTORY: (id: string | number) => ['rector-assignments:history', String(id)] as const,
  AUDIT: (id: string | number) => ['rector-assignments:audit', String(id)] as const,
  ESCALATIONS_DETAIL: (id: string | number) => ['rector-assignments:escalations-detail', String(id)] as const,
  TEMPLATES: ['rector-assignments:templates'] as const,
  MY: ['rector-assignments:my'] as const,
  OUTBOX: ['rector-assignments:outbox'] as const,
  OUTBOX_ASSIGNMENT: (id: string | number) => ['rector-assignments:outbox', String(id)] as const,
  SLA_POLICIES: ['rector-assignments:sla-policies'] as const,
  ESCALATION_POLICIES: ['rector-assignments:escalation-policies'] as const,
};

// ---------------------------------------------------------------------------
// Read hooks
// ---------------------------------------------------------------------------

/** Dashboard summary — assert fake_metrics === false before rendering KPIs */
export function useRectorAssignmentDashboard() {
  return useQuery({
    queryKey: CACHE_KEYS.DASHBOARD,
    queryFn: () => apiGet<DashboardSummaryExpanded>(`${RECTOR_BASE}/dashboard/summary`),
    staleTime: 60000,
  });
}

export function useRectorAssignmentList(filters?: AssignmentListFilters) {
  return useQuery({
    queryKey: CACHE_KEYS.ALL(filters),
    queryFn: async () => {
      const params: Record<string, string | number | boolean> = {};
      if (filters?.status && filters.status !== 'all') params.status = filters.status;
      if (filters?.priority) params.priority = filters.priority;
      if (filters?.unit_id) params.unit_id = filters.unit_id;
      if (filters?.assignee_id) params.assignee_id = filters.assignee_id;
      if (filters?.overdue_only) params.overdue_only = true;
      if (filters?.search) params.search = filters.search;
      if (filters?.page) params.page = filters.page;
      if (filters?.page_size) params.page_size = filters.page_size;
      if (filters?.my_assignments) params.my_assignments = true;
      return apiGet<RectorAssignment[]>(RECTOR_BASE, params);
    },
    staleTime: 60000,
  });
}

/** Assignments where the current user is an assignee */
export function useMyRectorAssignments() {
  return useQuery({
    queryKey: CACHE_KEYS.MY,
    queryFn: () => apiGet<RectorAssignment[]>(RECTOR_BASE, { my_assignments: true }),
    staleTime: 60000,
  });
}

export function useRectorAssignmentDetail(id: string | number) {
  return useQuery({
    queryKey: CACHE_KEYS.DETAIL(id),
    queryFn: () => apiGet<AssignmentDetailResponse>(`${RECTOR_BASE}/${id}`),
    enabled: !!id,
    staleTime: 30000,
  });
}

export function useAssignmentReports(id: string | number) {
  return useQuery({
    queryKey: CACHE_KEYS.REPORTS(id),
    queryFn: () => apiGet<AssignmentReport[]>(`${RECTOR_BASE}/${id}/reports`),
    enabled: !!id,
    staleTime: 30000,
  });
}

export function useAssignmentEvidence(id: string | number) {
  return useQuery({
    queryKey: CACHE_KEYS.EVIDENCE(id),
    queryFn: () => apiGet<AssignmentEvidence[]>(`${RECTOR_BASE}/${id}/evidence`),
    enabled: !!id,
    staleTime: 30000,
  });
}

export function useAssignmentComments(id: string | number) {
  return useQuery({
    queryKey: CACHE_KEYS.COMMENTS(id),
    queryFn: () => apiGet<AssignmentComment[]>(`${RECTOR_BASE}/${id}/comments`),
    enabled: !!id,
    staleTime: 30000,
  });
}

export function useAssignmentStatusHistory(id: string | number) {
  return useQuery({
    queryKey: CACHE_KEYS.STATUS_HISTORY(id),
    queryFn: () => apiGet<AssignmentStatusHistory[]>(`${RECTOR_BASE}/${id}/status-history`),
    enabled: !!id,
    staleTime: 30000,
  });
}

export function useAssignmentAudit(id: string | number) {
  return useQuery({
    queryKey: CACHE_KEYS.AUDIT(id),
    queryFn: () => apiGet<AssignmentAuditEvent[]>(`${RECTOR_BASE}/${id}/audit`),
    enabled: !!id,
    staleTime: 30000,
  });
}

export function useAssignmentEscalationsDetail(id: string | number) {
  return useQuery({
    queryKey: CACHE_KEYS.ESCALATIONS_DETAIL(id),
    queryFn: () => apiGet<AssignmentEscalation[]>(`${RECTOR_BASE}/${id}/escalations`),
    enabled: !!id,
    staleTime: 30000,
  });
}

export function useRectorAssignmentTemplates() {
  return useQuery({
    queryKey: CACHE_KEYS.TEMPLATES,
    queryFn: () => apiGet<AssignmentTemplate[]>(`${RECTOR_BASE}/templates`),
    staleTime: 60000,
  });
}

// ---------------------------------------------------------------------------
// Mutation helpers
// ---------------------------------------------------------------------------

function invalidateAfterLifecycle(
  queryClient: ReturnType<typeof useQueryClient>,
  id?: string | number,
) {
  if (id) {
    queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DETAIL(id) });
    queryClient.invalidateQueries({ queryKey: CACHE_KEYS.STATUS_HISTORY(id) });
    queryClient.invalidateQueries({ queryKey: CACHE_KEYS.AUDIT(id) });
  }
  queryClient.invalidateQueries({ queryKey: ['rector-assignments:all'] });
  queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
  queryClient.invalidateQueries({ queryKey: CACHE_KEYS.MY });
}

// ---------------------------------------------------------------------------
// Create / Update mutations
// ---------------------------------------------------------------------------

export function useCreateRectorAssignment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AssignmentCreatePayload) =>
      apiPost<RectorAssignment>(RECTOR_BASE, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rector-assignments:all'] });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

export function useUpdateRectorAssignment(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AssignmentUpdatePayload) =>
      apiPut<RectorAssignment>(`${RECTOR_BASE}/${id}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DETAIL(id) });
      queryClient.invalidateQueries({ queryKey: ['rector-assignments:all'] });
    },
  });
}

// ---------------------------------------------------------------------------
// Lifecycle action mutations
// ---------------------------------------------------------------------------

export function useAssignAssignment(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: StatusActionPayload) =>
      apiPost<RectorAssignment>(`${RECTOR_BASE}/${id}/assign`, payload),
    onSuccess: () => invalidateAfterLifecycle(queryClient, id),
  });
}

export function useAcceptAssignment(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiPost<RectorAssignment>(`${RECTOR_BASE}/${id}/accept`, {}),
    onSuccess: () => invalidateAfterLifecycle(queryClient, id),
  });
}

export function useReturnAssignment(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: StatusActionPayload) =>
      apiPost<RectorAssignment>(`${RECTOR_BASE}/${id}/return-for-revision`, payload),
    onSuccess: () => invalidateAfterLifecycle(queryClient, id),
  });
}

export function useCompleteAssignment(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: StatusActionPayload) =>
      apiPost<RectorAssignment>(`${RECTOR_BASE}/${id}/complete`, payload),
    onSuccess: () => invalidateAfterLifecycle(queryClient, id),
  });
}

export function useEscalateAssignment(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: StatusActionPayload & { escalated_to_role: string }) =>
      apiPost<RectorAssignment>(`${RECTOR_BASE}/${id}/escalate`, payload),
    onSuccess: () => invalidateAfterLifecycle(queryClient, id),
  });
}

export function useCancelAssignment(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: StatusActionPayload) =>
      apiPost<RectorAssignment>(`${RECTOR_BASE}/${id}/cancel`, payload),
    onSuccess: () => invalidateAfterLifecycle(queryClient, id),
  });
}

export function useArchiveAssignment(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: StatusActionPayload) =>
      apiPost<RectorAssignment>(`${RECTOR_BASE}/${id}/archive`, payload),
    onSuccess: () => invalidateAfterLifecycle(queryClient, id),
  });
}

// ---------------------------------------------------------------------------
// Report mutations
// ---------------------------------------------------------------------------

export function useSubmitReport(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AssignmentReportCreatePayload) =>
      apiPost<AssignmentReport>(`${RECTOR_BASE}/${id}/reports`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DETAIL(id) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.REPORTS(id) });
      queryClient.invalidateQueries({ queryKey: ['rector-assignments:all'] });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
    },
  });
}

// ---------------------------------------------------------------------------
// Evidence mutations
// ---------------------------------------------------------------------------

export function useAttachEvidence(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: EvidenceCreatePayload) =>
      apiPost<AssignmentEvidence>(`${RECTOR_BASE}/${id}/evidence`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DETAIL(id) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.EVIDENCE(id) });
    },
  });
}

// ---------------------------------------------------------------------------
// Comment mutations
// ---------------------------------------------------------------------------

export function useAddComment(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CommentCreatePayload) =>
      apiPost<AssignmentComment>(`${RECTOR_BASE}/${id}/comments`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.COMMENTS(id) });
    },
  });
}

// ---------------------------------------------------------------------------
// Template mutations
// ---------------------------------------------------------------------------

export function useCreateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AssignmentTemplateCreatePayload) =>
      apiPost<AssignmentTemplate>(`${RECTOR_BASE}/templates`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.TEMPLATES });
    },
  });
}

export function useUpdateTemplate(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AssignmentTemplateUpdatePayload) =>
      apiPatch<AssignmentTemplate>(`${RECTOR_BASE}/templates/${id}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.TEMPLATES });
    },
  });
}

// ---------------------------------------------------------------------------
// A-031.5 Outbox hooks
// ---------------------------------------------------------------------------

/** Global outbox event list — requires outbox.read permission */
export function useOutboxEvents(filters?: OutboxEventFilters) {
  return useQuery({
    queryKey: [...CACHE_KEYS.OUTBOX, filters],
    queryFn: () => {
      const params: Record<string, string | number> = {};
      if (filters?.status) params.status = filters.status;
      if (filters?.event_type) params.event_type = filters.event_type;
      if (filters?.channel) params.channel = filters.channel;
      if (filters?.assignment_id) params.assignment_id = filters.assignment_id;
      if (filters?.page) params.page = filters.page;
      if (filters?.page_size) params.page_size = filters.page_size;
      return apiGet<OutboxEventListResponse>(`${RECTOR_BASE}/outbox`, params);
    },
    staleTime: 30000,
  });
}

/** Outbox events for a specific assignment — requires outbox.read */
export function useAssignmentOutboxEvents(id: string | number) {
  return useQuery({
    queryKey: CACHE_KEYS.OUTBOX_ASSIGNMENT(id),
    queryFn: () => apiGet<RectorAssignmentOutboxEvent[]>(`${RECTOR_BASE}/${id}/outbox`),
    enabled: !!id,
    staleTime: 30000,
  });
}

/** Mark outbox event READY — requires outbox.manage */
export function useMarkOutboxEventReady(assignmentId: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (eventId: number) =>
      apiPost<RectorAssignmentOutboxEvent>(
        `${RECTOR_BASE}/${assignmentId}/outbox/${eventId}/ready`,
        {},
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.OUTBOX_ASSIGNMENT(assignmentId) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.OUTBOX });
    },
  });
}

/** Cancel outbox event — requires outbox.manage */
export function useCancelOutboxEvent(assignmentId: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (eventId: number) =>
      apiPost<RectorAssignmentOutboxEvent>(
        `${RECTOR_BASE}/${assignmentId}/outbox/${eventId}/cancel`,
        {},
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.OUTBOX_ASSIGNMENT(assignmentId) });
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.OUTBOX });
    },
  });
}

// ---------------------------------------------------------------------------
// A-031.5 SLA Policy hooks
// ---------------------------------------------------------------------------

export function useSlaPolicies() {
  return useQuery({
    queryKey: CACHE_KEYS.SLA_POLICIES,
    queryFn: () => apiGet<RectorAssignmentSlaPolicy[]>(`${RECTOR_BASE}/sla-policies`),
    staleTime: 60000,
  });
}

export function useCreateSlaPolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SlaPolicyCreatePayload) =>
      apiPost<RectorAssignmentSlaPolicy>(`${RECTOR_BASE}/sla-policies`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.SLA_POLICIES });
    },
  });
}

export function useUpdateSlaPolicy(policyId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SlaPolicyUpdatePayload) =>
      apiPut<RectorAssignmentSlaPolicy>(`${RECTOR_BASE}/sla-policies/${policyId}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.SLA_POLICIES });
    },
  });
}

/** Archive SLA policy (backend DELETE = archive, not hard delete) */
export function useArchiveSlaPolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (policyId: number) =>
      apiDelete(`${RECTOR_BASE}/sla-policies/${policyId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.SLA_POLICIES });
    },
  });
}

// ---------------------------------------------------------------------------
// A-031.5 Escalation Policy hooks
// ---------------------------------------------------------------------------

export function useEscalationPolicies() {
  return useQuery({
    queryKey: CACHE_KEYS.ESCALATION_POLICIES,
    queryFn: () => apiGet<RectorAssignmentEscalationPolicy[]>(`${RECTOR_BASE}/escalation-policies`),
    staleTime: 60000,
  });
}

export function useCreateEscalationPolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: EscalationPolicyCreatePayload) =>
      apiPost<RectorAssignmentEscalationPolicy>(
        `${RECTOR_BASE}/escalation-policies`,
        payload,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ESCALATION_POLICIES });
    },
  });
}

export function useUpdateEscalationPolicy(policyId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: EscalationPolicyUpdatePayload) =>
      apiPut<RectorAssignmentEscalationPolicy>(
        `${RECTOR_BASE}/escalation-policies/${policyId}`,
        payload,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ESCALATION_POLICIES });
    },
  });
}

/** Archive escalation policy (backend DELETE = archive, not hard delete) */
export function useArchiveEscalationPolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (policyId: number) =>
      apiDelete(`${RECTOR_BASE}/escalation-policies/${policyId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.ESCALATION_POLICIES });
    },
  });
}
