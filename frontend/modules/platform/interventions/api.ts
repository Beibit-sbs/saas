import { apiGet, apiPost } from "@/shared/api/client";
import type {
  AddInterventionActionPayload,
  AssignInterventionPayload,
  InterventionAction,
  InterventionActionsResponse,
  InterventionCase,
  InterventionCasesResponse,
  UpdateInterventionStatusPayload,
} from "./types";

const BASE = "/api/admin/interventions/cases";

type BackendInterventionCase = {
  id: number;
  tenant_id: number;
  student_profile_id: number;
  ai_recommendation_id: number | null;
  recommendation_snapshot: string | null;
  severity: InterventionCase["severity"];
  status: InterventionCase["status"];
  owner_type: InterventionCase["owner_type"];
  owner_ref: string;
  assignee_type: InterventionCase["assignee_type"];
  assignee_ref: string | null;
  due_at: string | null;
  metadata_json: Record<string, unknown>;
  last_action_at: string | null;
  version: number;
  created_at: string;
  updated_at: string;
};

type BackendInterventionAction = {
  id: number;
  case_id: number;
  action_type: InterventionAction["action_type"];
  actor_type: InterventionAction["actor_type"];
  actor_ref: string;
  assignee_type: InterventionAction["assignee_type"];
  assignee_ref: string | null;
  prev_status: InterventionAction["prev_status"];
  new_status: InterventionAction["new_status"];
  description: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

type BackendListResponse = {
  total: number;
  page: number;
  page_size: number;
  items: BackendInterventionCase[];
};

type BackendActionsResponse = {
  total: number;
  items: BackendInterventionAction[];
};

type BackendWithCase = { case: BackendInterventionCase };

type BackendCreateActionResponse = {
  case: BackendInterventionCase;
  action: BackendInterventionAction;
};

function toCase(row: BackendInterventionCase): InterventionCase {
  return {
    id: String(row.id),
    tenant_id: String(row.tenant_id),
    student_profile_id: String(row.student_profile_id),
    ai_recommendation_id: row.ai_recommendation_id != null ? String(row.ai_recommendation_id) : null,
    recommendation_snapshot: row.recommendation_snapshot ?? null,
    severity: row.severity,
    status: row.status,
    owner_type: row.owner_type,
    owner_ref: row.owner_ref,
    assignee_type: row.assignee_type,
    assignee_ref: row.assignee_ref,
    due_at: row.due_at,
    metadata_json: row.metadata_json ?? {},
    last_action_at: row.last_action_at,
    version: Number(row.version ?? 0),
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

function toAction(row: BackendInterventionAction): InterventionAction {
  return {
    id: String(row.id),
    case_id: String(row.case_id),
    action_type: row.action_type,
    actor_type: row.actor_type,
    actor_ref: row.actor_ref,
    assignee_type: row.assignee_type,
    assignee_ref: row.assignee_ref,
    prev_status: row.prev_status,
    new_status: row.new_status,
    description: row.description,
    metadata_json: row.metadata_json ?? {},
    created_at: row.created_at,
  };
}

export const interventionsApi = {
  listCases: async (params?: {
    page?: number;
    page_size?: number;
    status?: string;
    severity?: string;
    assignee_ref?: string;
    overdue_only?: boolean;
  }): Promise<InterventionCasesResponse> => {
    const payload = await apiGet<BackendListResponse>(BASE, params);
    return {
      total: Number(payload?.total ?? 0),
      page: Number(payload?.page ?? params?.page ?? 1),
      page_size: Number(payload?.page_size ?? params?.page_size ?? 20),
      items: Array.isArray(payload?.items) ? payload.items.map(toCase) : [],
    };
  },

  getCase: async (id: string): Promise<InterventionCase> => {
    const payload = await apiGet<BackendInterventionCase>(`${BASE}/${id}`);
    return toCase(payload);
  },

  listActions: async (caseId: string, limit = 20): Promise<InterventionActionsResponse> => {
    const payload = await apiGet<BackendActionsResponse>(`${BASE}/${caseId}/actions`, { limit });
    return {
      total: Number(payload?.total ?? 0),
      items: Array.isArray(payload?.items) ? payload.items.map(toAction) : [],
    };
  },

  takeCase: async (id: string, expectedVersion: number): Promise<InterventionCase> => {
    const payload = await apiPost<BackendWithCase>(`${BASE}/${id}/take`, { expected_version: expectedVersion });
    return toCase(payload.case);
  },

  assignCase: async (id: string, body: AssignInterventionPayload): Promise<InterventionCase> => {
    const payload = await apiPost<BackendWithCase>(`${BASE}/${id}/assign`, body);
    return toCase(payload.case);
  },

  updateStatus: async (id: string, body: UpdateInterventionStatusPayload): Promise<InterventionCase> => {
    const payload = await apiPost<BackendWithCase>(`${BASE}/${id}/status`, body);
    return toCase(payload.case);
  },

  addAction: async (id: string, body: AddInterventionActionPayload): Promise<{ case: InterventionCase; action: InterventionAction }> => {
    const payload = await apiPost<BackendCreateActionResponse>(`${BASE}/${id}/actions`, body);
    return {
      case: toCase(payload.case),
      action: toAction(payload.action),
    };
  },
};
