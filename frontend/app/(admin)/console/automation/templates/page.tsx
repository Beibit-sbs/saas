"use client"

import React, { useState } from "react"
import { useRouter } from "next/navigation"

import { PageHeader } from "@/shared/ui/page-header"
import { Card } from "@/shared/ui/card"
import { Button } from "@/shared/ui/button"
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

// Template Card Component
function TemplateCard({
  template,
  onInstantiate,
  isInstantiating,
}: {
  template: AutomationTemplate
  onInstantiate: (template: AutomationTemplate) => void
  isInstantiating: boolean
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
              <span className="text-xs text-muted-foreground mt-1">System Template</span>
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
          <span className="font-medium">Event:</span> {template.event_type}
        </div>

        {Object.keys(template.condition_json).length > 0 && (
          <div>
            <span className="font-medium">Condition:</span>{" "}
            {summarizeCondition(template.condition_json)}
          </div>
        )}

        {template.actions_json.length > 0 && (
          <div>
            <span className="font-medium">Actions:</span>{" "}
            {summarizeActions(template.actions_json)}
          </div>
        )}
      </div>

      {/* Action Button */}
      <Button
        onClick={() => onInstantiate(template)}
        disabled={isInstantiating}
        className="w-full"
        size="sm"
      >
        {isInstantiating ? (
          <>
            <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" />
            Creating...
          </>
        ) : (
          "Create Rule"
        )}
      </Button>
    </Card>
  )
}

// Main Templates Page
export default function AutomationTemplatesPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [selectedTemplate, setSelectedTemplate] = useState<AutomationTemplate | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const { data: templates, isLoading, error } = useAutomationTemplates()
  const instantiateMutation = useInstantiateTemplate()

  async function handleInstantiate(template: AutomationTemplate) {
    try {
      const rule = await instantiateMutation.mutateAsync({
        template_key: template.template_key,
        request: {
          rule_name: template.title,
          rule_description: template.description,
        },
      })

      toast({
        title: "Rule created",
        description: `Created rule "${rule.name}" from template "${template.title}".`,
      })

      // Redirect to new rule
      router.push(`/console/automation?highlight=${rule.id}`)
    } catch (err) {
      toast({
        title: "Failed to create rule",
        description:
          err instanceof Error ? err.message : "An unexpected error occurred.",
        variant: "destructive",
      })
    }
  }

  const filteredTemplates = selectedCategory
    ? templates?.filter((t) => t.category === selectedCategory)
    : templates

  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Automation Templates"
          description="Create automation rules from predefined templates."
          icon={Zap}
        />
        <Card className="p-6">
          <p className="text-sm text-destructive">Failed to load templates.</p>
        </Card>
      </div>
    )
  }

  return (
    <RequirePermission permission="automation.write">
      <div className="space-y-6">
        <PageHeader
          title="Automation Templates"
          description="Create automation rules from predefined templates. Choose a template and customize it for your needs."
          icon={Zap}
        />

        {/* Category Filter */}
        <div className="flex gap-2 flex-wrap">
          <Button
            variant={selectedCategory === null ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedCategory(null)}
          >
            All Templates
          </Button>
          {TEMPLATE_CATEGORIES.map((category) => (
            <Button
              key={category}
              variant={selectedCategory === category ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(category)}
            >
              {category}
            </Button>
          ))}
        </div>

        {/* Templates Grid */}
        {isLoading ? (
          <Card className="p-12">
            <div className="flex items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          </Card>
        ) : filteredTemplates && filteredTemplates.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTemplates.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                onInstantiate={handleInstantiate}
                isInstantiating={
                  instantiateMutation.isPending &&
                  selectedTemplate?.id === template.id
                }
              />
            ))}
          </div>
        ) : (
          <Card className="p-12">
            <div className="text-center text-muted-foreground">
              {selectedCategory
                ? `No templates in the ${selectedCategory} category.`
                : "No templates available."}
            </div>
          </Card>
        )}

        {/* Back to Rules */}
        <div className="flex justify-end">
          <Button
            variant="outline"
            onClick={() => router.push("/console/automation")}
          >
            Back to Rules
          </Button>
        </div>
      </div>
    </RequirePermission>
  )
}
