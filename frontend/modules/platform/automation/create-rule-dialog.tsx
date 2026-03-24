"use client";

import { useFieldArray, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, Plus, Trash2 } from "lucide-react";

import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { DrawerPanel } from "@/shared/ui/drawer-panel";

import { useCreateAutomationRule } from "./create-rule";
import {
  AUTOMATION_ACTION_TYPES,
  AUTOMATION_OPERATORS,
  KNOWN_EVENT_TYPES,
  type AutomationAction,
  type AutomationCondition,
} from "./types";

// ---------------------------------------------------------------------------
// Form schema
// ---------------------------------------------------------------------------

const actionItemSchema = z.object({
  type: z.enum(["send_notification", "create_task", "emit_event"]),
  // send_notification fields
  channel: z.string().default("in_app"),
  template: z.string().default(""),
  // create_task fields
  job_type: z.string().default(""),
  max_retries: z.coerce.number().min(0).max(10).default(3),
  // emit_event fields
  new_event_type: z.string().default(""),
  aggregate_type: z.string().default(""),
});

const ruleFormSchema = z.object({
  name: z.string().min(1, "Name is required").max(255),
  description: z.string().default(""),
  event_type: z.string().min(1, "Event type is required"),
  // condition (optional — leave field empty to create unconditional rule)
  condition_field: z.string().default(""),
  condition_operator: z.enum(["==", "!=", ">", "<", ">=", "<="]).default("<"),
  condition_value: z.string().default(""),
  // actions list
  actions: z.array(actionItemSchema).default([]),
});

type RuleFormValues = z.infer<typeof ruleFormSchema>;

// ---------------------------------------------------------------------------
// Transform form values → API payload
// ---------------------------------------------------------------------------

function buildConditionPayload(
  field: string,
  operator: RuleFormValues["condition_operator"],
  value: string,
): AutomationCondition | Record<string, never> {
  if (!field.trim()) return {};
  const numericValue = Number(value);
  return {
    field: field.trim(),
    operator,
    value: !isNaN(numericValue) && value.trim() !== "" ? numericValue : value.trim(),
  };
}

function buildActionPayload(item: RuleFormValues["actions"][number]): AutomationAction {
  switch (item.type) {
    case "send_notification":
      return { type: "send_notification", channel: item.channel, template: item.template };
    case "create_task":
      return { type: "create_task", job_type: item.job_type, max_retries: item.max_retries };
    case "emit_event":
      return { type: "emit_event", event_type: item.new_event_type, aggregate_type: item.aggregate_type };
  }
}

// ---------------------------------------------------------------------------
// Action row — type-specific fields
// ---------------------------------------------------------------------------

type ActionItemProps = {
  index: number;
  register: ReturnType<typeof useForm<RuleFormValues>>["register"];
  watch: ReturnType<typeof useForm<RuleFormValues>>["watch"];
  setValue: ReturnType<typeof useForm<RuleFormValues>>["setValue"];
  onRemove: () => void;
};

function ActionRow({ index, register, watch, setValue, onRemove }: ActionItemProps) {
  const actionType = watch(`actions.${index}.type`);

  return (
    <div className="rounded-md border bg-muted/30 p-3 space-y-3" data-testid="action-row">
      <div className="flex items-center justify-between">
        <Label className="text-xs uppercase tracking-wide text-muted-foreground">Action {index + 1}</Label>
        <Button type="button" variant="ghost" size="icon" className="h-7 w-7" onClick={onRemove}>
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>

      <div className="space-y-1">
        <Label htmlFor={`action-type-${index}`} className="text-xs">Type</Label>
        <Select
          value={actionType}
          onValueChange={(v) => setValue(`actions.${index}.type`, v as RuleFormValues["actions"][number]["type"])}
        >
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
      </div>

      {actionType === "send_notification" && (
        <>
          <div className="space-y-1">
            <Label htmlFor={`action-channel-${index}`} className="text-xs">Channel</Label>
            <Select
              value={watch(`actions.${index}.channel`) || "in_app"}
              onValueChange={(v) => setValue(`actions.${index}.channel`, v)}
            >
              <SelectTrigger id={`action-channel-${index}`} className="h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="in_app">In-App</SelectItem>
                <SelectItem value="email">Email</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label htmlFor={`action-template-${index}`} className="text-xs">Template</Label>
            <Input
              id={`action-template-${index}`}
              placeholder="e.g. student_risk"
              className="h-9"
              {...register(`actions.${index}.template`)}
            />
          </div>
        </>
      )}

      {actionType === "create_task" && (
        <>
          <div className="space-y-1">
            <Label htmlFor={`action-jobtype-${index}`} className="text-xs">Job Type</Label>
            <Input
              id={`action-jobtype-${index}`}
              placeholder="e.g. remediation_review"
              className="h-9"
              {...register(`actions.${index}.job_type`)}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor={`action-retries-${index}`} className="text-xs">Max Retries</Label>
            <Input
              id={`action-retries-${index}`}
              type="number"
              min={0}
              max={10}
              className="h-9"
              {...register(`actions.${index}.max_retries`)}
            />
          </div>
        </>
      )}

      {actionType === "emit_event" && (
        <>
          <div className="space-y-1">
            <Label htmlFor={`action-evtype-${index}`} className="text-xs">Event Type</Label>
            <Input
              id={`action-evtype-${index}`}
              placeholder="e.g. academic_alert.created"
              className="h-9"
              {...register(`actions.${index}.new_event_type`)}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor={`action-aggtype-${index}`} className="text-xs">Aggregate Type</Label>
            <Input
              id={`action-aggtype-${index}`}
              placeholder="e.g. academic_alert"
              className="h-9"
              {...register(`actions.${index}.aggregate_type`)}
            />
          </div>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main dialog component
// ---------------------------------------------------------------------------

interface CreateRuleDialogProps {
  open: boolean;
  onClose: () => void;
  tenantId: number;
}

export function CreateRuleDialog({ open, onClose, tenantId }: CreateRuleDialogProps) {
  const { mutateAsync, isPending } = useCreateAutomationRule();

  const form = useForm<RuleFormValues>({
    resolver: zodResolver(ruleFormSchema),
    defaultValues: {
      name: "",
      description: "",
      event_type: "",
      condition_field: "",
      condition_operator: "<",
      condition_value: "",
      actions: [],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "actions",
  });

  function handleClose() {
    if (!isPending) {
      form.reset();
      onClose();
    }
  }

  async function onSubmit(values: RuleFormValues) {
    const conditionPayload = buildConditionPayload(
      values.condition_field,
      values.condition_operator,
      values.condition_value,
    );
    const actionsPayload = values.actions.map(buildActionPayload);

    await mutateAsync({
      tenant_id: tenantId,
      name: values.name,
      description: values.description,
      event_type: values.event_type,
      condition_json: conditionPayload,
      actions_json: actionsPayload,
      is_active: true,
    });

    form.reset();
    onClose();
  }

  return (
    <DrawerPanel
      open={open}
      onClose={handleClose}
      title="Create Automation Rule"
      description="Define an event trigger, optional condition, and a list of actions to execute."
      width="lg"
    >
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6" data-testid="create-rule-form">
        {/* Rule Info */}
        <section className="space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Rule Info</h3>

          <div className="space-y-1">
            <Label htmlFor="rule-name">Name *</Label>
            <Input
              id="rule-name"
              placeholder="e.g. Low Grade Academic Alert"
              {...form.register("name")}
            />
            {form.formState.errors.name && (
              <p className="text-xs text-destructive">{form.formState.errors.name.message}</p>
            )}
          </div>

          <div className="space-y-1">
            <Label htmlFor="rule-description">Description</Label>
            <textarea
              id="rule-description"
              rows={2}
              placeholder="Optional description…"
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
              {...form.register("description")}
            />
          </div>

          <div className="space-y-1">
            <Label htmlFor="rule-event-type">Trigger Event *</Label>
            <Select
              value={form.watch("event_type")}
              onValueChange={(v) => form.setValue("event_type", v)}
            >
              <SelectTrigger id="rule-event-type">
                <SelectValue placeholder="Select event type…" />
              </SelectTrigger>
              <SelectContent>
                {KNOWN_EVENT_TYPES.map((et) => (
                  <SelectItem key={et} value={et}>
                    {et}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {form.formState.errors.event_type && (
              <p className="text-xs text-destructive">{form.formState.errors.event_type.message}</p>
            )}
          </div>
        </section>

        {/* Condition Builder */}
        <section className="space-y-3">
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Condition</h3>
            <p className="text-xs text-muted-foreground mt-0.5">Leave field empty for unconditional (always fires).</p>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div className="space-y-1">
              <Label htmlFor="cond-field" className="text-xs">Field</Label>
              <Input
                id="cond-field"
                placeholder="grade_points"
                className="h-9"
                {...form.register("condition_field")}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="cond-operator" className="text-xs">Operator</Label>
              <Select
                value={form.watch("condition_operator")}
                onValueChange={(v) => form.setValue("condition_operator", v as RuleFormValues["condition_operator"])}
              >
                <SelectTrigger id="cond-operator" className="h-9">
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
            </div>
            <div className="space-y-1">
              <Label htmlFor="cond-value" className="text-xs">Value</Label>
              <Input
                id="cond-value"
                placeholder="50"
                className="h-9"
                {...form.register("condition_value")}
              />
            </div>
          </div>
        </section>

        {/* Actions */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Actions ({fields.length})
            </h3>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                append({
                  type: "send_notification",
                  channel: "in_app",
                  template: "",
                  job_type: "",
                  max_retries: 3,
                  new_event_type: "",
                  aggregate_type: "",
                })
              }
            >
              <Plus className="mr-1.5 h-3.5 w-3.5" />
              Add Action
            </Button>
          </div>

          {fields.length === 0 && (
            <p className="text-xs text-muted-foreground italic">No actions yet — add at least one action.</p>
          )}

          {fields.map((field, index) => (
            <ActionRow
              key={field.id}
              index={index}
              register={form.register}
              watch={form.watch}
              setValue={form.setValue}
              onRemove={() => remove(index)}
            />
          ))}
        </section>

        {/* Submit */}
        <div className="flex justify-end gap-2 pt-2 border-t">
          <Button type="button" variant="outline" onClick={handleClose} disabled={isPending}>
            Cancel
          </Button>
          <Button type="submit" disabled={isPending}>
            {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isPending ? "Creating…" : "Create Rule"}
          </Button>
        </div>
      </form>
    </DrawerPanel>
  );
}
