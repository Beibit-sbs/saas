import { useCallback, useEffect, useMemo, useState } from "react";

import { buildCsrfHeaders } from "../../components/csrf";
import { formatFeatureFlagLastChange } from "../utils";
import type { AdminCopy, FeatureFlag, InlineFeedback, TxFn } from "../types";

const FEATURE_FLAGS_BFF_PATH = "/api/bff/admin/feature-flags";

function extractErrorDetail(errorBody: unknown, fallbackStatus: number): string {
  if (errorBody && typeof errorBody === "object") {
    const body = errorBody as { detail?: unknown; error?: { detail?: unknown } };
    if (typeof body.detail === "string" && body.detail.trim().length > 0) {
      return body.detail;
    }
    if (typeof body.error?.detail === "string" && body.error.detail.trim().length > 0) {
      return body.error.detail;
    }
  }
  return String(fallbackStatus);
}

type UseAdminFeatureFlagsParams = {
  activeTab: string;
  buildAuthHeaders: () => Record<string, string>;
  l: AdminCopy;
  tx: TxFn;
};

type UseAdminFeatureFlagsResult = {
  featureFlags: FeatureFlag[];
  featureFlagSearch: string;
  featureFlagEnabledOnly: boolean;
  featureFlagsFeedback: InlineFeedback | null;
  featureFlagsLoading: boolean;
  featureFlagUpdateBusy: Record<string, boolean>;
  filteredFeatureFlags: FeatureFlag[];
  featureFlagFilterBadges: string[];
  hasActiveFeatureFlagFilters: boolean;
  featureFlagSummary: string;
  featureFlagsMutating: boolean;
  setFeatureFlagSearch: (value: string) => void;
  setFeatureFlagEnabledOnly: (value: boolean) => void;
  loadFeatureFlags: (preserveFeedback?: boolean) => Promise<void>;
  setFeatureFlagEnabled: (flag: FeatureFlag, enabled: boolean) => Promise<void>;
  getFeatureFlagLastChange: (flag: FeatureFlag) => string;
};

export function useAdminFeatureFlags({
  activeTab,
  buildAuthHeaders,
  l,
  tx,
}: UseAdminFeatureFlagsParams): UseAdminFeatureFlagsResult {
  const [featureFlags, setFeatureFlags] = useState<FeatureFlag[]>([]);
  const [featureFlagSearch, setFeatureFlagSearch] = useState("");
  const [featureFlagEnabledOnly, setFeatureFlagEnabledOnly] = useState(false);
  const [featureFlagsFeedback, setFeatureFlagsFeedback] = useState<InlineFeedback | null>(null);
  const [featureFlagsLoading, setFeatureFlagsLoading] = useState(false);
  const [featureFlagUpdateBusy, setFeatureFlagUpdateBusy] = useState<Record<string, boolean>>({});

  const normalizedFeatureFlagSearch = featureFlagSearch.trim().toLowerCase();

  const filteredFeatureFlags = useMemo(() => {
    return featureFlags.filter((flag) => {
      if (featureFlagEnabledOnly && !flag.enabled) {
        return false;
      }
      if (!normalizedFeatureFlagSearch) {
        return true;
      }

      const haystack = `${flag.key} ${flag.description || ""}`.toLowerCase();
      return haystack.includes(normalizedFeatureFlagSearch);
    });
  }, [featureFlagEnabledOnly, featureFlags, normalizedFeatureFlagSearch]);

  const featureFlagFilterBadges = useMemo(
    () => [
      normalizedFeatureFlagSearch ? `${tx("featureFlagFilterSearch", "Search")}: ${featureFlagSearch.trim()}` : "",
      featureFlagEnabledOnly ? tx("featureFlagFilterEnabledOnly", "Enabled only") : "",
    ].filter(Boolean),
    [featureFlagEnabledOnly, featureFlagSearch, normalizedFeatureFlagSearch, tx],
  );

  const hasActiveFeatureFlagFilters = featureFlagFilterBadges.length > 0;
  const featureFlagSummary = hasActiveFeatureFlagFilters
    ? tx("featureFlagsShowingFiltered", "Showing {count} filtered flags").replace("{count}", String(filteredFeatureFlags.length))
    : tx("featureFlagsShowing", "Showing {count} flags").replace("{count}", String(filteredFeatureFlags.length));

  const featureFlagsMutating = useMemo(
    () => Object.values(featureFlagUpdateBusy).some(Boolean),
    [featureFlagUpdateBusy],
  );

  const loadFeatureFlags = useCallback(async (preserveFeedback = false) => {
    setFeatureFlagsLoading(true);
    if (!preserveFeedback) {
      setFeatureFlagsFeedback(null);
    }

    try {
      const res = await fetch(FEATURE_FLAGS_BFF_PATH, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setFeatureFlagsFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`,
        });
        return;
      }

      const json = (await res.json()) as { flags?: FeatureFlag[] };
      setFeatureFlags(json.flags || []);
    } catch (error) {
      setFeatureFlagsFeedback({ tone: "error", message: String(error) });
    } finally {
      setFeatureFlagsLoading(false);
    }
  }, [buildAuthHeaders, l.errorPrefix]);

  const setFeatureFlagEnabled = useCallback(async (flag: FeatureFlag, enabled: boolean) => {
    const confirmed = window.confirm(
      (enabled
        ? tx("featureFlagEnableConfirm", "Enable feature flag {flag}?")
        : tx("featureFlagDisableConfirm", "Disable feature flag {flag}?"))
        .replace("{flag}", flag.key),
    );
    if (!confirmed) {
      setFeatureFlagsFeedback({ tone: "info", message: tx("featureFlagUpdateCancelled", "Feature flag update cancelled") });
      return;
    }

    setFeatureFlagUpdateBusy((prev) => ({ ...prev, [flag.key]: true }));
    setFeatureFlagsFeedback(null);
    try {
      const csrfHeaders = await buildCsrfHeaders("/api");
      const res = await fetch(FEATURE_FLAGS_BFF_PATH, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          key: flag.key,
          enabled,
          description: flag.description || "",
          scope: flag.scope || "global",
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setFeatureFlagsFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`,
        });
        return;
      }

      await loadFeatureFlags(true);
      const statusLabel = enabled ? tx("enabled", "Enabled") : tx("disabled", "Disabled");
      setFeatureFlagsFeedback({
        tone: "success",
        message: tx("featureFlagUpdated", "Feature flag {flag} set to {status}")
          .replace("{flag}", flag.key)
          .replace("{status}", statusLabel),
      });
    } catch (error) {
      setFeatureFlagsFeedback({ tone: "error", message: String(error) });
    } finally {
      setFeatureFlagUpdateBusy((prev) => ({ ...prev, [flag.key]: false }));
    }
  }, [buildAuthHeaders, l.errorPrefix, loadFeatureFlags, tx]);

  const getFeatureFlagLastChange = useCallback((flag: FeatureFlag) => formatFeatureFlagLastChange(flag), []);

  useEffect(() => {
    if (activeTab !== "feature-flags") {
      return;
    }

    void loadFeatureFlags();
  }, [activeTab, loadFeatureFlags]);

  return {
    featureFlags,
    featureFlagSearch,
    featureFlagEnabledOnly,
    featureFlagsFeedback,
    featureFlagsLoading,
    featureFlagUpdateBusy,
    filteredFeatureFlags,
    featureFlagFilterBadges,
    hasActiveFeatureFlagFilters,
    featureFlagSummary,
    featureFlagsMutating,
    setFeatureFlagSearch,
    setFeatureFlagEnabledOnly,
    loadFeatureFlags,
    setFeatureFlagEnabled,
    getFeatureFlagLastChange,
  };
}