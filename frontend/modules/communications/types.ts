export interface CommDomainSummary {
  domain_key: string;
  display_name: string;
  purpose: string;
  planned_table_groups: number;
  provider_boundary: boolean;
  brain_signal_applicable: boolean;
  workflow_status: string;
  live_delivery_enabled: boolean;
  production_ready: boolean;
}

export interface ProviderReadinessSummary {
  provider_key: string;
  provider_type: string;
  integration_status: string;
  credential_status: string;
  status_timestamp: string;
  status_label: string;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  no_live_delivery_reason: string;
}

export interface BrainActionBoundaryItem {
  source_signal_type: string;
  recommended_action: string;
  urgency_level: string;
  approval_required: boolean;
  approval_status: string;
  execution_status: string;
  policy_gates: string[];
}

export interface CommunicationsRuntimeShellResponse {
  tenant_id: number;
  generated_at: string;
  total_domains: number;
  total_planned_tables: number;
  total_core_permissions: number;
  domain_registry_loaded: boolean;
  live_delivery_enabled: boolean;
  provider_boundary_enforced: boolean;
  brain_action_boundary_enforced: boolean;
  production_ready: boolean;
  domains: CommDomainSummary[];
  provider_readiness: ProviderReadinessSummary[];
  brain_action_samples: BrainActionBoundaryItem[];
  safety_constraints: string[];
}

export interface NotificationProviderBoundary {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface NotificationCenterItem {
  notification_id: string;
  title: string;
  message_preview: string;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  created_at: string;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface NotificationCenterSummaryResponse {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  total_notifications: number;
  unread_notifications: number;
  high_priority_notifications: number;
  boundary: NotificationProviderBoundary;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface NotificationListResponse {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  notifications: NotificationCenterItem[];
  total: number;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface AnnouncementRegistryBoundary {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  publish_workflow_enabled: boolean;
  broadcast_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface AnnouncementRegistryItem {
  announcement_id: string;
  title: string;
  category: string;
  audience_scope: string;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  created_at: string;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  publish_workflow_enabled: boolean;
  broadcast_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface AnnouncementRegistrySummaryResponse {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  total_announcements: number;
  active_announcements: number;
  expiring_soon_announcements: number;
  boundary: AnnouncementRegistryBoundary;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  publish_workflow_enabled: boolean;
  broadcast_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface AnnouncementListResponse {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  announcements: AnnouncementRegistryItem[];
  total: number;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  publish_workflow_enabled: boolean;
  broadcast_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface MessageTemplateRegistryBoundary {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  template_send_enabled: boolean;
  preference_mutation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface MessageTemplateRegistryItem {
  template_id: string;
  template_name: string;
  channel_type: string;
  locale: string;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  updated_at: string;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  template_send_enabled: boolean;
  preference_mutation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface MessageTemplateRegistrySummaryResponse {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  total_templates: number;
  active_templates: number;
  channels_covered: number;
  boundary: MessageTemplateRegistryBoundary;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  template_send_enabled: boolean;
  preference_mutation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface MessageTemplateListResponse {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  templates: MessageTemplateRegistryItem[];
  total: number;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  template_send_enabled: boolean;
  preference_mutation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface NotificationPreferenceRegistryBoundary {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  template_send_enabled: boolean;
  preference_mutation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface NotificationPreferenceRegistryItem {
  preference_id: string;
  audience_type: string;
  channel_type: string;
  preference_scope: string;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  updated_at: string;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  template_send_enabled: boolean;
  preference_mutation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface NotificationPreferenceRegistrySummaryResponse {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  total_preferences: number;
  default_preferences: number;
  audience_segments: number;
  boundary: NotificationPreferenceRegistryBoundary;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  template_send_enabled: boolean;
  preference_mutation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface NotificationPreferenceListResponse {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  preferences: NotificationPreferenceRegistryItem[];
  total: number;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  template_send_enabled: boolean;
  preference_mutation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface DeliveryAuditBoundary {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  delivery_success_claimed: boolean;
  escalation_execution_enabled: boolean;
  autonomous_escalation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface DeliveryAuditEventItem {
  audit_event_id: string;
  event_type: string;
  channel_type: string;
  audience_scope: string;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  recorded_at: string;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  delivery_success_claimed: boolean;
  escalation_execution_enabled: boolean;
  autonomous_escalation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface DeliveryAuditSummaryResponse {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  total_audit_events: number;
  pending_internal_events: number;
  policy_review_events: number;
  boundary: DeliveryAuditBoundary;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  delivery_success_claimed: boolean;
  escalation_execution_enabled: boolean;
  autonomous_escalation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface DeliveryAuditListResponse {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  events: DeliveryAuditEventItem[];
  total: number;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  delivery_success_claimed: boolean;
  escalation_execution_enabled: boolean;
  autonomous_escalation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface EscalationWorkflowBoundary {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  delivery_success_claimed: boolean;
  escalation_execution_enabled: boolean;
  autonomous_escalation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface EscalationWorkflowItem {
  escalation_id: string;
  workflow_type: string;
  approval_level: string;
  policy_gate: string;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  reviewed_at: string;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  delivery_success_claimed: boolean;
  escalation_execution_enabled: boolean;
  autonomous_escalation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface EscalationWorkflowSummaryResponse {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  total_workflows: number;
  approval_gated_workflows: number;
  critical_policy_workflows: number;
  boundary: EscalationWorkflowBoundary;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  delivery_success_claimed: boolean;
  escalation_execution_enabled: boolean;
  autonomous_escalation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}

export interface EscalationWorkflowListResponse {
  tenant_id: number;
  source_type: string;
  internal_status: string;
  external_delivery_status: string;
  workflows: EscalationWorkflowItem[];
  total: number;
  live_delivery_enabled: boolean;
  provider_connected: boolean;
  external_delivery_claimed: boolean;
  delivery_success_claimed: boolean;
  escalation_execution_enabled: boolean;
  autonomous_escalation_enabled: boolean;
  no_live_delivery_reason: string;
  provider_status_label: string;
}
