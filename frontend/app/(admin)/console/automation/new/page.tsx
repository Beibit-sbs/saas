"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, useFieldArray, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Trash2, Plus, Zap } from "lucide-react";

import { PageHeader } from "@/shared/ui/page-header";
import { Card } from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/shared/ui/select";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { useToast } from "@/shared/ui/use-toast";
import { useCreateAutomationRule } from "@/modules/platform/automation/create-rule";
import {
  KNOWN_EVENT_TYPES,
  AUTOMATION_OPERATORS,
  AUTOMATION_ACTION_TYPES,
} from "@/modules/platform/automation/types";
import type {
  AutomationCondition,
  AutomationAction,
  CreateAutomationRuleRequest,
} from "@/modules/platform/automation/types";

// Zod schema for the form
const ruleFormSchema = z.object({
  name: z.string().min(1, "Name is required").max(255),
  description: z.string().default(""),
  event_type: z.string().min(1, "Event type is required"),
  condition_field: z.string().default(""),
  condition_operator: z
    .enum(["==", "!=", ">", "<", ">=", "<="])
    .default("=="),
  condition_value: z.string().default(""),
  actions: z.array(
    z.discriminatedUnion("type", [
      z.object({
        type: z.literal("send_notification"),
        channel: z.string().default("in_app"),
        template: z.string().default(""),
      }),
      z.object({
        type: z.literal("create_task"),
        job_type: z.string().default(""),
        max_retries: z.coerce.number().min(0).max(10).default(3),
      }),
      z.object({
        type: z.literal("emit_event"),
        new_event_type: z.string().default(""),
        aggregate_type: z.string().default(""),
      }),
    ])
  ),
  is_active: z.boolean().default(true),
});

type RuleFormValues = z.infer<typeof ruleFormSchema>;

// Helper to build condition_json from form values
function buildConditionJson(
  field: string,
  operator: string,
  value: string
): AutomationCondition | Record<string, unknown> {
  if (!field || !value) {
    return {}; // Empty condition = always match
  }

  // Try to parse value as number if it looks numeric
  const numValue = !isNaN(Number(value)) ? Number(value) : value;

  return {
    field,
    operator: operator as "==" | "!=" | ">" | "<" | ">=" | "<=",
    value: numValue,
  };
}

// Helper to transform form actions to AutomationAction[]
function buildActionsPayload(formActions: RuleFormValues["actions"]) {
  return formActions.map((action) => {
    switch (action.type) {
      case "send_notification":
        return {
          type: "send_notification" as const,
          channel: action.channel,
          template: action.template,
        };
      case "create_task":
        return {
          type: "create_task" as const,
          job_type: action.job_type,
          max_retries: action.max_retries,
        };
      case "emit_event":
        return {
          type: "emit_event" as const,
          event_type: action.new_event_type,
          aggregate_type: action.aggregate_type,
        };
      default:
        return action;
    }
  });
}

// Action row component for dynamic actions
function ActionRow({
  index,
  onRemove,
  watch,
  control,
  register,
  setValue,
}: {
  index: number;
  onRemove: () => void;
  watch: (path: string) => string;
  control: any;
  register: any;
  setValue: any;
}) {
  const actionType = watch(`actions.${index}.type`);

  return (
    <div className="rounded-md border bg-muted/30 p-3 space-y-3">
      <div className="flex items-center justify-between">
        <Label className="text-xs uppercase font-semibold">
          Action {index + 1}
        </Label>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onRemove}
          className="h-7 w-7"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Action Type Selector */}
      <Controller
        control={control}
        name={`actions.${index}.type`}
        render={({ field }) => (
          <Select value={field.value} onValueChange={field.onChange}>
            <SelectTrigger id={`action-type-${index}`} className="h-9">
              <SelectValue placeholder="Select action type" />
            </SelectTrigger>
            <SelectContent>
              {AUTOMATION_ACTION_TYPES.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      />

      {/* Conditional Fields by Action Type */}
      {actionType === "send_notification" && (
        <>
          <Controller
            control={control}
            name={`actions.${index}.channel`}
            render={({ field }) => (
              <Select
                value={field.value || "in_app"}
                onValueChange={field.onChange}
              >
                <SelectTrigger className="h-9">
                  <SelectValue placeholder="Select channel" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="in_app">In-App</SelectItem>
                  <SelectItem value="email">Email</SelectItem>
                </SelectContent>
              </Select>
            )}
          />
          <Input
            placeholder="Template name (e.g., student_risk)"
            {...register(`actions.${index}.template`)}
            className="h-9"
          />
        </>
      )}

      {actionType === "create_task" && (
        <>
          <Input
            placeholder="Job type (e.g., remediation_review)"
            {...register(`actions.${index}.job_type`)}
            className="h-9"
          />
          <div className="grid grid-cols-4 gap-2">
            <div className="col-span-1">
              <Label htmlFor={`max-retries-${index}`} className="text-xs">
                Retries
              </Label>
            </div>
            <div className="col-span-1">
              <Input
                id={`max-retries-${index}`}
                type="number"
                min={0}
                max={10}
                {...register(`actions.${index}.max_retries`)}
                className="h-9"
              />
            </div>
          </div>
        </>
      )}

      {actionType === "emit_event" && (
        <>
          <Input
            placeholder="Event type (e.g., student_flagged)"
            {...register(`actions.${index}.new_event_type`)}
            className="h-9"
          />
          <Input
            placeholder="Aggregate type (e.g., student)"
            {...register(`actions.${index}.aggregate_type`)}
            className="h-9"
          />
        </>
      )}
    </div>
  );
}

// Main page component
export default function AutomationRuleNewPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [submitting, setSubmitting] = useState(false);

  const createRuleMutation = useCreateAutomationRule();

  const form = useForm<RuleFormValues>({
    resolver: zodResolver(ruleFormSchema),
    defaultValues: {
      name: "",
      description: "",
      event_type: "",
      condition_field: "",
      condition_operator: "==",
      condition_value: "",
      actions: [],
      is_active: true,
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "actions",
  });

  // Compute JSON preview
  const jsonPreview = {
    name: form.watch("name") || "(untitled)",
    description: form.watch("description") || "",
    event_type: form.watch("event_type") || "",
    condition_json: buildConditionJson(
      form.watch("condition_field"),
      form.watch("condition_operator"),
      form.watch("condition_value")
    ),
    actions_json: buildActionsPayload(form.watch("actions")),
    is_active: form.watch("is_active"),
  };

  async function onSubmit(values: RuleFormValues) {
    try {
      setSubmitting(true);

      const payload: CreateAutomationRuleRequest = {
        tenant_id: 1,
        name: values.name,
        description: values.description,
        event_type: values.event_type,
        condition_json: buildConditionJson(
          values.condition_field,
          values.condition_operator,
          values.condition_value
        ),
        actions_json: buildActionsPayload(values.actions),
        is_active: values.is_active,
      };

      await createRuleMutation.mutateAsync(payload);

      toast({
        title: "Rule created",
        description: `"${values.name}" has been created successfully.`,
      });

      router.push("/console/automation");
    } catch (error) {
      toast({
        title: "Failed to create rule",
        description:
          error instanceof Error
            ? error.message
            : "An unexpected error occurred.",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <RequirePermission permission="automation.write">
      <div className="space-y-6">
        <PageHeader
          title="Create Automation Rule"
          description="Build a new automation rule by defining an event type, optional condition, and actions."
          icon={Zap}
        />

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Form Card */}
            <div className="lg:col-span-2 space-y-6">
              {/* Basic Info */}
              <Card className="p-6 space-y-4">
                <h2 className="font-semibold text-sm">Rule Details</h2>

                <div>
                  <Label htmlFor="rule-name">Rule Name *</Label>
                  <Input
                    id="rule-name"
                    placeholder="e.g., Flag High-Risk Students"
                    {...form.register("name")}
                    className="mt-1"
                  />
                  {form.formState.errors.name && (
                    <p className="text-xs text-destructive mt-1">
                      {form.formState.errors.name.message}
                    </p>
                  )}
                </div>

                <div>
                  <Label htmlFor="rule-description">Description</Label>
                  <Input
                    id="rule-description"
                    placeholder="Describe what this rule does..."
                    {...form.register("description")}
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label htmlFor="rule-event-type">Event Type *</Label>
                  <Controller
                    control={form.control}
                    name="event_type"
                    render={({ field }) => (
                      <Select
                        value={field.value || ""}
                        onValueChange={field.onChange}
                      >
                        <SelectTrigger
                          id="rule-event-type"
                          className="mt-1 h-9"
                        >
                          <SelectValue placeholder="Select event type" />
                        </SelectTrigger>
                        <SelectContent>
                          {KNOWN_EVENT_TYPES.map((et) => (
                            <SelectItem key={et} value={et}>
                              {et}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                  {form.formState.errors.event_type && (
                    <p className="text-xs text-destructive mt-1">
                      {form.formState.errors.event_type.message}
                    </p>
                  )}
                </div>
              </Card>

              {/* Condition Builder */}
              <Card className="p-6 space-y-4">
                <h2 className="font-semibold text-sm">
                  Condition (Optional)
                </h2>
                <p className="text-xs text-muted-foreground">
                  Leave blank to match any event. Otherwise, rule only triggers
                  when condition is true.
                </p>

                <div className="grid grid-cols-1 gap-3">
                  <div>
                    <Label htmlFor="condition-field" className="text-xs">
                      Field
                    </Label>
                    <Input
                      id="condition-field"
                      placeholder="e.g., gpa"
                      {...form.register("condition_field")}
                      className="mt-1 h-9"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label htmlFor="condition-operator" className="text-xs">
                        Operator
                      </Label>
                      <Controller
                        control={form.control}
                        name="condition_operator"
                        render={({ field }) => (
                          <Select
                            value={field.value || "=="}
                            onValueChange={field.onChange}
                          >
                            <SelectTrigger
                              id="condition-operator"
                              className="mt-1 h-9"
                            >
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {AUTOMATION_OPERATORS.map((op) => (
                                <SelectItem key={op.value} value={op.value}>
                                  {op.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </div>

                    <div>
                      <Label htmlFor="condition-value" className="text-xs">
                        Value
                      </Label>
                      <Input
                        id="condition-value"
                        placeholder="e.g., 3.5"
                        {...form.register("condition_value")}
                        className="mt-1 h-9"
                      />
                    </div>
                  </div>
                </div>
              </Card>

              {/* Actions Builder */}
              <Card className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="font-semibold text-sm">Actions</h2>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      append({
                        type: "send_notification",
                        channel: "in_app",
                        template: "",
                      })
                    }
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Action
                  </Button>
                </div>

                {fields.length === 0 ? (
                  <p className="text-xs text-muted-foreground italic">
                    No actions defined yet. Click &quot;Add Action&quot; to get started.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {fields.map((field, index) => (
                      <ActionRow
                        key={field.id}
                        index={index}
                        onRemove={() => remove(index)}
                        watch={form.watch}
                        control={form.control}
                        register={form.register}
                        setValue={form.setValue}
                      />
                    ))}
                  </div>
                )}
              </Card>
            </div>

            {/* JSON Preview Card (Sidebar) */}
            <div className="lg:col-span-1">
              <Card className="p-4 sticky top-6 space-y-3">
                <h2 className="font-semibold text-sm">JSON Preview</h2>
                <div className="bg-muted rounded p-3 font-mono text-xs whitespace-pre-wrap overflow-auto max-h-96">
                  {JSON.stringify(jsonPreview, null, 2)}
                </div>
              </Card>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex gap-2 justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => router.push("/console/automation")}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={submitting || !form.formState.isValid}
            >
              {submitting ? "Creating..." : "Create Rule"}
            </Button>
          </div>
        </form>
      </div>
    </RequirePermission>
  );
}
