import { useCallback, useEffect, useMemo, useState } from "react";
import type { AdminTranslationKey } from "../../../i18n/admin";
import type { AdminTab, DashboardSnapshot, InlineFeedback, SupportedLanguage } from "../types";

type UseAdminOverviewParams = {
  activeTab: AdminTab;
  buildAuthHeaders: () => Record<string, string>;
  errorPrefix: string;
  supportedLanguages: SupportedLanguage[];
  tx: (key: AdminTranslationKey, fallback?: string) => string;
};

type UseAdminOverviewResult = {
  dashboardLoading: boolean;
  overviewFeedback: InlineFeedback | null;
  dashboardSnapshot: DashboardSnapshot | null;
  dashboardStamp: string;
  enabledLanguageCodes: string;
  loadDashboard: () => Promise<void>;
  touchDashboardStamp: () => void;
};

export function useAdminOverview({
  activeTab,
  buildAuthHeaders,
  errorPrefix,
  supportedLanguages,
  tx,
}: UseAdminOverviewParams): UseAdminOverviewResult {
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [overviewFeedback, setOverviewFeedback] = useState<InlineFeedback | null>(null);
  const [dashboardSnapshot, setDashboardSnapshot] = useState<DashboardSnapshot | null>(null);
  const [dashboardStamp, setDashboardStamp] = useState(() => new Date().toLocaleString());

  const enabledLanguageCodes = useMemo(
    () => supportedLanguages
      .filter((item) => item.enabled)
      .map((item) => item.code)
      .join(", "),
    [supportedLanguages],
  );

  const loadDashboard = useCallback(async () => {
    setOverviewFeedback(null);
    setDashboardLoading(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const res = await fetch(`${baseUrl}/admin/dashboard`, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setOverviewFeedback({
          tone: "error",
          message: `${errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      const json = (await res.json()) as DashboardSnapshot;
      setDashboardSnapshot(json);
      setDashboardStamp(new Date(json.generated_at).toLocaleString());

      setOverviewFeedback({ tone: "success", message: tx("overviewRefreshed") });
    } catch (error) {
      setOverviewFeedback({ tone: "error", message: String(error) });
    } finally {
      setDashboardLoading(false);
    }
  }, [buildAuthHeaders, errorPrefix, tx]);

  const touchDashboardStamp = useCallback(() => {
    setDashboardStamp(new Date().toLocaleString());
  }, []);

  useEffect(() => {
    if (activeTab !== "overview") {
      return;
    }
    void loadDashboard();
  }, [activeTab, loadDashboard]);

  return {
    dashboardLoading,
    overviewFeedback,
    dashboardSnapshot,
    dashboardStamp,
    enabledLanguageCodes,
    loadDashboard,
    touchDashboardStamp,
  };
}
