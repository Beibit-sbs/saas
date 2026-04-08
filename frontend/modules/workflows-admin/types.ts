export interface WorkflowInstance {
  id: number;
  entity_type: string;
  entity_id: number;
  status: string;
  initiated_by: string;
  started_at: string;
}

export interface WorkflowTask {
  id: number;
  workflow_instance_id: number;
  title: string;
  assignee_ref: string;
  status: string;
  due_at?: string | null;
}

export interface WorkflowInstancesResponse {
  total: number;
  items: WorkflowInstance[];
}

export interface WorkflowTasksResponse {
  total: number;
  items: WorkflowTask[];
}

export interface StartWorkflowPayload {
  workflow_key: string;
  entity_type: string;
  entity_id: number;
  metadata_json?: Record<string, unknown>;
  workflow_version_no?: number;
}
