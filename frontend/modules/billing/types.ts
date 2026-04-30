// Types mirroring backend app/modules/billing/schemas.py

export interface BillingPlan {
  id: number;
  code: string;
  name: string;
  price_cents: number;
  features: Record<string, boolean>;
  limits: Record<string, number>;
  active: boolean;
  created_at: string;
}

export interface BillingPlanCreatePayload {
  code: string;
  name: string;
  price_cents: number;
  features?: Record<string, boolean>;
  limits?: Record<string, number>;
}

export interface BillingPlanUpdatePayload {
  name?: string;
  active?: boolean;
}

export interface BillingSubscription {
  tenant_id: number;
  plan_id: number;
  plan_code: string;
  status: string;
  started_at: string;
  trial_ends_at: string | null;
  current_period_start: string;
  current_period_end: string;
  next_plan_id: number | null;
  next_plan_code: string | null;
  updated_at: string;
}

export interface BillingState {
  tenant_id: number;
  plan_code: string;
  plan_id: number;
  next_plan_code: string | null;
  subscription_status: string;
  billing_state: string;
  period_start: string | null;
  period_end: string | null;
  limits: Record<string, number>;
  usage: Record<string, number>;
  subscription: BillingSubscription;
}

export interface BillingSubscriptionAssignPayload {
  plan_code: string;
}

export interface BillingTransitionPayload {
  status: string;
}

export interface BillingPlanChangePayload {
  plan_code: string;
  effective?: string;
}

export interface BillingUsage {
  tenant_id: number;
  usage: Record<string, number>;
}

export interface BillingDunningPolicy {
  grace_period_days: number;
  overdue_period_days: number;
  suspension_period_days: number;
  auto_cancel_after_days: number;
  reminder_schedule: number[];
  require_approval_for_reactivation: boolean;
}

export interface BillingCollectionEvent {
  event_type: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface BillingDelinquencyRecord {
  id: number;
  tenant_id: number;
  invoice_id: string;
  status: string;
  opened_at: string;
  last_reminder_at: string | null;
  reminder_count: number;
  escalated_at: string | null;
  resolved_at: string | null;
  resolution: string | null;
  notes: string | null;
  amount_cents: number;
  events: BillingCollectionEvent[];
}

export interface BillingDelinquencyListResponse {
  items: BillingDelinquencyRecord[];
  total: number;
}

export interface BillingDelinquencyDashboard {
  total: number;
  open_total: number;
  total_overdue_cents: number;
  by_status: Record<string, number>;
}
