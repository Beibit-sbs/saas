import { apiDelete, apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type {
  AbandonExecutionPayload,
  CompleteStepPayload,
  Playbook,
  PlaybookCreatePayload,
  PlaybookExecution,
  PlaybookExecutionListResponse,
  PlaybookExecutionStatus,
  PlaybookListResponse,
  PlaybookUpdatePayload,
  SkipStepPayload,
  StartExecutionPayload,
} from "./playbook-types";

const BASE = "/api/admin/interventions/playbooks";
const EXEC = `${BASE}/executions`;

export const playbookApi = {
  // --- Templates ---
  list: (params?: { enabled_only?: boolean; offset?: number; limit?: number }) =>
    apiGet<PlaybookListResponse>(BASE, params),

  get: (id: number) => apiGet<Playbook>(`${BASE}/${id}`),

  create: (payload: PlaybookCreatePayload) => apiPost<Playbook>(BASE, payload),

  update: (id: number, payload: PlaybookUpdatePayload) =>
    apiPatch<Playbook>(`${BASE}/${id}`, payload),

  delete: (id: number) => apiDelete<void>(`${BASE}/${id}`),

  // --- Executions ---
  listExecutions: (params?: {
    playbook_id?: number;
    case_id?: number;
    status?: PlaybookExecutionStatus;
    offset?: number;
    limit?: number;
  }) => apiGet<PlaybookExecutionListResponse>(EXEC, params),

  getExecution: (id: number) => apiGet<PlaybookExecution>(`${EXEC}/${id}`),

  startExecution: (payload: StartExecutionPayload) =>
    apiPost<PlaybookExecution>(EXEC, payload),

  abandonExecution: (id: number, payload: AbandonExecutionPayload) =>
    apiPost<PlaybookExecution>(`${EXEC}/${id}/abandon`, payload),

  completeStep: (
    executionId: number,
    stepExecutionId: number,
    payload: CompleteStepPayload,
  ) =>
    apiPost<PlaybookExecution>(
      `${EXEC}/${executionId}/steps/${stepExecutionId}/complete`,
      payload,
    ),

  skipStep: (
    executionId: number,
    stepExecutionId: number,
    payload: SkipStepPayload,
  ) =>
    apiPost<PlaybookExecution>(
      `${EXEC}/${executionId}/steps/${stepExecutionId}/skip`,
      payload,
    ),
};
