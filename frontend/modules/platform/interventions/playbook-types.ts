// F2 Playbook types — mirrors backend playbook_models + playbook_schemas

export type PlaybookStepActionType =
  | "consultation_scheduled"
  | "notification_sent"
  | "plan_updated"
  | "advisor_meeting"
  | "escalation"
  | "resource_assigned"
  | "note";

export type PlaybookAssigneeRole =
  | "advisor"
  | "registrar"
  | "program_manager"
  | "dean";

export type PlaybookExecutionStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "abandoned";

export type PlaybookStepExecutionStatus =
  | "pending"
  | "completed"
  | "skipped";

export type PlaybookTriggerType = "manual" | "auto";

// -----------------------------------------------------------------------
// Playbook template
// -----------------------------------------------------------------------

export interface PlaybookStep {
  id: number;
  playbook_id: number;
  step_order: number;
  title: string;
  action_type: PlaybookStepActionType;
  rationale: string | null;
  is_mandatory: boolean;
  due_days_offset: number;
  assignee_role: PlaybookAssigneeRole;
  metadata_json: Record<string, unknown>;
}

export interface Playbook {
  id: number;
  tenant_id: number;
  name: string;
  description: string | null;
  trigger_threshold_id: number | null;
  enabled: boolean;
  version: number;
  metadata_json: Record<string, unknown>;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
  steps: PlaybookStep[];
}

export interface PlaybookListResponse {
  items: Playbook[];
  total: number;
}

export interface PlaybookCreatePayload {
  name: string;
  description?: string | null;
  trigger_threshold_id?: number | null;
  enabled?: boolean;
  steps?: PlaybookStepCreatePayload[];
  metadata_json?: Record<string, unknown>;
}

export interface PlaybookStepCreatePayload {
  step_order: number;
  title: string;
  action_type: PlaybookStepActionType;
  rationale?: string | null;
  is_mandatory?: boolean;
  due_days_offset?: number;
  assignee_role?: PlaybookAssigneeRole;
  metadata_json?: Record<string, unknown>;
}

export interface PlaybookUpdatePayload {
  expected_version: number;
  name?: string;
  description?: string | null;
  trigger_threshold_id?: number | null;
  enabled?: boolean;
  metadata_json?: Record<string, unknown>;
}

// -----------------------------------------------------------------------
// Playbook execution
// -----------------------------------------------------------------------

export interface PlaybookStepExecution {
  id: number;
  execution_id: number;
  step_id: number;
  status: PlaybookStepExecutionStatus;
  performed_by: string | null;
  performed_at: string | null;
  outcome_note: string | null;
  metadata_json: Record<string, unknown>;
}

export interface PlaybookExecution {
  id: number;
  tenant_id: number;
  playbook_id: number;
  case_id: number | null;
  student_profile_id: number | null;
  triggered_by: PlaybookTriggerType;
  status: PlaybookExecutionStatus;
  started_at: string;
  completed_at: string | null;
  abandoned_at: string | null;
  abandon_reason: string | null;
  outcome_delta_score: number | null;
  metadata_json: Record<string, unknown>;
  created_by: string;
  created_at: string;
  updated_at: string;
  step_executions: PlaybookStepExecution[];
}

export interface PlaybookExecutionListResponse {
  items: PlaybookExecution[];
  total: number;
}

export interface StartExecutionPayload {
  playbook_id: number;
  case_id?: number | null;
  student_profile_id?: number | null;
  triggered_by?: PlaybookTriggerType;
  metadata_json?: Record<string, unknown>;
}

export interface CompleteStepPayload {
  outcome_note?: string | null;
  metadata_json?: Record<string, unknown>;
}

export interface SkipStepPayload {
  outcome_note?: string | null;
}

export interface AbandonExecutionPayload {
  abandon_reason: string;
}
