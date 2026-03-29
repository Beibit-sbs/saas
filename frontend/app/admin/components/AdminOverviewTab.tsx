import type { AdminCopy, DashboardSnapshot, InlineFeedback, TxFn } from "../types";

type AdminOverviewTabProps = {
  l: AdminCopy;
  tx: TxFn;
  dashboardStamp: string;
  dashboardLoading: boolean;
  overviewFeedback: InlineFeedback | null;
  dashboardSnapshot: DashboardSnapshot | null;
  enabledLanguageCodes: string;
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
  onRefresh,
}: AdminOverviewTabProps) {
  return (
    <div className="grid2">
      <article className="panelCard">
        <h2>{tx("overviewLive")}</h2>
        <p className="subText">
          {tx("overviewLastRefresh")}: {dashboardStamp}
          {dashboardLoading ? ` · ${tx("loading")}` : ""}
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
                <span>{tx("overviewBackend")}</span>
                <span className={`badge ${dashboardSnapshot.system.backend_health === "ok" ? "badgeOk" : "badgeErr"}`}>
                  {dashboardSnapshot.system.backend_health}
                </span>
              </div>
              <div className="statusItem">
                <span>{tx("overviewApi")}</span>
                <span className={`badge ${dashboardSnapshot.system.api_health === "ok" ? "badgeOk" : "badgeErr"}`}>
                  {dashboardSnapshot.system.api_health}
                </span>
              </div>
              <div className="statusItem">
                <span>{tx("overviewLdap")}</span>
                <span className={`badge ${dashboardSnapshot.integrations.ldap.enabled && dashboardSnapshot.integrations.ldap.configured ? "badgeOk" : dashboardSnapshot.integrations.ldap.enabled ? "badgeWarn" : "badgeInfo"}`}>
                  {dashboardSnapshot.integrations.ldap.enabled
                    ? (dashboardSnapshot.integrations.ldap.configured ? tx("configured") : tx("notConfigured"))
                    : tx("disabled")}
                </span>
              </div>
              <div className="statusItem">
                <span>{tx("overviewAi")}</span>
                <span className={`badge ${dashboardSnapshot.integrations.ai_providers.configured_count > 0 ? "badgeOk" : "badgeWarn"}`}>
                  {dashboardSnapshot.integrations.ai_providers.configured_count}/{dashboardSnapshot.integrations.ai_providers.total_count}
                </span>
              </div>
              <div className="statusItem">
                <span>{tx("overviewLastBackup")}</span>
                <span className={`badge ${dashboardSnapshot.backups.last_job?.status === "success" ? "badgeOk" : dashboardSnapshot.backups.last_job ? "badgeWarn" : "badgeInfo"}`}>
                  {dashboardSnapshot.backups.last_job?.status || tx("none")}
                </span>
              </div>
              <div className="statusItem">
                <span>{tx("overviewRecentAudit")}</span>
                <span className={`badge ${dashboardSnapshot.audit.last_event?.result === "failed" ? "badgeErr" : dashboardSnapshot.audit.recent_events_count > 0 ? "badgeOk" : "badgeInfo"}`}>
                  {dashboardSnapshot.audit.recent_events_count}
                </span>
              </div>
            </div>

            <ul className="plainList" style={{ marginTop: 12 }}>
              <li>{tx("overviewUsers")}: {dashboardSnapshot.users.local_users_count}</li>
              <li>{tx("overviewRoles")}: {dashboardSnapshot.rbac.roles_count}</li>
              <li>{tx("overviewAssignments")}: {dashboardSnapshot.rbac.assignments_count}</li>
              <li>
                {tx("overviewEnabledLanguages")}: {dashboardSnapshot.languages.enabled_count} / {dashboardSnapshot.languages.total_count}
                {enabledLanguageCodes ? ` (${enabledLanguageCodes})` : ""}
              </li>
              <li>
                {tx("overviewLastBackup")}: {dashboardSnapshot.backups.last_job?.finished_at || tx("none")}
                {dashboardSnapshot.backups.last_job?.profile_id ? ` · ${dashboardSnapshot.backups.last_job.profile_id}` : ""}
                {typeof dashboardSnapshot.backups.last_job?.size_bytes === "number" ? ` · ${dashboardSnapshot.backups.last_job.size_bytes} B` : ""}
              </li>
              <li>
                {tx("overviewLastAudit")}: {dashboardSnapshot.audit.last_event?.timestamp || tx("none")}
                {dashboardSnapshot.audit.last_event ? ` · ${dashboardSnapshot.audit.last_event.actor} · ${dashboardSnapshot.audit.last_event.action} · ${dashboardSnapshot.audit.last_event.result || "success"}` : ""}
              </li>
            </ul>
          </>
        ) : (
          <p className="subText">{tx("overviewNoData")}</p>
        )}
        <div className="rowButtons">
          <button type="button" className="ghost" onClick={() => void onRefresh()} disabled={dashboardLoading}>
            {dashboardLoading ? tx("loading") : tx("overviewRefresh")}
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
    </div>
  );
}