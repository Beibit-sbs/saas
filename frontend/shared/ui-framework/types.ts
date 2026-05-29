import type { ReactNode } from 'react';

export type ActionVariant = 'default' | 'secondary' | 'outline' | 'ghost' | 'destructive';

export interface ActionDefinition {
  id: string;
  label: string;
  onClick?: () => void;
  disabled?: boolean;
  disabledReason?: string;
  requiredPermission?: string;
  hasPermission?: boolean;
  icon?: ReactNode;
  variant?: ActionVariant;
}

export type EmptyStateVariant =
  | 'no_data'
  | 'no_results'
  | 'permission_denied'
  | 'unavailable'
  | 'metadata_only'
  | 'future_scope';

export interface AuditTrailEvent {
  id: string;
  actor: string;
  timestamp: string;
  status: string;
  event: string;
  metadata?: Record<string, string | number | boolean | null | undefined>;
}

export interface StatusFilterOption {
  value: string;
  label: string;
}

export interface DateRangeValue {
  from: string;
  to: string;
}