export interface FeatureFlag {
  key: string;
  description: string;
  enabled: boolean;
  scope: string;
  rollout_percentage: number;
  updated_at: string;
}

export interface UpsertFlagPayload {
  key: string;
  enabled: boolean;
  rollout_percentage?: number;
  description?: string;
  scope?: string;
}
