"use client";

import { PageHeader } from "@/shared/ui/page-header";
import { Switch } from "@/shared/ui/switch";
import { Skeleton } from "@/shared/ui/skeleton";
import { ErrorState } from "@/shared/ui/error-state";
import { useFeatureFlags, useUpdateFeatureFlag } from "@/modules/platform/feature-flags/hooks";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { PERMISSIONS } from "@/shared/config/permissions";
import { formatDate } from "@/shared/utils/format";
import { ToggleLeft } from "lucide-react";

export default function FeatureFlagsPage() {
  const { data: flags, isLoading, error, refetch } = useFeatureFlags();
  const update = useUpdateFeatureFlag();
  const { hasPermission } = usePermissions();
  const { getHandlers } = useMutationFeedback();
  const canWrite = hasPermission(PERMISSIONS.FEATURE_FLAGS_WRITE);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <PageHeader title="Feature Flags" icon={ToggleLeft} />
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-16 rounded-lg" />
        ))}
      </div>
    );
  }

  if (error) {
    return <ErrorState title="Failed to load flags" onRetry={refetch} />;
  }

  return (
    <div className="space-y-4">
      <PageHeader title="Feature Flags" description="Toggle platform-level features" icon={ToggleLeft} />

      <div className="rounded-lg border bg-card divide-y">
        {(flags ?? []).map((flag) => (
          <div key={flag.key} className="flex items-center justify-between px-4 py-3">
            <div>
              <p className="font-medium text-sm">{flag.display_name}</p>
              <p className="text-xs text-muted-foreground">{flag.description}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Updated {formatDate(flag.updated_at)} · <code>{flag.key}</code>
              </p>
            </div>
            <Switch
              checked={flag.global_enabled}
              disabled={!canWrite || update.isPending}
              onCheckedChange={(enabled) =>
                update.mutate(
                  { key: flag.key, payload: { global_enabled: enabled } },
                  getHandlers({ successTitle: `${flag.display_name} ${enabled ? "enabled" : "disabled"}` }),
                )
              }
            />
          </div>
        ))}
      </div>
    </div>
  );
}
