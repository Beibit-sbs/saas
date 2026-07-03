'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import { communicationsApi } from './api';
import { COMMUNICATIONS_BOUNDARY_COPY, COMMUNICATIONS_NAV_ITEMS, COMMUNICATIONS_ROUTES } from './constants';
import { COMMUNICATIONS_PERMISSIONS } from './guards';
import type {
  AnnouncementRegistryItem,
  BrainActionBoundaryItem,
  CommDomainSummary,
  DeliveryAuditEventItem,
  EscalationWorkflowItem,
  MessageTemplateRegistryItem,
  NotificationCenterItem,
  NotificationPreferenceRegistryItem,
  ProviderReadinessSummary,
} from './types';

function Shell({ title, description, currentPath, children }: { title: string; description: string; currentPath: string; children: React.ReactNode }) {
  return (
    <section className="space-y-6" data-testid="communications-shell">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">{title}</h1>
        <p className="text-sm text-muted-foreground">{description}</p>
      </header>
      <nav className="flex flex-wrap gap-2" aria-label="Communications navigation">
        {COMMUNICATIONS_NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`rounded border px-3 py-1.5 text-sm ${item.href === currentPath ? 'bg-primary/10 text-primary' : 'text-muted-foreground'}`}
          >
            {item.title}
          </Link>
        ))}
      </nav>
      {children}
    </section>
  );
}

function BoundaryPanel({ items }: { items: readonly string[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="communications-boundary-panel">
      <h2 className="text-lg font-semibold">Runtime safety</h2>
      <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function MetricCard({ label, value, helper }: { label: string; value: string | number; helper?: string }) {
  return (
    <div className="rounded-lg border p-4" data-testid={`communications-metric-${label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}>
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{String(value)}</p>
      {helper ? <p className="mt-1 text-xs text-muted-foreground">{helper}</p> : null}
    </div>
  );
}

function RegistryList<T,>({
  title,
  description,
  items,
  emptyMessage,
  renderItem,
  testId,
}: {
  title: string;
  description: string;
  items: T[];
  emptyMessage: string;
  renderItem: (item: T) => React.ReactNode;
  testId: string;
}) {
  return (
    <section className="rounded-lg border p-4" data-testid={testId}>
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      <div className="mt-4 space-y-3">
        {items.length === 0 ? <p className="text-sm text-muted-foreground">{emptyMessage}</p> : items.map(renderItem)}
      </div>
    </section>
  );
}

function useOverview() {
  return useQuery({ queryKey: ['communications:overview'], queryFn: communicationsApi.getOverview, staleTime: 30000 });
}
function useNotifications() {
  return useQuery({ queryKey: ['communications:notifications'], queryFn: communicationsApi.getNotifications, staleTime: 30000 });
}
function useNotificationsSummary() {
  return useQuery({ queryKey: ['communications:notifications-summary'], queryFn: communicationsApi.getNotificationsSummary, staleTime: 30000 });
}
function useAnnouncements() {
  return useQuery({ queryKey: ['communications:announcements'], queryFn: communicationsApi.getAnnouncements, staleTime: 30000 });
}
function useAnnouncementsSummary() {
  return useQuery({ queryKey: ['communications:announcements-summary'], queryFn: communicationsApi.getAnnouncementsSummary, staleTime: 30000 });
}
function useTemplates() {
  return useQuery({ queryKey: ['communications:templates'], queryFn: communicationsApi.getTemplates, staleTime: 30000 });
}
function useTemplatesSummary() {
  return useQuery({ queryKey: ['communications:templates-summary'], queryFn: communicationsApi.getTemplatesSummary, staleTime: 30000 });
}
function usePreferences() {
  return useQuery({ queryKey: ['communications:preferences'], queryFn: communicationsApi.getPreferences, staleTime: 30000 });
}
function usePreferencesSummary() {
  return useQuery({ queryKey: ['communications:preferences-summary'], queryFn: communicationsApi.getPreferencesSummary, staleTime: 30000 });
}
function useDeliveryAudit() {
  return useQuery({ queryKey: ['communications:delivery-audit'], queryFn: communicationsApi.getDeliveryAudit, staleTime: 30000 });
}
function useDeliveryAuditSummary() {
  return useQuery({ queryKey: ['communications:delivery-audit-summary'], queryFn: communicationsApi.getDeliveryAuditSummary, staleTime: 30000 });
}
function useEscalations() {
  return useQuery({ queryKey: ['communications:escalations'], queryFn: communicationsApi.getEscalations, staleTime: 30000 });
}
function useEscalationsSummary() {
  return useQuery({ queryKey: ['communications:escalations-summary'], queryFn: communicationsApi.getEscalationsSummary, staleTime: 30000 });
}
function useProviderReadiness() {
  return useQuery({ queryKey: ['communications:provider-readiness'], queryFn: communicationsApi.getProviderReadiness, staleTime: 30000 });
}
function useBrainActions() {
  return useQuery({ queryKey: ['communications:brain-actions'], queryFn: communicationsApi.getBrainActions, staleTime: 30000 });
}

function PageError(message: string, error: unknown) {
  return <ErrorState error={error} message={message} />;
}

export function CommunicationsOverviewPage() {
  const runtimeShell = useOverview();
  if (runtimeShell.isPending) return <LoadingState title="Loading Communications overview" />;
  if (runtimeShell.error) return PageError('Failed to load Communications overview.', runtimeShell.error);
  if (!runtimeShell.data) return <ErrorState message="Communications overview is unavailable." />;

  return (
    <RequirePermission permission={COMMUNICATIONS_PERMISSIONS.summaryRead}>
      <Shell title="Communications Overview" description="Read-only communications runtime shell covering notifications, announcements, templates, preferences, delivery audit, escalation readiness, providers, and brain action boundaries." currentPath={COMMUNICATIONS_ROUTES.overview}>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" data-testid="comm-overview-main">
          <MetricCard label="Domains" value={runtimeShell.data.total_domains} helper="Canonical domain registry" />
          <MetricCard label="Planned tables" value={runtimeShell.data.total_planned_tables} helper="Planning-only foundation" />
          <MetricCard label="Core permissions" value={runtimeShell.data.total_core_permissions} helper="Read-only A-054 scope" />
          <MetricCard label="Production ready" value={String(runtimeShell.data.production_ready)} helper="Must remain false" />
        </div>
        <RegistryList<CommDomainSummary>
          title="Domain registry"
          description="All planned communications domains with workflow and provider boundary state."
          items={runtimeShell.data.domains}
          emptyMessage="No communications domains available."
          testId="comm-domains-list"
          renderItem={(item) => (
            <div key={item.domain_key} className="rounded border p-3 text-sm">
              <div className="font-medium">{item.display_name}</div>
              <div className="text-xs text-muted-foreground">{item.domain_key}</div>
              <div className="mt-2 grid gap-1 md:grid-cols-2">
                <p>workflow: {item.workflow_status}</p>
                <p>tables: {item.planned_table_groups}</p>
                <p>provider boundary: {String(item.provider_boundary)}</p>
                <p>brain signal applicable: {String(item.brain_signal_applicable)}</p>
              </div>
            </div>
          )}
        />
        <RegistryList<ProviderReadinessSummary>
          title="Provider readiness"
          description="Provider readiness only. No live delivery is claimed."
          items={runtimeShell.data.provider_readiness}
          emptyMessage="No provider readiness entries available."
          testId="comm-provider-readiness-list"
          renderItem={(item) => (
            <div key={item.provider_key} className="rounded border p-3 text-sm">
              <div className="font-medium">{item.provider_key}</div>
              <div>{item.integration_status} / {item.credential_status}</div>
              <div className="text-xs text-muted-foreground">{item.no_live_delivery_reason}</div>
            </div>
          )}
        />
        <RegistryList<BrainActionBoundaryItem>
          title="Brain action boundaries"
          description="Communications brain actions remain approval-gated and non-executing in this phase."
          items={runtimeShell.data.brain_action_samples}
          emptyMessage="No brain action samples available."
          testId="comm-brain-actions-list"
          renderItem={(item) => (
            <div key={`${item.source_signal_type}-${item.recommended_action}`} className="rounded border p-3 text-sm">
              <div className="font-medium">{item.source_signal_type}</div>
              <div>action: {item.recommended_action}</div>
              <div>approval required: {String(item.approval_required)}</div>
              <div className="text-xs text-muted-foreground">policy gates: {item.policy_gates.join(', ')}</div>
            </div>
          )}
        />
        <BoundaryPanel items={runtimeShell.data.safety_constraints} />
      </Shell>
    </RequirePermission>
  );
}

export function CommunicationsNotificationsPage() {
  const summary = useNotificationsSummary();
  const notifications = useNotifications();
  if (summary.isPending || notifications.isPending) return <LoadingState title="Loading notification center" />;
  if (summary.error || notifications.error) return PageError('Failed to load notification center.', summary.error ?? notifications.error);
  if (!summary.data || !notifications.data) return <ErrorState message="Notification center is unavailable." />;

  return (
    <RequirePermission permission={COMMUNICATIONS_PERMISSIONS.notificationsRead}>
      <Shell title="Notification Center" description="Read-only notification center slice with provider boundary visibility only." currentPath={COMMUNICATIONS_ROUTES.notifications}>
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Total notifications" value={summary.data.total_notifications} />
          <MetricCard label="Unread" value={summary.data.unread_notifications} />
          <MetricCard label="High priority" value={summary.data.high_priority_notifications} />
        </div>
        <RegistryList<NotificationCenterItem>
          title="Notifications"
          description="Internal notification inventory with no live provider claim."
          items={notifications.data.notifications}
          emptyMessage="No notifications available."
          testId="comm-notif-list"
          renderItem={(item) => (
            <div key={item.notification_id} className="rounded border p-3 text-sm">
              <div className="font-medium">{item.title}</div>
              <div>{item.message_preview}</div>
              <div className="text-xs text-muted-foreground">{item.internal_status} / {item.external_delivery_status}</div>
            </div>
          )}
        />
        <BoundaryPanel items={COMMUNICATIONS_BOUNDARY_COPY} />
      </Shell>
    </RequirePermission>
  );
}

export function CommunicationsAnnouncementsPage() {
  const summary = useAnnouncementsSummary();
  const announcements = useAnnouncements();
  if (summary.isPending || announcements.isPending) return <LoadingState title="Loading announcement registry" />;
  if (summary.error || announcements.error) return PageError('Failed to load announcement registry.', summary.error ?? announcements.error);
  if (!summary.data || !announcements.data) return <ErrorState message="Announcement registry is unavailable." />;

  return (
    <RequirePermission permission={COMMUNICATIONS_PERMISSIONS.announcementsRead}>
      <Shell title="Announcement Registry" description="Read-only announcement registry with no publish or broadcast workflow execution." currentPath={COMMUNICATIONS_ROUTES.announcements}>
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Total announcements" value={summary.data.total_announcements} />
          <MetricCard label="Active" value={summary.data.active_announcements} />
          <MetricCard label="Expiring soon" value={summary.data.expiring_soon_announcements} />
        </div>
        <RegistryList<AnnouncementRegistryItem>
          title="Announcements"
          description="Read-only institutional announcement inventory."
          items={announcements.data.announcements}
          emptyMessage="No announcements available."
          testId="comm-announcement-list"
          renderItem={(item) => (
            <div key={item.announcement_id} className="rounded border p-3 text-sm">
              <div className="font-medium">{item.title}</div>
              <div>{item.category} / {item.audience_scope}</div>
              <div className="text-xs text-muted-foreground">publish workflow: {String(item.publish_workflow_enabled)} | broadcast: {String(item.broadcast_enabled)}</div>
            </div>
          )}
        />
        <BoundaryPanel items={COMMUNICATIONS_BOUNDARY_COPY} />
      </Shell>
    </RequirePermission>
  );
}

export function CommunicationsTemplatesPage() {
  const summary = useTemplatesSummary();
  const templates = useTemplates();
  if (summary.isPending || templates.isPending) return <LoadingState title="Loading message templates" />;
  if (summary.error || templates.error) return PageError('Failed to load message templates.', summary.error ?? templates.error);
  if (!summary.data || !templates.data) return <ErrorState message="Message template registry is unavailable." />;

  return (
    <RequirePermission permission={COMMUNICATIONS_PERMISSIONS.templatesRead}>
      <Shell title="Message Templates" description="Read-only message template registry with no template send execution." currentPath={COMMUNICATIONS_ROUTES.templates}>
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Total templates" value={summary.data.total_templates} />
          <MetricCard label="Active templates" value={summary.data.active_templates} />
          <MetricCard label="Channels covered" value={summary.data.channels_covered} />
        </div>
        <RegistryList<MessageTemplateRegistryItem>
          title="Templates"
          description="Read-only template inventory."
          items={templates.data.templates}
          emptyMessage="No templates available."
          testId="comm-templates-list"
          renderItem={(item) => (
            <div key={item.template_id} className="rounded border p-3 text-sm">
              <div className="font-medium">{item.template_name}</div>
              <div>{item.channel_type} / {item.locale}</div>
              <div className="text-xs text-muted-foreground">template send enabled: {String(item.template_send_enabled)}</div>
            </div>
          )}
        />
        <BoundaryPanel items={COMMUNICATIONS_BOUNDARY_COPY} />
      </Shell>
    </RequirePermission>
  );
}

export function CommunicationsPreferencesPage() {
  const summary = usePreferencesSummary();
  const preferences = usePreferences();
  if (summary.isPending || preferences.isPending) return <LoadingState title="Loading notification preferences" />;
  if (summary.error || preferences.error) return PageError('Failed to load notification preferences.', summary.error ?? preferences.error);
  if (!summary.data || !preferences.data) return <ErrorState message="Notification preferences are unavailable." />;

  return (
    <RequirePermission permission={COMMUNICATIONS_PERMISSIONS.preferencesRead}>
      <Shell title="Notification Preferences" description="Read-only preference registry. Mutation workflows remain deferred." currentPath={COMMUNICATIONS_ROUTES.preferences}>
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Total preferences" value={summary.data.total_preferences} />
          <MetricCard label="Default preferences" value={summary.data.default_preferences} />
          <MetricCard label="Audience segments" value={summary.data.audience_segments} />
        </div>
        <RegistryList<NotificationPreferenceRegistryItem>
          title="Preferences"
          description="Read-only audience and channel preference inventory."
          items={preferences.data.preferences}
          emptyMessage="No preferences available."
          testId="comm-preferences-list"
          renderItem={(item) => (
            <div key={item.preference_id} className="rounded border p-3 text-sm">
              <div className="font-medium">{item.audience_type}</div>
              <div>{item.channel_type} / {item.preference_scope}</div>
              <div className="text-xs text-muted-foreground">preference mutation enabled: {String(item.preference_mutation_enabled)}</div>
            </div>
          )}
        />
        <BoundaryPanel items={COMMUNICATIONS_BOUNDARY_COPY} />
      </Shell>
    </RequirePermission>
  );
}

export function CommunicationsDeliveryAuditPage() {
  const summary = useDeliveryAuditSummary();
  const audit = useDeliveryAudit();
  if (summary.isPending || audit.isPending) return <LoadingState title="Loading delivery audit" />;
  if (summary.error || audit.error) return PageError('Failed to load delivery audit.', summary.error ?? audit.error);
  if (!summary.data || !audit.data) return <ErrorState message="Delivery audit is unavailable." />;

  return (
    <RequirePermission permission={COMMUNICATIONS_PERMISSIONS.auditRead}>
      <Shell title="Delivery Audit" description="Read-only delivery audit trail with anti-fake provider and delivery-success boundaries." currentPath={COMMUNICATIONS_ROUTES.deliveryAudit}>
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Audit events" value={summary.data.total_audit_events} />
          <MetricCard label="Pending internal" value={summary.data.pending_internal_events} />
          <MetricCard label="Policy review" value={summary.data.policy_review_events} />
        </div>
        <RegistryList<DeliveryAuditEventItem>
          title="Audit events"
          description="Read-only delivery audit records."
          items={audit.data.events}
          emptyMessage="No delivery audit events available."
          testId="comm-delivery-audit-list"
          renderItem={(item) => (
            <div key={item.audit_event_id} className="rounded border p-3 text-sm">
              <div className="font-medium">{item.event_type}</div>
              <div>{item.channel_type} / {item.audience_scope}</div>
              <div className="text-xs text-muted-foreground">delivery success claimed: {String(item.delivery_success_claimed)}</div>
            </div>
          )}
        />
        <BoundaryPanel items={COMMUNICATIONS_BOUNDARY_COPY} />
      </Shell>
    </RequirePermission>
  );
}

export function CommunicationsEscalationsPage() {
  const summary = useEscalationsSummary();
  const escalations = useEscalations();
  if (summary.isPending || escalations.isPending) return <LoadingState title="Loading escalation readiness" />;
  if (summary.error || escalations.error) return PageError('Failed to load escalation readiness.', summary.error ?? escalations.error);
  if (!summary.data || !escalations.data) return <ErrorState message="Escalation readiness is unavailable." />;

  return (
    <RequirePermission permission={COMMUNICATIONS_PERMISSIONS.escalationsRead}>
      <Shell title="Escalation Workflow" description="Read-only escalation workflow readiness. No autonomous escalation is executed in this phase." currentPath={COMMUNICATIONS_ROUTES.escalations}>
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Workflows" value={summary.data.total_workflows} />
          <MetricCard label="Approval gated" value={summary.data.approval_gated_workflows} />
          <MetricCard label="Critical policy" value={summary.data.critical_policy_workflows} />
        </div>
        <RegistryList<EscalationWorkflowItem>
          title="Escalation readiness"
          description="Read-only escalation workflow metadata."
          items={escalations.data.workflows}
          emptyMessage="No escalation workflows available."
          testId="comm-escalations-list"
          renderItem={(item) => (
            <div key={item.escalation_id} className="rounded border p-3 text-sm">
              <div className="font-medium">{item.workflow_type}</div>
              <div>{item.approval_level} / {item.policy_gate}</div>
              <div className="text-xs text-muted-foreground">autonomous escalation: {String(item.autonomous_escalation_enabled)}</div>
            </div>
          )}
        />
        <BoundaryPanel items={COMMUNICATIONS_BOUNDARY_COPY} />
      </Shell>
    </RequirePermission>
  );
}

export function CommunicationsProviderReadinessPage() {
  const readiness = useProviderReadiness();
  if (readiness.isPending) return <LoadingState title="Loading provider readiness" />;
  if (readiness.error) return PageError('Failed to load provider readiness.', readiness.error);
  if (!readiness.data) return <ErrorState message="Provider readiness is unavailable." />;

  return (
    <RequirePermission permission={COMMUNICATIONS_PERMISSIONS.providersRead}>
      <Shell title="Provider Readiness" description="Provider readiness only. No live delivery, no connected providers, no external provider claim." currentPath={COMMUNICATIONS_ROUTES.providerReadiness}>
        <RegistryList<ProviderReadinessSummary>
          title="Providers"
          description="Read-only provider readiness inventory."
          items={readiness.data.providers}
          emptyMessage="No provider readiness entries available."
          testId="comm-provider-readiness-page"
          renderItem={(item) => (
            <div key={item.provider_key} className="rounded border p-3 text-sm">
              <div className="font-medium">{item.provider_key}</div>
              <div>{item.integration_status} / {item.credential_status}</div>
              <div className="text-xs text-muted-foreground">{item.no_live_delivery_reason}</div>
            </div>
          )}
        />
        <BoundaryPanel items={COMMUNICATIONS_BOUNDARY_COPY} />
      </Shell>
    </RequirePermission>
  );
}

export function CommunicationsBrainActionsPage() {
  const actions = useBrainActions();
  if (actions.isPending) return <LoadingState title="Loading brain action boundaries" />;
  if (actions.error) return PageError('Failed to load brain action boundaries.', actions.error);
  if (!actions.data) return <ErrorState message="Brain action boundaries are unavailable." />;

  return (
    <RequirePermission permission={COMMUNICATIONS_PERMISSIONS.brainActionsRead}>
      <Shell title="Brain Actions" description="Advisory-only communication action proposals with approval gates and no execution rights." currentPath={COMMUNICATIONS_ROUTES.brainActions}>
        <RegistryList<BrainActionBoundaryItem>
          title="Brain action proposals"
          description="Read-only communications action boundary samples."
          items={actions.data.samples}
          emptyMessage="No brain action samples available."
          testId="comm-brain-actions-page"
          renderItem={(item) => (
            <div key={`${item.source_signal_type}-${item.recommended_action}`} className="rounded border p-3 text-sm">
              <div className="font-medium">{item.source_signal_type}</div>
              <div>recommended action: {item.recommended_action}</div>
              <div>approval required: {String(item.approval_required)}</div>
              <div className="text-xs text-muted-foreground">{item.policy_gates.join(', ')}</div>
            </div>
          )}
        />
        <BoundaryPanel items={COMMUNICATIONS_BOUNDARY_COPY} />
      </Shell>
    </RequirePermission>
  );
}
