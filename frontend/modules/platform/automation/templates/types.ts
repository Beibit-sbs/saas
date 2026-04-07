// Automation Templates - Frontend Types

import type { AutomationAction } from "../types"

export interface AutomationTemplate {
  id: string
  template_key: string
  title: string
  description: string
  category: string
  event_type: string
  condition_json: Record<string, unknown>
  actions_json: AutomationAction[]
  is_system_template: boolean
  created_at: string
  updated_at: string
  version: number
}

export interface InstantiateTemplateRequest {
  rule_name?: string
  rule_description?: string
}

// Constants
export const TEMPLATE_CATEGORIES = [
  "Academic",
  "Onboarding",
  "Administration",
  "Finance",
  "Compliance",
] as const

export const TEMPLATE_CATEGORY_ICONS: Record<string, string> = {
  Academic: "📚",
  Onboarding: "👋",
  Administration: "⚙️",
  Finance: "💰",
  Compliance: "📋",
}

export function getCategoryIcon(category: string): string {
  return TEMPLATE_CATEGORY_ICONS[category] || "📦"
}
