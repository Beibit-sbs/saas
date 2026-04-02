import { useCallback, useEffect, useState } from "react";

import type { AdminTab, InlineFeedback, SystemHealthResponse } from "../types";

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

type UseAdminSystemHealthParams = {
  activeTab: AdminTab;
  buildAuthHeaders: () => Record<string, string>;
};

type UseAdminSystemHealthResult = {
  systemHealth: SystemHealthResponse | null;
  loading: boolean;
  feedback: InlineFeedback | null;
  refresh: () => Promise<void>;
  lastUpdated: string;
};

export function useAdminSystemHealth({
  activeTab,
  buildAuthHeaders,
}: UseAdminSystemHealthParams): UseAdminSystemHealthResult {
  const [systemHealth, setSystemHealth] = useState<SystemHealthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<InlineFeedback | null>(null);
  const [lastUpdated, setLastUpdated] = useState("-");

  const refresh = useCallback(async () => {
    setLoading(true);
    setFeedback(null);
    try {
      const res = await fetch("/api/bff/admin/system/health", {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setFeedback({
          tone: "error",
          message: `Error: ${extractErrorDetail(err, res.status)}`,
        });
        return;
      }

      const json = (await res.json()) as SystemHealthResponse;
      setSystemHealth(json);
      setLastUpdated(new Date().toLocaleString());
    } catch (error) {
      setFeedback({ tone: "error", message: String(error) });
    } finally {
      setLoading(false);
    }
  }, [buildAuthHeaders]);

  useEffect(() => {
    if (activeTab !== "system") {
      return;
    }

    void refresh();
    const intervalId = window.setInterval(() => {
      void refresh();
    }, 30_000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [activeTab, refresh]);

  return {
    systemHealth,
    loading,
    feedback,
    refresh,
    lastUpdated,
  };
}
