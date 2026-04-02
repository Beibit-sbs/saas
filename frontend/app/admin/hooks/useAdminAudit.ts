import { useCallback, useEffect, useMemo, useState } from "react";

import type { AdminCopy, AuditEvent, AuditExportBusy, InlineFeedback, TxFn } from "../types";

const AUDIT_BFF_BASE = "/api/bff/admin/audit";

function auditBffPath(path: string): string {
  return `${AUDIT_BFF_BASE}/${path}`;
}

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

type UseAdminAuditParams = {
  activeTab: string;
  buildAuthHeaders: () => Record<string, string>;
  l: AdminCopy;
  tx: TxFn;
};

type LoadAuditOverrides = {
  actor?: string;
  action?: string;
  entity?: string;
  result?: string;
  correlationId?: string;
  since?: string;
};

type UseAdminAuditResult = {
  auditActor: string;
  auditAction: string;
  auditEntity: string;
  auditResult: string;
  auditCorrelationId: string;
  auditSince: string;
  auditEvents: AuditEvent[];
  auditFeedback: InlineFeedback | null;
  auditLoading: boolean;
  auditExportBusy: AuditExportBusy;
  auditFilterBadges: string[];
  hasActiveAuditFilters: boolean;
  auditLatestTimestamp: string;
  setAuditActor: (value: string) => void;
  setAuditAction: (value: string) => void;
  setAuditEntity: (value: string) => void;
  setAuditResult: (value: string) => void;
  setAuditCorrelationId: (value: string) => void;
  setAuditSince: (value: string) => void;
  loadAuditEvents: (overrides?: LoadAuditOverrides) => Promise<void>;
  exportAudit: (format: "json" | "csv") => Promise<void>;
  clearAuditFilters: () => Promise<void>;
};

export function useAdminAudit({
  activeTab,
  buildAuthHeaders,
  l,
  tx,
}: UseAdminAuditParams): UseAdminAuditResult {
  const [auditActor, setAuditActor] = useState("");
  const [auditAction, setAuditAction] = useState("");
  const [auditEntity, setAuditEntity] = useState("");
  const [auditResult, setAuditResult] = useState("");
  const [auditCorrelationId, setAuditCorrelationId] = useState("");
  const [auditSince, setAuditSince] = useState("");
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [auditFeedback, setAuditFeedback] = useState<InlineFeedback | null>(null);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditExportBusy, setAuditExportBusy] = useState<AuditExportBusy>("");

  const auditFilterBadges = useMemo(
    () => [
      auditActor.trim() ? `${tx("auditActor", "Actor")}: ${auditActor.trim()}` : "",
      auditAction.trim() ? `${tx("auditAction", "Action")}: ${auditAction.trim()}` : "",
      auditEntity.trim() ? `${tx("auditEntity", "Entity")}: ${auditEntity.trim()}` : "",
      auditResult.trim() ? `${tx("auditResult", "Result")}: ${auditResult.trim()}` : "",
      auditSince.trim() ? `${tx("auditTs", "Timestamp")}: ${auditSince.trim()}` : "",
      auditCorrelationId.trim() ? `${tx("auditCorrelation", "Correlation ID")}: ${auditCorrelationId.trim()}` : "",
    ].filter(Boolean),
    [auditAction, auditActor, auditCorrelationId, auditEntity, auditResult, auditSince, tx],
  );

  const hasActiveAuditFilters = auditFilterBadges.length > 0;

  const auditLatestTimestamp = useMemo(() => {
    if (auditEvents.length === 0) {
      return "-";
    }

    let latest = auditEvents[0].timestamp;
    for (const item of auditEvents) {
      if (new Date(item.timestamp).getTime() > new Date(latest).getTime()) {
        latest = item.timestamp;
      }
    }
    return latest;
  }, [auditEvents]);

  const loadAuditEvents = useCallback(async (overrides?: LoadAuditOverrides) => {
    setAuditLoading(true);
    setAuditFeedback(null);

    try {
      const effectiveActor = overrides?.actor ?? auditActor;
      const effectiveAction = overrides?.action ?? auditAction;
      const effectiveEntity = overrides?.entity ?? auditEntity;
      const effectiveResult = overrides?.result ?? auditResult;
      const effectiveCorrelationId = overrides?.correlationId ?? auditCorrelationId;
      const effectiveSince = overrides?.since ?? auditSince;
      const params = new URLSearchParams();

      if (effectiveActor.trim()) {
        params.set("actor", effectiveActor.trim());
      }
      if (effectiveAction.trim()) {
        params.set("action", effectiveAction.trim());
      }
      if (effectiveEntity.trim()) {
        params.set("entity", effectiveEntity.trim());
      }
      if (effectiveResult.trim()) {
        params.set("result", effectiveResult.trim());
      }
      if (effectiveCorrelationId.trim()) {
        params.set("correlation_id", effectiveCorrelationId.trim());
      }
      if (effectiveSince.trim()) {
        params.set("since", effectiveSince.trim());
      }
      params.set("limit", "200");

      const res = await fetch(`${auditBffPath("events")}?${params.toString()}`, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setAuditFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`,
        });
        return;
      }

      const json = (await res.json()) as { events?: AuditEvent[] };
      const rows = json.events || [];
      setAuditEvents(rows);
      setAuditFeedback({
        tone: "success",
        message: tx("auditShowingEvents", "Showing {count} events").replace("{count}", String(rows.length)),
      });
    } catch (error) {
      setAuditFeedback({ tone: "error", message: String(error) });
    } finally {
      setAuditLoading(false);
    }
  }, [auditAction, auditActor, auditCorrelationId, auditEntity, auditResult, auditSince, buildAuthHeaders, l.errorPrefix, tx]);

  const exportAudit = useCallback(async (format: "json" | "csv") => {
    setAuditFeedback(null);
    setAuditExportBusy(format);

    try {
      const params = new URLSearchParams();
      params.set("format", format);
      if (auditActor.trim()) {
        params.set("actor", auditActor.trim());
      }
      if (auditAction.trim()) {
        params.set("action", auditAction.trim());
      }
      if (auditEntity.trim()) {
        params.set("entity", auditEntity.trim());
      }
      if (auditResult.trim()) {
        params.set("result", auditResult.trim());
      }
      if (auditCorrelationId.trim()) {
        params.set("correlation_id", auditCorrelationId.trim());
      }
      if (auditSince.trim()) {
        params.set("since", auditSince.trim());
      }

      const res = await fetch(`${auditBffPath("export")}?${params.toString()}`, {
        headers: buildAuthHeaders(),
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setAuditFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`,
        });
        return;
      }

      const text = await res.text();
      const blob = new Blob([text], { type: format === "csv" ? "text/csv" : "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = format === "csv" ? "audit-events.csv" : "audit-events.json";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setAuditFeedback({
        tone: "success",
        message: tx("export", "Export CSV/JSON"),
      });
    } catch (error) {
      setAuditFeedback({ tone: "error", message: String(error) });
    } finally {
      setAuditExportBusy("");
    }
  }, [auditAction, auditActor, auditCorrelationId, auditEntity, auditResult, auditSince, buildAuthHeaders, l.errorPrefix, tx]);

  const clearAuditFilters = useCallback(async () => {
    setAuditActor("");
    setAuditAction("");
    setAuditEntity("");
    setAuditResult("");
    setAuditCorrelationId("");
    setAuditSince("");
    setAuditFeedback({ tone: "info", message: tx("auditNoFiltersActive", "No active filters") });
    await loadAuditEvents({
      actor: "",
      action: "",
      entity: "",
      result: "",
      correlationId: "",
      since: "",
    });
  }, [loadAuditEvents, tx]);

  useEffect(() => {
    if (activeTab !== "audit") {
      return;
    }

    void loadAuditEvents();
  }, [activeTab, loadAuditEvents]);

  return {
    auditActor,
    auditAction,
    auditEntity,
    auditResult,
    auditCorrelationId,
    auditSince,
    auditEvents,
    auditFeedback,
    auditLoading,
    auditExportBusy,
    auditFilterBadges,
    hasActiveAuditFilters,
    auditLatestTimestamp,
    setAuditActor,
    setAuditAction,
    setAuditEntity,
    setAuditResult,
    setAuditCorrelationId,
    setAuditSince,
    loadAuditEvents,
    exportAudit,
    clearAuditFilters,
  };
}
