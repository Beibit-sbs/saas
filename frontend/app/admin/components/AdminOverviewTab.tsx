import type { AdminCopy, DashboardSnapshot, ExampleReferenceItem, InlineFeedback, TxFn } from "../types";

type AdminOverviewTabProps = {
  l: AdminCopy;
  tx: TxFn;
  dashboardStamp: string;
  dashboardLoading: boolean;
  overviewFeedback: InlineFeedback | null;
  dashboardSnapshot: DashboardSnapshot | null;
  enabledLanguageCodes: string;
  exampleReferenceItems: ExampleReferenceItem[];
  onRefresh: () => void | Promise<void>;
};

export function AdminOverviewTab({
  l,
  tx,
  dashboardStamp,
  dashboardLoading,
  overviewFeedback,
  dashboardSnapshot,
  enabledLanguageCodes,
  exampleReferenceItems,
  onRefresh,
}: AdminOverviewTabProps) {
  return (
    <div className="grid2">
      <article className="panelCard">
        <h2>{tx("overviewLive", "Live operational snapshot")}</h2>
        <p className="subText">
          {tx("overviewLastRefresh", "Last refresh")}: {dashboardStamp}
          {dashboardLoading ? ` · ${tx("loading", "Loading...")}` : ""}
        </p>
        {overviewFeedback ? (
          <p className={`inlineFeedback inlineFeedback${overviewFeedback.tone === "error" ? "Error" : overviewFeedback.tone === "success" ? "Success" : "Info"}`}>
            {overviewFeedback.message}
          </p>
        ) : null}
        {dashboardSnapshot ? (
          <>
            <div className="statusGrid">
              <div className="statusItem">
                <span>{tx("overviewBackend", "Backend health")}</span>
                <span className={`badge ${dashboardSnapshot.system.backend_health === "ok" ? "badgeOk" : "badgeErr"}`}>
                  {dashboardSnapshot.system.backend_health}
                </span>
              </div>
              <div className="statusItem">
                <span>{tx("overviewApi", "API health")}</span>
                <span className={`badge ${dashboardSnapshot.system.api_health === "ok" ? "badgeOk" : "badgeErr"}`}>
                  {dashboardSnapshot.system.api_health}
                </span>
              </div>
              <div className="statusItem">
                <span>{tx("overviewLdap", "LDAP")}</span>
                <span className={`badge ${dashboardSnapshot.integrations.ldap.enabled && dashboardSnapshot.integrations.ldap.configured ? "badgeOk" : dashboardSnapshot.integrations.ldap.enabled ? "badgeWarn" : "badgeInfo"}`}>
                  {dashboardSnapshot.integrations.ldap.enabled
                    ? (dashboardSnapshot.integrations.ldap.configured ? tx("configured", "Configured") : tx("notConfigured", "Not configured"))
                    : tx("disabled", "Disabled")}
                </span>
              </div>
              <div className="statusItem">
                <span>{tx("overviewAi", "Configured AI providers")}</span>
                <span className={`badge ${dashboardSnapshot.integrations.ai_providers.configured_count > 0 ? "badgeOk" : "badgeWarn"}`}>
                  {dashboardSnapshot.integrations.ai_providers.configured_count}/{dashboardSnapshot.integrations.ai_providers.total_count}
                </span>
              </div>
              <div className="statusItem">
                <span>{tx("overviewLastBackup", "Last backup")}</span>
                <span className={`badge ${dashboardSnapshot.backups.last_job?.status === "success" ? "badgeOk" : dashboardSnapshot.backups.last_job ? "badgeWarn" : "badgeInfo"}`}>
                  {dashboardSnapshot.backups.last_job?.status || tx("none", "None")}
                </span>
              </div>
              <div className="statusItem">
                <span>{tx("overviewRecentAudit", "Recent audit events")}</span>
                <span className={`badge ${dashboardSnapshot.audit.last_event?.result === "failed" ? "badgeErr" : dashboardSnapshot.audit.recent_events_count > 0 ? "badgeOk" : "badgeInfo"}`}>
                  {dashboardSnapshot.audit.recent_events_count}
                </span>
              </div>
            </div>

            <ul className="plainList" style={{ marginTop: 12 }}>
              <li>{tx("overviewUsers", "Local users")}: {dashboardSnapshot.users.local_users_count}</li>
              <li>{tx("overviewRoles", "Roles")}: {dashboardSnapshot.rbac.roles_count}</li>
              <li>{tx("overviewAssignments", "Assignments")}: {dashboardSnapshot.rbac.assignments_count}</li>
              <li>
                {tx("overviewEnabledLanguages", "Enabled languages")}: {dashboardSnapshot.languages.enabled_count} / {dashboardSnapshot.languages.total_count}
                {enabledLanguageCodes ? ` (${enabledLanguageCodes})` : ""}
              </li>
              <li>
                {tx("overviewLastBackup", "Last backup")}: {dashboardSnapshot.backups.last_job?.finished_at || tx("none", "None")}
                {dashboardSnapshot.backups.last_job?.profile_id ? ` · ${dashboardSnapshot.backups.last_job.profile_id}` : ""}
                {typeof dashboardSnapshot.backups.last_job?.size_bytes === "number" ? ` · ${dashboardSnapshot.backups.last_job.size_bytes} B` : ""}
              </li>
              <li>
                {tx("overviewLastAudit", "Last audit event")}: {dashboardSnapshot.audit.last_event?.timestamp || tx("none", "None")}
                {dashboardSnapshot.audit.last_event ? ` · ${dashboardSnapshot.audit.last_event.actor} · ${dashboardSnapshot.audit.last_event.action} · ${dashboardSnapshot.audit.last_event.result || "success"}` : ""}
              </li>
            </ul>
          </>
        ) : (
          <p className="subText">{tx("overviewNoData", "No snapshot loaded yet.")}</p>
        )}
        <div className="rowButtons">
          <button type="button" className="ghost" onClick={() => void onRefresh()} disabled={dashboardLoading}>
            {dashboardLoading ? tx("loading", "Loading...") : tx("overviewRefresh", "Refresh snapshot")}
          </button>
        </div>
      </article>
      <article className="panelCard">
        <h2>{l.platformModules}</h2>
        <ul className="plainList">
          <li>{l.usersRoles}</li>
          <li>{l.ldapSettings}</li>
          <li>{l.aiControls}</li>
          <li>{l.auditEvents}</li>
        </ul>
      </article>
      <article className="panelCard">
        <h2>{l.operationalFocus}</h2>
        <ul className="plainList">
          <li>{l.trackChanges}</li>
          <li>{l.keepI18n}</li>
          <li>{l.controlledExceptions}</li>
          <li>{l.documentActions}</li>
        </ul>
      </article>
      <article className="panelCard">
        <h2>{tx("exampleSliceTitle", "Example Vertical Slice")}</h2>
        <p className="subText">{tx("exampleSliceHelp", "Reference-only module for derived projects: route + RBAC + audit.")}</p>
        {exampleReferenceItems.length === 0 ? (
          <p className="subText">{tx("exampleSliceEmpty", "No example items loaded.")}</p>
        ) : (
          <ul className="plainList">
            {exampleReferenceItems.map((item) => (
              <li key={item.key}>
                <b>{item.title}</b> ({item.key})
                <br />
                {tx("exampleSlicePermission", "Permission")}: {item.required_permission} | {tx("exampleSliceAudit", "Audit action")}: {item.audit_action}
              </li>
            ))}
          </ul>
        )}
      </article>
    </div>
  );
}