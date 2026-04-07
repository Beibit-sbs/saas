export interface RectorTrendPoint {
  snapshot_date: string;
  value: number;
}

export interface RectorKpiCard {
  metric_key: string;
  title: string;
  value: number;
  trend_7d: RectorTrendPoint[];
  metadata_json: Record<string, unknown>;
}

export interface RectorDashboard {
  tenant_id: number;
  snapshot_date: string;
  cards: RectorKpiCard[];
  generated_at: string | null;
  source: string;
}

export interface TenantMetricSnapshot {
  id: number;
  tenant_id: number;
  metric_key: string;
  metric_value: number;
  snapshot_date: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  version: number;
}
