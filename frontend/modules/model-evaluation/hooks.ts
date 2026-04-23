import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type {
  CreateEvalRunPayload,
  EvalRun,
  LeaderboardEntry,
  SubmitResultsPayload,
} from "./types";

const BASE = "/api/admin/model-evaluation";

export function useCreateEvalRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateEvalRunPayload) =>
      apiPost<EvalRun>(`${BASE}/runs`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["me-runs"] }),
  });
}

export function useListEvalRuns() {
  return useQuery<EvalRun[]>({
    queryKey: ["me-runs"],
    queryFn: () => apiGet<EvalRun[]>(`${BASE}/runs`),
  });
}

export function useLeaderboard() {
  return useQuery<LeaderboardEntry[]>({
    queryKey: ["me-leaderboard"],
    queryFn: () => apiGet<LeaderboardEntry[]>(`${BASE}/leaderboard`),
  });
}

export function useSubmitEvalResults(runId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: SubmitResultsPayload) =>
      apiPost<EvalRun>(`${BASE}/runs/${runId}/results`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["me-runs"] });
      qc.invalidateQueries({ queryKey: ["me-leaderboard"] });
    },
  });
}
