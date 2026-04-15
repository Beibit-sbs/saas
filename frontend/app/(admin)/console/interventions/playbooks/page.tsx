"use client";

import { useState, useCallback } from "react";
import { Plus, BookOpen, Trash2, ToggleLeft, ToggleRight, ChevronDown, ChevronUp } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { DetailList } from "@/shared/ui/detail-list";
import { ErrorState } from "@/shared/ui/error-state";
import { PERMISSIONS } from "@/shared/config/permissions";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { formatRelative } from "@/shared/utils/format";
import { useLanguage } from "@/app/components/LanguageProvider";
import {
  usePlaybooks,
  useCreatePlaybook,
  useUpdatePlaybook,
  useDeletePlaybook,
} from "@/modules/platform/interventions/playbook-hooks";
import type {
  Playbook,
  PlaybookStep,
  PlaybookStepActionType,
  PlaybookAssigneeRole,
} from "@/modules/platform/interventions/playbook-types";

const ACTION_TYPE_LABELS: Record<PlaybookStepActionType, string> = {
  consultation_scheduled: "Consultation",
  notification_sent: "Notification",
  plan_updated: "Plan Update",
  advisor_meeting: "Advisor Meeting",
  escalation: "Escalation",
  resource_assigned: "Resource",
  note: "Note",
};

const ROLE_LABELS: Record<PlaybookAssigneeRole, string> = {
  advisor: "Advisor",
  registrar: "Registrar",
  program_manager: "Program Manager",
  dean: "Dean",
};

function StepList({ steps }: { steps: PlaybookStep[] }) {
  const sorted = [...steps].sort((a, b) => a.step_order - b.step_order);
  return (
    <ol className="space-y-2 mt-2">
      {sorted.map((s) => (
        <li key={s.id} className="flex items-start gap-3 text-sm">
          <span className="flex-none w-6 h-6 rounded-full bg-muted flex items-center justify-center text-xs font-medium">
            {s.step_order + 1}
          </span>
          <div className="flex-1 min-w-0">
            <p className="font-medium truncate">{s.title}</p>
            <p className="text-muted-foreground text-xs">
              {ACTION_TYPE_LABELS[s.action_type]} · {ROLE_LABELS[s.assignee_role]} · +{s.due_days_offset}d
              {s.is_mandatory && (
                <span className="ml-1 text-destructive">required</span>
              )}
            </p>
            {s.rationale && (
              <p className="text-muted-foreground text-xs mt-0.5 italic truncate">{s.rationale}</p>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}

interface CreateForm {
  name: string;
  description: string;
}

const EMPTY_FORM: CreateForm = { name: "", description: "" };

export default function PlaybooksPage() {
  const { t } = useLanguage();
  const { getHandlers } = useMutationFeedback();

  const { data, isLoading, isError } = usePlaybooks();
  const createPlaybook = useCreatePlaybook();
  const updatePlaybook = useUpdatePlaybook();
  const deletePlaybook = useDeletePlaybook();

  const [selectedPlaybook, setSelectedPlaybook] = useState<Playbook | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState<number | null>(null);
  const [form, setForm] = useState<CreateForm>(EMPTY_FORM);

  const handleCreate = useCallback(async () => {
    if (!form.name.trim()) return;
    createPlaybook.mutate(
      { name: form.name.trim(), description: form.description.trim() || null },
      {
        ...getHandlers({ successTitle: "Playbook created" }),
        onSuccess: () => {
          setShowCreate(false);
          setForm(EMPTY_FORM);
        },
      },
    );
  }, [form, createPlaybook, getHandlers]);

  const handleToggleEnabled = useCallback(
    (playbook: Playbook) => {
      updatePlaybook.mutate(
        {
          id: playbook.id,
          payload: { expected_version: playbook.version, enabled: !playbook.enabled },
        },
        getHandlers({
          successTitle: playbook.enabled ? "Playbook disabled" : "Playbook enabled",
        }),
      );
    },
    [updatePlaybook, getHandlers],
  );

  const handleDelete = useCallback(
    (playbook: Playbook) => {
      if (!confirm(`Delete playbook "${playbook.name}"?`)) return;
      deletePlaybook.mutate(playbook.id, getHandlers({ successTitle: "Playbook deleted" }));
    },
    [deletePlaybook, getHandlers],
  );

  const columns: Column<Playbook>[] = [
    {
      key: "name",
      header: "Name",
      cell: (p) => (
        <button
          className="font-medium text-left hover:underline"
          onClick={() => setSelectedPlaybook(p)}
        >
          {p.name}
        </button>
      ),
    },
    {
      key: "steps",
      header: "Steps",
      cell: (p) => (
        <button
          className="flex items-center gap-1 text-sm"
          onClick={() => setExpandedSteps(expandedSteps === p.id ? null : p.id)}
        >
          <span>{p.steps.length}</span>
          {expandedSteps === p.id ? (
            <ChevronUp className="h-3 w-3" />
          ) : (
            <ChevronDown className="h-3 w-3" />
          )}
        </button>
      ),
    },
    {
      key: "enabled",
      header: "Status",
      cell: (p) =>
        p.enabled ? (
          <Badge variant="success">Enabled</Badge>
        ) : (
          <Badge variant="secondary">Disabled</Badge>
        ),
    },
    {
      key: "updated_at",
      header: "Updated",
      cell: (p) => formatRelative(p.updated_at),
    },
    {
      key: "actions",
      header: "",
      cell: (p) => (
        <RequirePermission permission={PERMISSIONS.INTERVENTIONS_EXECUTE_PLAYBOOK}>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleToggleEnabled(p)}
              title={p.enabled ? "Disable" : "Enable"}
            >
              {p.enabled ? (
                <ToggleRight className="h-4 w-4 text-green-600" />
              ) : (
                <ToggleLeft className="h-4 w-4 text-muted-foreground" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleDelete(p)}
              title="Delete"
            >
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        </RequirePermission>
      ),
    },
  ];

  if (isError) return <ErrorState />;

  const items = data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        icon={BookOpen}
        title="Playbooks"
        description="Reusable multi-step intervention workflows"
        actions={
          <RequirePermission permission={PERMISSIONS.INTERVENTIONS_EXECUTE_PLAYBOOK}>
            <Button size="sm" onClick={() => setShowCreate(true)}>
              <Plus className="h-4 w-4 mr-1" />
              New Playbook
            </Button>
          </RequirePermission>
        }
      />

      <DataTable
        columns={columns}
        data={items}
        getRowKey={(row) => String(row.id)}
        isLoading={isLoading}
        emptyDescription="No playbooks yet. Create one to get started."
      />

      {/* Create drawer */}
      <DrawerPanel
        open={showCreate}
        onClose={() => {
          setShowCreate(false);
          setForm(EMPTY_FORM);
        }}
        title="New Playbook"
      >
        <div className="space-y-4 p-4">
          <div className="space-y-1">
            <Label htmlFor="playbook-name">Name *</Label>
            <Input
              id="playbook-name"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="e.g. Academic Risk Intervention"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="playbook-desc">Description</Label>
            <Input
              id="playbook-desc"
              value={form.description}
              onChange={(e) =>
                setForm((f) => ({ ...f, description: e.target.value }))
              }
              placeholder="Optional description"
            />
          </div>
          <Button
            onClick={handleCreate}
            disabled={!form.name.trim() || createPlaybook.isPending}
            className="w-full"
          >
            {createPlaybook.isPending ? "Creating…" : "Create Playbook"}
          </Button>
        </div>
      </DrawerPanel>

      {/* Detail drawer */}
      <DrawerPanel
        open={selectedPlaybook !== null}
        onClose={() => setSelectedPlaybook(null)}
        title={selectedPlaybook?.name ?? ""}
      >
        {selectedPlaybook && (
          <div className="space-y-4 p-4">
            <DetailList
              items={[
                { label: "ID", value: String(selectedPlaybook.id) },
                {
                  label: "Status",
                  value: selectedPlaybook.enabled ? "Enabled" : "Disabled",
                },
                {
                  label: "Trigger threshold",
                  value: selectedPlaybook.trigger_threshold_id
                    ? String(selectedPlaybook.trigger_threshold_id)
                    : "—",
                },
                { label: "Version", value: String(selectedPlaybook.version) },
                {
                  label: "Created by",
                  value: selectedPlaybook.created_by,
                },
                {
                  label: "Updated",
                  value: formatRelative(selectedPlaybook.updated_at),
                },
              ]}
            />
            <div>
              <p className="text-sm font-medium mb-1">
                Steps ({selectedPlaybook.steps.length})
              </p>
              <StepList steps={selectedPlaybook.steps} />
            </div>
          </div>
        )}
      </DrawerPanel>
    </div>
  );
}
