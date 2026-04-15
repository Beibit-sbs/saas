import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { playbookApi } from "./playbook-api";
import type {
  AbandonExecutionPayload,
  CompleteStepPayload,
  PlaybookCreatePayload,
  PlaybookExecutionStatus,
  PlaybookUpdatePayload,
  SkipStepPayload,
  StartExecutionPayload,
} from "./playbook-types";

export const PLAYBOOKS_KEY = "playbooks";

// -----------------------------------------------------------------------
// Queries — templates
// -----------------------------------------------------------------------

export function usePlaybooks(params?: {
  enabled_only?: boolean;
  offset?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: [PLAYBOOKS_KEY, "list", params],
    queryFn: () => playbookApi.list(params),
    refetchInterval: 30_000,
  });
}

export function usePlaybook(id: number | null) {
  return useQuery({
    queryKey: [PLAYBOOKS_KEY, "detail", id],
    queryFn: () => playbookApi.get(id!),
    enabled: id !== null,
  });
}

// -----------------------------------------------------------------------
// Queries — executions
// -----------------------------------------------------------------------

export function usePlaybookExecutions(params?: {
  playbook_id?: number;
  case_id?: number;
  status?: PlaybookExecutionStatus;
  offset?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: [PLAYBOOKS_KEY, "executions", params],
    queryFn: () => playbookApi.listExecutions(params),
    refetchInterval: 15_000,
  });
}

export function usePlaybookExecution(id: number | null) {
  return useQuery({
    queryKey: [PLAYBOOKS_KEY, "execution", id],
    queryFn: () => playbookApi.getExecution(id!),
    enabled: id !== null,
    refetchInterval: 10_000,
  });
}

// -----------------------------------------------------------------------
// Mutations — templates
// -----------------------------------------------------------------------

function useInvalidatePlaybooks() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: [PLAYBOOKS_KEY] });
}

export function useCreatePlaybook() {
  const invalidate = useInvalidatePlaybooks();
  return useMutation({
    mutationFn: (payload: PlaybookCreatePayload) => playbookApi.create(payload),
    onSuccess: invalidate,
  });
}

export function useUpdatePlaybook() {
  const invalidate = useInvalidatePlaybooks();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: PlaybookUpdatePayload }) =>
      playbookApi.update(id, payload),
    onSuccess: invalidate,
  });
}

export function useDeletePlaybook() {
  const invalidate = useInvalidatePlaybooks();
  return useMutation({
    mutationFn: (id: number) => playbookApi.delete(id),
    onSuccess: invalidate,
  });
}

// -----------------------------------------------------------------------
// Mutations — executions
// -----------------------------------------------------------------------

export function useStartExecution() {
  const invalidate = useInvalidatePlaybooks();
  return useMutation({
    mutationFn: (payload: StartExecutionPayload) =>
      playbookApi.startExecution(payload),
    onSuccess: invalidate,
  });
}

export function useAbandonExecution() {
  const invalidate = useInvalidatePlaybooks();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: AbandonExecutionPayload }) =>
      playbookApi.abandonExecution(id, payload),
    onSuccess: invalidate,
  });
}

export function useCompleteStep() {
  const invalidate = useInvalidatePlaybooks();
  return useMutation({
    mutationFn: ({
      executionId,
      stepExecutionId,
      payload,
    }: {
      executionId: number;
      stepExecutionId: number;
      payload: CompleteStepPayload;
    }) => playbookApi.completeStep(executionId, stepExecutionId, payload),
    onSuccess: invalidate,
  });
}

export function useSkipStep() {
  const invalidate = useInvalidatePlaybooks();
  return useMutation({
    mutationFn: ({
      executionId,
      stepExecutionId,
      payload,
    }: {
      executionId: number;
      stepExecutionId: number;
      payload: SkipStepPayload;
    }) => playbookApi.skipStep(executionId, stepExecutionId, payload),
    onSuccess: invalidate,
  });
}
