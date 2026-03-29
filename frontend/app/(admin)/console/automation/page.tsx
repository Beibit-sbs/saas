"use client";

import { useState, useCallback } from "react";
import { Bot, Plus } from "lucide-react";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { ConfirmActionDialog } from "@/shared/ui/confirm-action-dialog";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { PageHeader } from "@/shared/ui/page-header";
import { PermissionGate, RequirePermission } from "@/shared/ui/permission-gate";
import { Switch } from "@/shared/ui/switch";
import { useToast } from "@/shared/ui/use-toast";
import { PERMISSIONS } from "@/shared/config/permissions";
import { formatDate } from "@/shared/utils/format";
import { useAdminAuth } from "@/shared/auth/context";

import { CreateRuleDialog } from "@/modules/platform/automation/create-rule-dialog";
import { useAutomationRules, useUpdateAutomationRule } from "@/modules/platform/automation/use-rules";
import {
  summarizeActions,
  summarizeCondition,
  type AutomationRule,
} from "@/modules/platform/automation/types";

// ---------------------------------------------------------------------------
// Rule Row State (for optimistic updates + toggle dialogs)
// ---------------------------------------------------------------------------

interface RuleRowState {
  rule_id: number;
  toggling: boolean;
  dialogOpen: boolean;
  optimisticActive: boolean | null;
}

// ---------------------------------------------------------------------------
// Columns Factory (needs state + mutation for toggle behavior)
// ---------------------------------------------------------------------------

function createColumns(
  onToggleClick: (rule: AutomationRule) => void,
  togglingRuleIds: Set<number>,
  hasWrite: boolean,
): Column<AutomationRule>[] {
  return [
    {
      key: "name",
      header: "Name",
      cell: (row) => (
        <div>
          <div className="font-medium">{row.name}</div>
          {row.description && (
            <div className="text-xs text-muted-foreground mt-0.5 max-w-xs truncate">
              {row.description}
            </div>
          )}
        </div>
      ),
      sortValue: (row) => row.name,
    },
    {
      key: "event_type",
      header: "Event Type",
      width: "160px",
      cell: (row) => (
        <Badge variant="outline" className="font-mono text-xs">
          {row.event_type}
        </Badge>
      ),
      sortValue: (row) => row.event_type,
    },
    {
      key: "condition",
      header: "Condition",
      width: "180px",
      cell: (row) => (
        <span className="font-mono text-xs text-muted-foreground">
          {summarizeCondition(row.condition_json)}
        </span>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      width: "200px",
      cell: (row) => (
        <span className="text-xs text-muted-foreground">{summarizeActions(row.actions_json)}</span>
      ),
    },
    {
      key: "is_active",
      header: "Active",
      width: "100px",
      cell: (row) => (
        <Switch
          checked={row.is_active}
          onCheckedChange={() => onToggleClick(row)}
          disabled={!hasWrite || togglingRuleIds.has(row.id)}
          data-testid={`toggle-rule-${row.id}`}
        />
      ),
    },
    {
      key: "updated_at",
      header: "Updated At",
      width: "160px",
      cell: (row) => (
        <span className="text-xs text-muted-foreground">{formatDate(row.updated_at)}</span>
      ),
      sortValue: (row) => row.updated_at,
    },
  ];
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AutomationRulesPage() {
  const { user } = useAdminAuth();
  const tenantId = user?.tenantId ?? 0;
  const { data, isLoading, isError, refetch } = useAutomationRules(tenantId);
  const { toast } = useToast();
  const updateRule = useUpdateAutomationRule();

  const [createOpen, setCreateOpen] = useState(false);
  const [rowStates, setRowStates] = useState<Map<number, RuleRowState>>(new Map());

  // Get the write permission check
  const hasWrite =
    typeof window !== "undefined"
      ? JSON.parse(localStorage.getItem("user_permissions") || "[]").includes(
          PERMISSIONS.AUTOMATION_WRITE,
        )
      : false;

  const getRowState = useCallback((ruleId: number): RuleRowState => {
    return (
      rowStates.get(ruleId) ?? {
        rule_id: ruleId,
        toggling: false,
        dialogOpen: false,
        optimisticActive: null,
      }
    );
  }, [rowStates]);

  const updateRowState = useCallback((ruleId: number, updates: Partial<RuleRowState>) => {
    setRowStates((prev) => {
      const newMap = new Map(prev);
      const current = newMap.get(ruleId) || {
        rule_id: ruleId,
        toggling: false,
        dialogOpen: false,
        optimisticActive: null,
      };
      newMap.set(ruleId, { ...current, ...updates });
      return newMap;
    });
  }, []);

  const handleToggleClick = useCallback((rule: AutomationRule) => {
    updateRowState(rule.id, { dialogOpen: true });
  }, [updateRowState]);

  const handleConfirmToggle = useCallback(
    async (rule: AutomationRule) => {
      const newActive = !rule.is_active;

      // Optimistic update
      updateRowState(rule.id, {
        toggling: true,
        optimisticActive: newActive,
        dialogOpen: false,
      });

      try {
        await updateRule.mutateAsync({
          id: rule.id,
          is_active: newActive,
        });

        toast({
          variant: "success",
          title: newActive ? "Rule activated" : "Rule deactivated",
        });

        // Clear optimistic state
        updateRowState(rule.id, { toggling: false, optimisticActive: null });
      } catch {
        // Rollback optimistic update
        updateRowState(rule.id, { toggling: false, optimisticActive: null });

        toast({
          variant: "destructive",
          title: "Failed to update rule",
        });
      }
    },
    [updateRule, toast, updateRowState],
  );

  const togglingRuleIds = new Set(
    Array.from(rowStates.entries())
      .filter(([, state]) => state.toggling)
      .map(([id]) => id),
  );

  const columns = createColumns(handleToggleClick, togglingRuleIds, hasWrite);

  return (
    <RequirePermission
      permission={PERMISSIONS.AUTOMATION_READ}
      message="You need automation.read permission to view automation rules."
    >
      <div className="space-y-6" data-testid="automation-rules-page">
        <PageHeader
          title="Automation Rules"
          description="Manage event-driven rules that trigger automated actions."
          icon={Bot}
          actions={
            <PermissionGate permission={PERMISSIONS.AUTOMATION_WRITE}>
              <Button size="sm" onClick={() => setCreateOpen(true)} data-testid="create-rule-btn">
                <Plus className="mr-2 h-4 w-4" />
                Create Rule
              </Button>
            </PermissionGate>
          }
        />

        {isError && !isLoading && (
          <ErrorState
            title="Failed to load automation rules"
            message="Could not fetch automation rules."
            onRetry={() => void refetch()}
          />
        )}

        {!isError && (
          <DataTable
            columns={columns}
            data={data ?? []}
            isLoading={isLoading}
            getRowKey={(row) => String(row.id)}
            emptyTitle="No automation rules"
            emptyDescription="Create your first rule to start automating event-driven workflows."
            emptyAction={
              <PermissionGate permission={PERMISSIONS.AUTOMATION_WRITE}>
                <Button size="sm" variant="outline" onClick={() => setCreateOpen(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Rule
                </Button>
              </PermissionGate>
            }
          />
        )}

        {/* Toggle Confirm Dialogs */}
        {data?.map((rule) => {
          const state = getRowState(rule.id);
          return (
            <ConfirmActionDialog
              key={`toggle-dialog-${rule.id}`}
              open={state.dialogOpen}
              onOpenChange={(open) => updateRowState(rule.id, { dialogOpen: open })}
              title="Change rule status?"
              confirmLabel={!rule.is_active ? "Activate" : "Deactivate"}
              onConfirm={() => handleConfirmToggle(rule)}
              loading={state.toggling}
              data-testid={`confirm-toggle-${rule.id}`}
            />
          );
        })}

        <PermissionGate permission={PERMISSIONS.AUTOMATION_WRITE}>
          <CreateRuleDialog
            open={createOpen}
            onClose={() => setCreateOpen(false)}
            tenantId={tenantId}
          />
        </PermissionGate>
      </div>
    </RequirePermission>
  );
}
