"use client"

import React, { useState } from "react"
import { useRouter } from "next/navigation"

import { PageHeader } from "@/shared/ui/page-header"
import { Card } from "@/shared/ui/card"
import { Button } from "@/shared/ui/button"
import { EmptyState } from "@/shared/ui/empty-state"
import { ErrorState } from "@/shared/ui/error-state"
import { Skeleton } from "@/shared/ui/skeleton"
import { useToast } from "@/shared/ui/use-toast"
import { RequirePermission } from "@/shared/ui/permission-gate"
import { 
  useAutomationTemplates, 
  useInstantiateTemplate 
} from "@/modules/platform/automation/templates/use-templates"
import { 
  getCategoryIcon, 
  TEMPLATE_CATEGORIES 
} from "@/modules/platform/automation/templates/types"
import { 
  summarizeCondition, 
  summarizeActions 
} from "@/modules/platform/automation/types"
import type { AutomationTemplate } from "@/modules/platform/automation/templates/types"
import { Zap, Loader2 } from "lucide-react"
import { useLanguage } from "@/app/components/LanguageProvider"

// Template Card Component
function TemplateCard({
  template,
  onInstantiate,
  isInstantiating,
  isActionDisabled,
  t,
}: {
  template: AutomationTemplate
  onInstantiate: (template: AutomationTemplate) => void
  isInstantiating: boolean
  isActionDisabled: boolean
  t: (key: never) => string
}) {
  return (
    <Card className="p-5 space-y-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg">{getCategoryIcon(template.category)}</span>
              <h3 className="font-semibold text-sm">{template.title}</h3>
            </div>
            {template.is_system_template && (
              <span className="text-xs text-muted-foreground mt-1">{t("automation.templates.systemTemplate" as never)}</span>
            )}
          </div>
        </div>
        <p className="text-xs text-muted-foreground line-clamp-2">
          {template.description}
        </p>
      </div>

      {/* Details */}
      <div className="space-y-2 text-xs">
        <div>
          <span className="font-medium">{t("automation.templates.eventLabel" as never)}:</span> {template.event_type}
        </div>

        {Object.keys(template.condition_json).length > 0 && (
          <div>
            <span className="font-medium">{t("automation.columns.condition" as never)}:</span>{" "}
            {summarizeCondition(template.condition_json)}
          </div>
        )}

        {template.actions_json.length > 0 && (
          <div>
            <span className="font-medium">{t("automation.columns.actions" as never)}:</span>{" "}
            {summarizeActions(template.actions_json)}
          </div>
        )}
      </div>

      {/* Action Button */}
      <Button
        onClick={() => onInstantiate(template)}
        disabled={isActionDisabled}
        className="w-full"
        size="sm"
      >
        {isInstantiating ? (
          <>
            <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" />
            {t("automation.templates.creating" as never)}
          </>
        ) : (
          t("automation.createRule" as never)
        )}
      </Button>
    </Card>
  )
}

// Main Templates Page
export default function AutomationTemplatesPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { t } = useLanguage()
  const [selectedTemplate, setSelectedTemplate] = useState<AutomationTemplate | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const { data: templates, isLoading, isFetching, error, refetch } = useAutomationTemplates()
  const instantiateMutation = useInstantiateTemplate()
  const isMutationBusy = instantiateMutation.isPending

  async function handleInstantiate(template: AutomationTemplate) {
    if (isMutationBusy) {
      return
    }
    setSelectedTemplate(template)
    try {
      const rule = await instantiateMutation.mutateAsync({
        template_key: template.template_key,
        request: {
          rule_name: template.title,
          rule_description: template.description,
        },
      })

      toast({
        title: t("automation.templates.ruleCreated"),
        description: t("automation.templates.ruleCreatedDescription")
          .replace("{rule}", rule.name)
          .replace("{template}", template.title),
      })

      // Redirect to new rule
      router.push(`/console/automation?highlight=${rule.id}`)
    } catch (err) {
      toast({
        title: t("automation.templates.createFailed"),
        description:
          err instanceof Error ? err.message : t("automation.templates.unexpectedError"),
        variant: "destructive",
      })
    } finally {
      setSelectedTemplate(null)
    }
  }

  const filteredTemplates = selectedCategory
    ? templates?.filter((t) => t.category === selectedCategory)
    : templates

  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader
          title={t("automation.templates.title")}
          description={t("automation.templates.shortDescription")}
          icon={Zap}
        />
        <ErrorState
          title={t("automation.templates.loadFailedTitle")}
          message={t("automation.templates.loadFailedMessage")}
          onRetry={() => void refetch()}
          retryLabel={t("state.retry" as never)}
          retrying={isFetching}
        />
      </div>
    )
  }

  return (
    <RequirePermission permission="automation.write">
      <div className="space-y-6">
        <PageHeader
          title={t("automation.templates.title")}
          description={t("automation.templates.description")}
          icon={Zap}
        />

        {/* Category Filter */}
        <div className="flex gap-2 flex-wrap">
          <Button
            variant={selectedCategory === null ? "default" : "outline"}
            size="sm"
            disabled={isMutationBusy}
            onClick={() => setSelectedCategory(null)}
          >
            {t("automation.templates.allTemplates")}
          </Button>
          {TEMPLATE_CATEGORIES.map((category) => (
            <Button
              key={category}
              variant={selectedCategory === category ? "default" : "outline"}
              size="sm"
              disabled={isMutationBusy}
              onClick={() => setSelectedCategory(category)}
            >
              {category}
            </Button>
          ))}
        </div>

        {/* Templates Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, index) => (
              <Card key={index} className="p-5 space-y-4">
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-4/5" />
                <Skeleton className="h-8 w-full" />
              </Card>
            ))}
          </div>
        ) : filteredTemplates && filteredTemplates.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTemplates.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                onInstantiate={handleInstantiate}
                t={t as never}
                isActionDisabled={isMutationBusy}
                isInstantiating={
                  isMutationBusy &&
                  selectedTemplate?.id === template.id
                }
              />
            ))}
          </div>
        ) : (
          <Card className="p-6">
            <EmptyState
              title={selectedCategory ? t("automation.templates.emptyByCategoryTitle") : t("automation.templates.emptyTitle")}
              description={
                selectedCategory
                  ? t("automation.templates.emptyByCategoryDescription").replace("{category}", selectedCategory)
                  : t("automation.templates.emptyDescription")
              }
            />
          </Card>
        )}

        {/* Back to Rules */}
        <div className="flex justify-end">
          <Button
            variant="outline"
            disabled={isMutationBusy}
            onClick={() => router.push("/console/automation")}
          >
            {t("automation.templates.backToRules")}
          </Button>
        </div>
      </div>
    </RequirePermission>
  )
}
