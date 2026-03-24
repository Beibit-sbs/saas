// Automation / Workflow Engine v1 — frontend types
// Designed for future visual workflow builder compatibility

export type AutomationOperator = "==" | "!=" | ">" | "<" | ">=" | "<=";
export type AutomationActionType = "send_notification" | "create_task" | "emit_event";
export type AutomationExecutionStatus = "pending" | "completed" | "failed";

// --------------------------------------------------------------------------
// Condition (supports future compound conditions via AND/OR wrappers)
// --------------------------------------------------------------------------

export interface AutomationCondition {
  field: string;
  operator: AutomationOperator;
  value: string | number;
}

// --------------------------------------------------------------------------
// Actions (union type — discriminated via "type")
// --------------------------------------------------------------------------

export interface SendNotificationAction {
  type: "send_notification";
  channel: string;
  template: string;
}

export interface CreateTaskAction {
  type: "create_task";
  job_type: string;
  max_retries?: number;
}

export interface EmitEventAction {
  type: "emit_event";
  event_type: string;
  aggregate_type: string;
}

export type AutomationAction = SendNotificationAction | CreateTaskAction | EmitEventAction;

// --------------------------------------------------------------------------
// Rule (backend AutomationRuleModel → API response)
// --------------------------------------------------------------------------

export interface AutomationRule {
  id: number;
  tenant_id: number;
  name: string;
  description: string;
  event_type: string;
  condition_json: AutomationCondition | Record<string, unknown>;
  actions_json: AutomationAction[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  version: number;
}

// --------------------------------------------------------------------------
// Execution (backend AutomationExecutionModel → API response)
// --------------------------------------------------------------------------

export interface AutomationExecution {
  id: number;
  tenant_id: number;
  rule_id: number;
  event_id: number;
  status: AutomationExecutionStatus;
  result_json: Record<string, unknown>;
  error_message: string | null;
  executed_at: string;
  created_at: string;
}

// --------------------------------------------------------------------------
// Create request (POST body)
// --------------------------------------------------------------------------

export interface CreateAutomationRuleRequest {
  tenant_id: number;
  name: string;
  description: string;
  event_type: string;
  condition_json: AutomationCondition | Record<string, unknown>;
  actions_json: AutomationAction[];
  is_active: boolean;
}

// --------------------------------------------------------------------------
// Helpers — purely presentational, visual builder will extend these
// --------------------------------------------------------------------------

export const KNOWN_EVENT_TYPES = [
  "tenant.created",
  "student.created",
  "enrollment.created",
  "grade.submitted",
] as const;

export const AUTOMATION_OPERATORS: { label: string; value: AutomationOperator }[] = [
  { label: "equals (==)", value: "==" },
  { label: "not equals (!=)", value: "!=" },
  { label: "greater than (>)", value: ">" },
  { label: "less than (<)", value: "<" },
  { label: "greater or equal (>=)", value: ">=" },
  { label: "less or equal (<=)", value: "<=" },
];

export const AUTOMATION_ACTION_TYPES: { label: string; value: AutomationActionType }[] = [
  { label: "Send Notification", value: "send_notification" },
  { label: "Create Task", value: "create_task" },
  { label: "Emit Event", value: "emit_event" },
];

/** Summarize condition_json as human-readable string */
export function summarizeCondition(condition: AutomationCondition | Record<string, unknown>): string {
  if (!condition || !("field" in condition) || !condition.field) return "—";
  const c = condition as AutomationCondition;
  return `${c.field} ${c.operator} ${c.value}`;
}

/** Summarize actions_json as short label list */
export function summarizeActions(actions: AutomationAction[]): string {
  if (!actions || actions.length === 0) return "—";
  return actions.map((a) => a.type.replace("_", " ")).join(", ");
}
