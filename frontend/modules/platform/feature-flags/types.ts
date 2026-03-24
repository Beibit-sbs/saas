export interface FeatureFlag {
  key: string;
  display_name: string;
  description: string;
  global_enabled: boolean;
  tenant_overrides: Record<string, boolean>;
  updated_at: string;
}

export interface UpdateFlagPayload {
  global_enabled?: boolean;
}

export interface TenantFlagOverridePayload {
  tenant_id: string;
  enabled: boolean;
}
