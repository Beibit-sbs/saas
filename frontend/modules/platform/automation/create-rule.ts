import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiPost } from "@/shared/api/client";
import type { AutomationRule, CreateAutomationRuleRequest } from "./types";
import { AUTOMATION_RULES_KEY } from "./use-rules";

export function useCreateAutomationRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateAutomationRuleRequest) =>
      apiPost<AutomationRule>("/api/bff/admin/platform/automation/rules", data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [AUTOMATION_RULES_KEY] });
    },
  });
}
