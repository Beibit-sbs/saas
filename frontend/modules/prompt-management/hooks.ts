import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type {
  ABTestResult,
  ABTestRoutePayload,
  CreateTemplatePayload,
  PromptTemplate,
} from "./types";

const BASE = "/api/admin/prompt-management";

export function useCreateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateTemplatePayload) =>
      apiPost<PromptTemplate>(`${BASE}/templates`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pm-templates"] }),
  });
}

export function useListTemplates() {
  return useQuery<PromptTemplate[]>({
    queryKey: ["pm-templates"],
    queryFn: () => apiGet<PromptTemplate[]>(`${BASE}/templates`),
  });
}

export function useABRoute() {
  return useMutation({
    mutationFn: (payload: ABTestRoutePayload) =>
      apiPost<ABTestResult>(`${BASE}/ab-test/route`, payload),
  });
}
