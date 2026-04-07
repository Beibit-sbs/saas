import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { jobsApi } from "./api";
import type { TriggerJobPayload } from "./types";

export const JOBS_KEY = "jobs";

export function useJobs(params?: { page?: number; page_size?: number; status?: string; job_type?: string }) {
  return useQuery({
    queryKey: [JOBS_KEY, params],
    queryFn: () => jobsApi.list(params),
    refetchInterval: 10_000,
  });
}

export function useJob(id: string) {
  return useQuery({
    queryKey: [JOBS_KEY, id],
    queryFn: () => jobsApi.get(id),
    enabled: !!id,
    refetchInterval: 5_000,
  });
}

export function useTriggerJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: TriggerJobPayload) => jobsApi.trigger(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [JOBS_KEY] }),
  });
}

export function useRetryJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => jobsApi.retry(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: [JOBS_KEY] }),
  });
}

export function useCancelJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => jobsApi.cancel(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: [JOBS_KEY] }),
  });
}
