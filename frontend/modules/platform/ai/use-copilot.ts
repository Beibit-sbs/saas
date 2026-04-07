import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type { CopilotAnswer, CopilotAskRequest, CopilotQueryLog } from "./types";

export const COPILOT_LOGS_KEY = "platform-ai-copilot-logs";

export function useAskCopilot() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CopilotAskRequest) =>
      apiPost<CopilotAnswer>("/api/bff/admin/platform/ai/copilot/ask", payload),
    onSuccess: (result, variables) => {
      void qc.invalidateQueries({ queryKey: [COPILOT_LOGS_KEY, variables.tenant_id] });
      return result;
    },
  });
}

export function useCopilotLogs(tenantId: number) {
  return useQuery({
    queryKey: [COPILOT_LOGS_KEY, tenantId],
    queryFn: () =>
      apiGet<CopilotQueryLog[]>("/api/bff/admin/platform/ai/copilot/logs", {
        tenant_id: tenantId,
        limit: 50,
      }),
    enabled: tenantId > 0,
    staleTime: 15_000,
  });
}
