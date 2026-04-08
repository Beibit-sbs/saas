export interface AuditEvent {
  event_id: string;
  timestamp: string;
  actor: string;
  action: string;
  entity: string;
  path: string;
  ip: string;
  client_ip: string;
  result: string;
  tenant_id: number;
  correlation_id: string;
  metadata: Record<string, unknown>;
}

export interface AuditEventsResponse {
  events: AuditEvent[];
}

export interface AuditEventsParams {
  actor?: string;
  action?: string;
  entity?: string;
  result?: string;
  correlation_id?: string;
  since?: string;
  tenant_id?: string;
  limit?: number;
}
