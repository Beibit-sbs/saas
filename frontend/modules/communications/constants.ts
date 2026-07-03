export const COMMUNICATIONS_API_PATHS = {
  overview: '/api/admin/communications/overview',
  domains: '/api/admin/communications/domains',
  notifications: '/api/admin/communications/notifications',
  notificationsSummary: '/api/admin/communications/notifications/summary',
  notificationsBoundary: '/api/admin/communications/notifications/boundary',
  announcements: '/api/admin/communications/announcements',
  announcementsSummary: '/api/admin/communications/announcements/summary',
  announcementsBoundary: '/api/admin/communications/announcements/boundary',
  templates: '/api/admin/communications/templates',
  templatesSummary: '/api/admin/communications/templates/summary',
  templatesBoundary: '/api/admin/communications/templates/boundary',
  preferences: '/api/admin/communications/preferences',
  preferencesSummary: '/api/admin/communications/preferences/summary',
  preferencesBoundary: '/api/admin/communications/preferences/boundary',
  deliveryAudit: '/api/admin/communications/delivery-audit',
  deliveryAuditSummary: '/api/admin/communications/delivery-audit/summary',
  deliveryAuditBoundary: '/api/admin/communications/delivery-audit/boundary',
  escalations: '/api/admin/communications/escalations',
  escalationsSummary: '/api/admin/communications/escalations/summary',
  escalationsBoundary: '/api/admin/communications/escalations/boundary',
  providerReadiness: '/api/admin/communications/provider-readiness',
  brainActions: '/api/admin/communications/brain-actions',
} as const;

export const COMMUNICATIONS_ROUTES = {
  overview: '/console/communications/overview',
  notifications: '/console/communications/notifications',
  announcements: '/console/communications/announcements',
  templates: '/console/communications/templates',
  preferences: '/console/communications/preferences',
  deliveryAudit: '/console/communications/delivery-audit',
  escalations: '/console/communications/escalations',
  providerReadiness: '/console/communications/provider-readiness',
  brainActions: '/console/communications/brain-actions',
} as const;

export const COMMUNICATIONS_NAV_ITEMS = [
  { key: 'overview', title: 'Overview', href: COMMUNICATIONS_ROUTES.overview },
  { key: 'notifications', title: 'Notifications', href: COMMUNICATIONS_ROUTES.notifications },
  { key: 'announcements', title: 'Announcements', href: COMMUNICATIONS_ROUTES.announcements },
  { key: 'templates', title: 'Templates', href: COMMUNICATIONS_ROUTES.templates },
  { key: 'preferences', title: 'Preferences', href: COMMUNICATIONS_ROUTES.preferences },
  { key: 'deliveryAudit', title: 'Delivery Audit', href: COMMUNICATIONS_ROUTES.deliveryAudit },
  { key: 'escalations', title: 'Escalations', href: COMMUNICATIONS_ROUTES.escalations },
  { key: 'providerReadiness', title: 'Provider Readiness', href: COMMUNICATIONS_ROUTES.providerReadiness },
  { key: 'brainActions', title: 'Brain Actions', href: COMMUNICATIONS_ROUTES.brainActions },
] as const;

export const COMMUNICATIONS_BOUNDARY_COPY = [
  'read_only_foundation',
  'no_workflow_execution',
  'no_external_delivery',
  'no_fake_delivery_success',
  'no_provider_credentials_stored',
  'no_autonomous_critical_actions',
  'tenant_isolation_enforced',
  'rbac_permission_required',
] as const;
