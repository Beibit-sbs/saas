import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import type { AuditEventsParams, AuditEventsResponse } from "./types";

export const AUDIT_EVENTS_KEY = "audit-events";

export function useAuditEvents(params?: AuditEventsParams) {
  return useQuery({
    queryKey: [AUDIT_EVENTS_KEY, params],
    queryFn: () => apiGet<AuditEventsResponse>("/api/admin/audit/events", params),
  });
}
