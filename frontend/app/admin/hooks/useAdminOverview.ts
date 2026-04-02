import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { AdminTranslationKey } from "../../../i18n/admin";
import type { AdminInsight, AdminTab, AuditEvent, DashboardSnapshot, InlineFeedback, JobItem, LocalUser, SupportedLanguage, SystemHealthResponse } from "../types";
import { normalizeApiError } from "@/shared/utils/api-error";
import { computeOverviewInsights } from "../utils/computeOverviewInsights";

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
  decisionInsights: AdminInsight[];
  dashboardStamp: string;
  enabledLanguageCodes: string;
  loadDashboard: () => Promise<void>;
  touchDashboardStamp: () => void;
};

async function fetchOptionalJson<T>(input: string, init: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(input, init);
    if (!res.ok) {
      return null;
    }
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

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
  const [decisionInsights, setDecisionInsights] = useState<AdminInsight[]>([]);
  const [dashboardStamp, setDashboardStamp] = useState(() => new Date().toLocaleString());
  const inFlightRef = useRef<Promise<void> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const enabledLanguageCodes = useMemo(
    () => supportedLanguages
      .filter((item) => item.enabled)
      .map((item) => item.code)
      .join(", "),
    [supportedLanguages],
  );

  const loadDashboard = useCallback(async () => {
    if (inFlightRef.current) {
      return inFlightRef.current;
    }

    setOverviewFeedback(null);
    setDashboardLoading(true);
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const request = (async () => {
      try {
        const requestInit: RequestInit = {
          headers: buildAuthHeaders(),
          credentials: "include",
          cache: "no-store",
          signal: controller.signal,
        };

        const res = await fetch("/api/bff/admin/dashboard", requestInit);

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          setDecisionInsights([]);
          setOverviewFeedback({
            tone: "error",
            message: `${errorPrefix}: ${extractErrorDetail(err, res.status)}`,
          });
          return;
        }

        const json = (await res.json()) as DashboardSnapshot;
        setDashboardSnapshot(json);
        setDashboardStamp(new Date(json.generated_at).toLocaleString());

        const optionalFetches = await Promise.allSettled([
          fetchOptionalJson<SystemHealthResponse>("/api/bff/admin/system/health", requestInit),
          fetchOptionalJson<{ jobs?: JobItem[] }>("/api/bff/admin/jobs", requestInit),
          fetchOptionalJson<{ events?: AuditEvent[] }>("/api/bff/admin/audit/events?limit=200", requestInit),
          fetchOptionalJson<{ users?: LocalUser[] }>("/api/bff/admin/local-users", requestInit),
        ]);

        const systemHealthJson = optionalFetches[0].status === "fulfilled" ? optionalFetches[0].value : null;
        const jobsJson = optionalFetches[1].status === "fulfilled" ? optionalFetches[1].value : null;
        const auditJson = optionalFetches[2].status === "fulfilled" ? optionalFetches[2].value : null;
        const localUsersJson = optionalFetches[3].status === "fulfilled" ? optionalFetches[3].value : null;
        const partialFailures = optionalFetches.filter((result) => result.status === "rejected" || result.value === null).length;

        setDecisionInsights(
          computeOverviewInsights({
            dashboardSnapshot: json,
            systemHealth: systemHealthJson,
            jobs: jobsJson?.jobs ?? [],
            auditEvents: auditJson?.events ?? [],
            localUsers: localUsersJson?.users ?? [],
            supportedLanguages,
          }),
        );

        setOverviewFeedback({
          tone: partialFailures > 0 ? "info" : "success",
          message: partialFailures > 0 ? tx("overviewPartialSignals") : tx("overviewRefreshed"),
        });
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }
        setDecisionInsights([]);
        const normalized = normalizeApiError(error);
        setOverviewFeedback({ tone: "error", message: `${normalized.message} ${normalized.actionable}`.trim() });
      } finally {
        if (abortRef.current === controller) {
          abortRef.current = null;
        }
        inFlightRef.current = null;
        setDashboardLoading(false);
      }
    })();

    inFlightRef.current = request;
    return request;
  }, [buildAuthHeaders, errorPrefix, supportedLanguages, tx]);

  const touchDashboardStamp = useCallback(() => {
    setDashboardStamp(new Date().toLocaleString());
  }, []);

  useEffect(() => {
    if (activeTab !== "overview") {
      abortRef.current?.abort();
      return;
    }
    void loadDashboard();
    return () => {
      abortRef.current?.abort();
    };
  }, [activeTab, loadDashboard]);

  return {
    dashboardLoading,
    overviewFeedback,
    dashboardSnapshot,
    decisionInsights,
    dashboardStamp,
    enabledLanguageCodes,
    loadDashboard,
    touchDashboardStamp,
  };
}
