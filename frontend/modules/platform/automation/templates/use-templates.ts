// Automation Templates - React Query Hooks

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost } from "@/shared/api/client"
import type { AutomationRule } from "@/modules/platform/automation/types"
import type { AutomationTemplate, InstantiateTemplateRequest } from "./types"

export const AUTOMATION_TEMPLATES_KEY = "platform-automation-templates"

export function useAutomationTemplates() {
  return useQuery({
    queryKey: [AUTOMATION_TEMPLATES_KEY],
    queryFn: () =>
      apiGet<AutomationTemplate[]>("/api/v1/admin/platform/automation/templates"),
    staleTime: 60_000,
  })
}

export function useInstantiateTemplate() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({
      template_key,
      request,
    }: {
      template_key: string
      request: InstantiateTemplateRequest
    }) =>
      apiPost<AutomationRule>(
        `/api/v1/admin/platform/automation/templates/${template_key}/instantiate`,
        request
      ),
    onSuccess: () => {
      // Invalidate both templates and rules queries
      void qc.invalidateQueries({ queryKey: [AUTOMATION_TEMPLATES_KEY] })
      void qc.invalidateQueries({ queryKey: ["platform-automation-rules"] })
    },
  })
}
