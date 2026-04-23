"use client";

import { useEffect, useState } from "react";
import { Settings2 } from "lucide-react";

import { useAdminAuth } from "@/shared/auth/context";
import { PERMISSIONS } from "@/shared/config/permissions";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { ConfirmActionDialog } from "@/shared/ui/confirm-action-dialog";
import { Label } from "@/shared/ui/label";
import { LoadingState } from "@/shared/ui/page-states";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { Switch } from "@/shared/ui/switch";
import { useToast } from "@/shared/ui/use-toast";
import { useBrainPolicyProfile, useUpdateBrainPolicyProfile } from "@/modules/brain-core/hooks";

const AUTONOMY_LEVELS = [
  { value: "0", label: "0 — Observe Only" },
  { value: "1", label: "1 — Recommend Only" },
  { value: "2", label: "2 — Semi-Autonomous (default)" },
  { value: "3", label: "3 — Autonomous" },
  { value: "4", label: "4 — Fully Autonomous" },
];

const APPROVAL_ROLES = [
  { value: "dean_office", label: "Dean's Office" },
  { value: "department_head", label: "Department Head" },
  { value: "academic_director", label: "Academic Director" },
  { value: "rector", label: "Rector" },
  { value: "admin", label: "System Admin" },
];

interface PolicyFormState {
  autonomy_level: string;
  require_approval_for_critical: boolean;
  default_approval_role: string;
  enable_ai_reasoning: boolean;
}

function PolicySettingsContent({ tenantId, actor }: { tenantId: number; actor: string }) {
  const { toast } = useToast();
  const profileQuery = useBrainPolicyProfile(tenantId);
  const update = useUpdateBrainPolicyProfile(tenantId);

  const profile = profileQuery.data;

  const [form, setForm] = useState<PolicyFormState>({
    autonomy_level: "2",
    require_approval_for_critical: true,
    default_approval_role: "dean_office",
    enable_ai_reasoning: false,
  });
  const [confirmOpen, setConfirmOpen] = useState(false);

  useEffect(() => {
    if (profile) {
      setForm({
        autonomy_level: String(profile.autonomy_level),
        require_approval_for_critical: profile.require_approval_for_critical,
        default_approval_role: profile.default_approval_role,
        enable_ai_reasoning: profile.enable_ai_reasoning,
      });
    }
  }, [profile]);

  if (profileQuery.isPending) return <LoadingState />;

  function handleSave() {
    update.mutate(
      {
        autonomy_level: Number(form.autonomy_level),
        require_approval_for_critical: form.require_approval_for_critical,
        default_approval_role: form.default_approval_role,
        enable_ai_reasoning: form.enable_ai_reasoning,
        actor,
      },
      {
        onSuccess: () => {
          toast({ title: "Policy updated", description: "Tenant policy profile saved." });
          setConfirmOpen(false);
        },
        onError: () => {
          toast({ title: "Update failed", description: "Could not save policy.", variant: "destructive" });
          setConfirmOpen(false);
        },
      },
    );
  }

  return (
    <div className="space-y-6 max-w-xl">
      <Card className="p-6 space-y-6">
        {/* Autonomy Level */}
        <div className="space-y-2">
          <Label htmlFor="autonomy-select">Autonomy Level</Label>
          <p className="text-xs text-muted-foreground">
            Controls how much the Brain Core acts without human approval.
          </p>
          <Select
            value={form.autonomy_level}
            onValueChange={(v) => setForm((f) => ({ ...f, autonomy_level: v }))}
          >
            <SelectTrigger id="autonomy-select" className="w-full">
              <SelectValue placeholder="Select level…" />
            </SelectTrigger>
            <SelectContent>
              {AUTONOMY_LEVELS.map((lvl) => (
                <SelectItem key={lvl.value} value={lvl.value}>
                  {lvl.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Require Approval for Critical */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="approval-switch">Require approval for critical decisions</Label>
            <p className="text-xs text-muted-foreground">
              If enabled, decisions with severity ≥ HIGH always require human approval regardless of autonomy level.
            </p>
          </div>
          <Switch
            id="approval-switch"
            checked={form.require_approval_for_critical}
            onCheckedChange={(v) => setForm((f) => ({ ...f, require_approval_for_critical: v }))}
          />
        </div>

        {/* Default Approval Role */}
        <div className="space-y-2">
          <Label htmlFor="role-select">Default approval role</Label>
          <p className="text-xs text-muted-foreground">
            Who receives approval requests when a decision requires human sign-off.
          </p>
          <Select
            value={form.default_approval_role}
            onValueChange={(v) => setForm((f) => ({ ...f, default_approval_role: v }))}
          >
            <SelectTrigger id="role-select" className="w-full">
              <SelectValue placeholder="Select role…" />
            </SelectTrigger>
            <SelectContent>
              {APPROVAL_ROLES.map((r) => (
                <SelectItem key={r.value} value={r.value}>
                  {r.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* AI Reasoning */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="ai-reasoning-switch">Enable AI reasoning (beta)</Label>
            <p className="text-xs text-muted-foreground">
              Uses an optional AI augmentation layer over rules-based reasoning with transparent trace output.
            </p>
          </div>
          <Switch
            id="ai-reasoning-switch"
            checked={form.enable_ai_reasoning}
            onCheckedChange={(v) => setForm((f) => ({ ...f, enable_ai_reasoning: v }))}
          />
        </div>

        <div className="flex justify-end pt-2">
          <Button onClick={() => setConfirmOpen(true)} disabled={update.isPending}>
            Save Policy
          </Button>
        </div>
      </Card>

      <ConfirmActionDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Update Policy Profile?"
        description={`This will change the autonomy level to ${form.autonomy_level} and update approval settings for tenant ${tenantId}. Active decisions will not be affected.`}
        onConfirm={handleSave}
        confirmLabel="Save"
        loading={update.isPending}
      />
    </div>
  );
}

export default function BrainPolicyPage() {
  const { user } = useAdminAuth();
  const tenantId = user?.tenantId ?? 0;
  const actor = user?.sub ?? "admin@brain";

  return (
    <RequirePermission permission={PERMISSIONS.DASHBOARD_READ}>
      <div className="space-y-6">
        <PageHeader
          icon={Settings2}
          title="Brain Core — Policy Settings"
          description="Configure decision autonomy and approval rules for this tenant."
        />
        <PolicySettingsContent tenantId={tenantId} actor={actor} />
      </div>
    </RequirePermission>
  );
}
