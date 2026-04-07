export type InterventionSeverity = "low" | "medium" | "high";

export type InterventionStatus = "open" | "in_progress" | "resolved" | "closed";

export type InterventionActionType =
  | "assignment"
  | "status_change"
  | "consultation_scheduled"
  | "notification_sent"
  | "plan_updated"
  | "note";

export interface InterventionCase {
  id: string;
  tenant_id: string;
  student_profile_id: string;
  ai_recommendation_id: string | null;
  recommendation_snapshot: string | null;
  severity: InterventionSeverity;
  status: InterventionStatus;
  owner_type: "user" | "group";
  owner_ref: string;
  assignee_type: "user" | "group" | null;
  assignee_ref: string | null;
  due_at: string | null;
  metadata_json: Record<string, unknown>;
  last_action_at: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface InterventionAction {
  id: string;
  case_id: string;
  action_type: InterventionActionType;
  actor_type: "user" | "service";
  actor_ref: string;
  assignee_type: "user" | "group" | null;
  assignee_ref: string | null;
  prev_status: InterventionStatus | null;
  new_status: InterventionStatus | null;
  description: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

export interface InterventionCasesResponse {
  total: number;
  page: number;
  page_size: number;
  items: InterventionCase[];
}

export interface InterventionActionsResponse {
  total: number;
  items: InterventionAction[];
}

export interface UpdateInterventionStatusPayload {
  status: InterventionStatus;
  expected_version: number;
}

export interface AssignInterventionPayload {
  assignee_type: "user" | "group";
  assignee_ref: string;
  due_at?: string;
  expected_version: number;
}

export interface AddInterventionActionPayload {
  action_type: InterventionActionType;
  description: string;
  expected_version: number;
  metadata_json?: Record<string, unknown>;
}
