"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/shared/ui/page-header";
import { Switch } from "@/shared/ui/switch";
import { Skeleton } from "@/shared/ui/skeleton";
import { ErrorState } from "@/shared/ui/error-state";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { useFeatureFlags, useUpsertFeatureFlag } from "@/modules/platform/feature-flags/hooks";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { PERMISSIONS } from "@/shared/config/permissions";
import { formatDate } from "@/shared/utils/format";
import { useLanguage } from "@/app/components/LanguageProvider";
import { ToggleLeft } from "lucide-react";
import type { FeatureFlag } from "@/modules/platform/feature-flags/types";

type UpsertMutation = ReturnType<typeof useUpsertFeatureFlag>;
type GetHandlersFn = ReturnType<typeof useMutationFeedback>["getHandlers"];

function FlagRow({
  flag,
  canWrite,
  update,
  getHandlers,
}: {
  flag: FeatureFlag;
  canWrite: boolean;
  update: UpsertMutation;
  getHandlers: GetHandlersFn;
}) {
  const [rollout, setRollout] = useState(flag.rollout_percentage);

  useEffect(() => {
    setRollout(flag.rollout_percentage);
  }, [flag.rollout_percentage]);

  function commitRollout() {
    const pct = Math.max(0, Math.min(100, rollout));
    setRollout(pct);
    if (pct !== flag.rollout_percentage) {
      update.mutate(
        { key: flag.key, enabled: flag.enabled, rollout_percentage: pct },
        getHandlers({ successTitle: `${flag.key} rollout: ${pct}%` }),
      );
    }
  }

  return (
    <div className="flex items-center justify-between px-4 py-3">
      <div>
        <p className="font-medium text-sm">{flag.key}</p>
        <p className="text-xs text-muted-foreground">{flag.description}</p>
        <p className="text-xs text-muted-foreground mt-0.5">
          Updated {formatDate(flag.updated_at)} &middot; <code>{flag.scope}</code>
        </p>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1" title="Rollout percentage">
          <input
            type="number"
            min={0}
            max={100}
            value={rollout}
            disabled={!canWrite || update.isPending}
            aria-label={`Rollout percentage for ${flag.key}`}
            className="w-14 text-right text-sm border rounded px-1 py-0.5 bg-background disabled:opacity-50 focus:outline-none focus:ring-1 focus:ring-ring"
            onChange={(e) => setRollout(Number(e.target.value))}
            onBlur={commitRollout}
            onKeyDown={(e) => {
              if (e.key === "Enter") commitRollout();
            }}
          />
          <span className="text-xs text-muted-foreground">%</span>
        </div>
        <Switch
          checked={flag.enabled}
          disabled={!canWrite || update.isPending}
          onCheckedChange={(enabled) =>
            update.mutate(
              { key: flag.key, enabled, rollout_percentage: flag.rollout_percentage },
              getHandlers({ successTitle: `${flag.key} ${enabled ? "enabled" : "disabled"}` }),
            )
          }
        />
      </div>
    </div>
  );
}

export default function FeatureFlagsPage() {
  const { t } = useLanguage();
  const { data: flags, isLoading, error, refetch } = useFeatureFlags();
  const update = useUpsertFeatureFlag();
  const { hasPermission } = usePermissions();
  const { getHandlers } = useMutationFeedback();
  const canWrite = hasPermission(PERMISSIONS.FEATURE_FLAGS_WRITE);

  if (!hasPermission(PERMISSIONS.FEATURE_FLAGS_READ)) return <AccessDenied />;

  if (isLoading) {
    return (
      <div className="space-y-4">
        <PageHeader title={t("nav.featureFlags")} icon={ToggleLeft} />
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
      <PageHeader title={t("nav.featureFlags")} description={t("console.featureFlags.description")} icon={ToggleLeft} />

      <div className="rounded-lg border bg-card divide-y">
        {(flags ?? []).map((flag) => (
          <FlagRow
            key={flag.key}
            flag={flag}
            canWrite={canWrite}
            update={update}
            getHandlers={getHandlers}
          />
        ))}
      </div>
    </div>
  );
}
