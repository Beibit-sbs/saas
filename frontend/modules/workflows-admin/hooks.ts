import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type {
  WorkflowInstancesResponse,
  WorkflowTasksResponse,
  StartWorkflowPayload,
  WorkflowInstance,
} from "./types";

const BASE = "/api/admin/workflows";
export const WORKFLOW_INSTANCES_KEY = "workflow-instances";
export const WORKFLOW_TASKS_KEY = "workflow-tasks";

export function useWorkflowInstances() {
  return useQuery({
    queryKey: [WORKFLOW_INSTANCES_KEY],
    queryFn: () => apiGet<WorkflowInstancesResponse>(`${BASE}/instances`),
  });
}

export function useWorkflowTasks() {
  return useQuery({
    queryKey: [WORKFLOW_TASKS_KEY],
    queryFn: () => apiGet<WorkflowTasksResponse>(`${BASE}/tasks`),
  });
}

export function useStartWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: StartWorkflowPayload) => apiPost<WorkflowInstance>(`${BASE}/start`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [WORKFLOW_INSTANCES_KEY] });
      qc.invalidateQueries({ queryKey: [WORKFLOW_TASKS_KEY] });
    },
  });
}
