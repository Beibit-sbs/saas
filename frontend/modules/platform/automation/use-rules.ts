import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch } from "@/shared/api/client";
import type { AutomationRule } from "./types";

export const AUTOMATION_RULES_KEY = "platform-automation-rules";

export function useAutomationRules(tenantId: number) {
  return useQuery({
    queryKey: [AUTOMATION_RULES_KEY, tenantId],
    queryFn: () =>
      apiGet<AutomationRule[]>("/api/bff/admin/platform/automation/rules", {
        tenant_id: tenantId,
      }),
    enabled: tenantId > 0,
    staleTime: 30_000,
  });
}

export function useUpdateAutomationRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      apiPatch<AutomationRule>("/api/bff/admin/platform/automation/rules/" + id, {
        is_active,
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [AUTOMATION_RULES_KEY] });
    },
  });
}
