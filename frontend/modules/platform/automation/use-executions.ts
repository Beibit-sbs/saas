import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import type { AutomationExecution } from "./types";

export const AUTOMATION_EXECUTIONS_KEY = "platform-automation-executions";

export function useAutomationExecutions(tenantId: number = 1) {
  return useQuery({
    queryKey: [AUTOMATION_EXECUTIONS_KEY, tenantId],
    queryFn: () =>
      apiGet<AutomationExecution[]>("/api/bff/admin/platform/automation/executions", {
        tenant_id: tenantId,
      }),
    enabled: tenantId > 0,
    staleTime: 15_000,
  });
}
