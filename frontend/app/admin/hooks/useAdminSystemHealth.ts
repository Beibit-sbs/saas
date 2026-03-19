import { useCallback, useEffect, useState } from "react";

import type { AdminTab, InlineFeedback } from "../types";

export type SystemHealthResponse = {
  status: string;
  services: Record<string, string>;
  metrics: Record<string, string | number | boolean | null>;
  queues: Record<string, string | number | boolean | null>;
  disk: {
    path: string;
    total_bytes: number;
    used_bytes: number;
    free_bytes: number;
    usage_percent: number;
  };
};

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
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const res = await fetch(`${baseUrl}/admin/system/health`, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setFeedback({
          tone: "error",
          message: `Error: ${String(err.detail || res.status)}`,
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
