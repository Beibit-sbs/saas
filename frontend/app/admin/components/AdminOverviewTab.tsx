import type { AdminCopy, AdminInsight, AdminTab, DashboardSnapshot, InlineFeedback, TxFn } from "../types";
import { useEffect, useMemo, useState } from "react";

function formatBytes(size?: number): string {
  if (typeof size !== "number" || !Number.isFinite(size) || size < 0) {
    return "-";
  }
  if (size < 1024) {
    return `${size} B`;
  }
  const kb = size / 1024;
  if (kb < 1024) {
    return `${kb.toFixed(1)} KB`;
  }
  const mb = kb / 1024;
  if (mb < 1024) {
    return `${mb.toFixed(1)} MB`;
  }
  return `${(mb / 1024).toFixed(2)} GB`;
}

function formatStamp(value?: string | null): string {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function percent(part: number, total: number): number {
  if (total <= 0) {
    return 0;
  }
  return Math.round((part / total) * 100);
}

type AdminOverviewTabProps = {
  l: AdminCopy;
  tx: TxFn;
  dashboardStamp: string;
  dashboardLoading: boolean;
  overviewFeedback: InlineFeedback | null;
  dashboardSnapshot: DashboardSnapshot | null;
  decisionInsights: AdminInsight[];
  enabledLanguageCodes: string;
  onRefresh: () => void | Promise<void>;
  onSelectTab?: (tab: AdminTab) => void;
  executiveMode?: boolean;
};

export function AdminOverviewTab({
  l,
  tx,
  dashboardStamp,
  dashboardLoading,
  overviewFeedback,
  dashboardSnapshot,
  decisionInsights,
  enabledLanguageCodes,
  onRefresh,
  onSelectTab,
  executiveMode = false,
}: AdminOverviewTabProps) {
  const lastBackup = dashboardSnapshot?.backups.last_job ?? null;
  const lastAudit = dashboardSnapshot?.audit.last_event ?? null;
  const aiConfigured = dashboardSnapshot?.integrations.ai_providers.configured_count ?? 0;
  const aiTotal = dashboardSnapshot?.integrations.ai_providers.total_count ?? 0;
  const enabledLanguages = dashboardSnapshot?.languages.enabled_count ?? 0;
  const totalLanguages = dashboardSnapshot?.languages.total_count ?? 0;
  const readySignals = [
    dashboardSnapshot?.system.backend_health === "ok",
    dashboardSnapshot?.system.api_health === "ok",
    dashboardSnapshot?.integrations.ldap.configured === true,
    lastBackup?.status === "success",
  ].filter(Boolean).length;
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(!executiveMode);

  useEffect(() => {
    setShowTechnicalDetails(!executiveMode);
  }, [executiveMode]);

  const insightCounters = useMemo(() => {
    const high = decisionInsights.filter((item) => item.impact === "high").length;
    const medium = decisionInsights.filter((item) => item.impact === "medium").length;
    const low = decisionInsights.filter((item) => item.impact === "low").length;
    return { high, medium, low };
  }, [decisionInsights]);

  const primaryInsight = decisionInsights[0] ?? null;
  const summaryTitle = decisionInsights.length > 0
    ? tx("overviewExecutiveDecisionSummaryWithCount").replace("{count}", String(decisionInsights.length))
    : tx("overviewExecutiveDecisionSummaryEmpty");
  const summaryRiskLine = tx("overviewExecutiveRiskCounts")
    .replace("{high}", String(insightCounters.high))
    .replace("{medium}", String(insightCounters.medium))
    .replace("{low}", String(insightCounters.low));

  if (dashboardLoading && !dashboardSnapshot) {
    return (
      <div className="overviewControlCenter">
        <article className="panelCard overviewHeroPanel overviewStateCard" data-testid="overview-state-loading">
          <div className="overviewStateBody">
            <span className="badge badgeInfo">{tx("loading")}</span>
            <h3>{tx("overviewLoadingTitle")}</h3>
            <p className="subText">{tx("overviewLoadingBody")}</p>
          </div>
        </article>
      </div>
    );
  }

  if (!dashboardSnapshot) {
    return (
      <div className="overviewControlCenter">
        <article className="panelCard overviewHeroPanel overviewStateCard" data-testid="overview-state-empty">
          <div className="overviewStateBody">
            <span className={`badge ${overviewFeedback?.tone === "error" ? "badgeErr" : "badgeInfo"}`}>
              {overviewFeedback?.tone === "error" ? tx("errorPrefix") : tx("overviewInsightsTitle")}
            </span>
            <h3>{tx("overviewUnavailableTitle")}</h3>
            <p className="subText">{overviewFeedback?.message || tx("overviewUnavailableBody")}</p>
            <div className="rowButtons">
              <button type="button" className="primary" onClick={() => void onRefresh()} disabled={dashboardLoading}>
                {dashboardLoading ? tx("loading") : tx("overviewRefresh")}
              </button>
            </div>
          </div>
        </article>
      </div>
    );
  }

  return (
    <div className={`overviewControlCenter ${executiveMode ? "overviewControlCenterExecutive" : ""}`}>
      <article className="panelCard overviewHeroPanel">
        <div className="overviewHeroBand">
          <div>
            <p className="kicker">{tx("overviewExecutiveTitle")}</p>
            <h2>{tx("overviewLive")}</h2>
            <p className="overviewHeroCopy">{tx("overviewExecutiveSubtitle")}</p>
          </div>
          <div className="overviewHeroMeta">
            <span className={`badge ${readySignals >= 3 ? "badgeOk" : readySignals >= 2 ? "badgeWarn" : "badgeErr"}`}>
              {readySignals}/4 {tx("overviewCoverage")}
            </span>
            <p>
              {tx("overviewLastRefresh")}: {dashboardStamp}
              {dashboardLoading ? ` · ${tx("loading")}` : ""}
            </p>
          </div>
        </div>

        {overviewFeedback ? (
          <p className={`inlineFeedback inlineFeedback${overviewFeedback.tone === "error" ? "Error" : overviewFeedback.tone === "success" ? "Success" : "Info"}`}>
            {overviewFeedback.message}
          </p>
        ) : null}

        {executiveMode ? (
          <div className="overviewExecutiveBrief" data-testid="overview-executive-brief">
            <article className="overviewExecutiveCard">
              <p className="overviewExecutiveLabel">{tx("overviewExecutiveDecisionSummaryLabel")}</p>
              <strong>{summaryTitle}</strong>
              <p>{summaryRiskLine}</p>
            </article>
            <article className="overviewExecutiveCard">
              <p className="overviewExecutiveLabel">{tx("overviewExecutiveRiskLabel")}</p>
              <strong>{primaryInsight?.title || tx("overviewExecutiveRiskEmptyTitle")}</strong>
              <p>{primaryInsight?.explanation || tx("overviewExecutiveRiskEmptyBody")}</p>
            </article>
            <article className="overviewExecutiveCard">
              <p className="overviewExecutiveLabel">{tx("overviewExecutiveRecommendedLabel")}</p>
              <strong>{primaryInsight?.recommendedAction || tx("overviewExecutiveRecommendedFallback")}</strong>
              <p>
                {tx("overviewExecutiveSourceLabel")}: {primaryInsight?.signal || tx("overviewExecutiveSourceOverview")}
              </p>
            </article>
          </div>
        ) : null}

        <>
            <div className="overviewSignalGrid">
              <button
                type="button"
                className="overviewSignalCard"
                onClick={() => onSelectTab?.("rbac")}
                disabled={!onSelectTab}
                data-testid="overview-kpi-operations"
              >
                <span className="overviewSignalLabel">{tx("overviewKpiOps")}</span>
                <strong>{dashboardSnapshot.users.local_users_count + dashboardSnapshot.rbac.assignments_count}</strong>
                <small>{dashboardSnapshot.rbac.roles_count} {tx("overviewRoles").toLowerCase()} · {dashboardSnapshot.rbac.assignments_count} {tx("overviewAssignments").toLowerCase()}</small>
              </button>

              <button
                type="button"
                className="overviewSignalCard"
                onClick={() => onSelectTab?.("integrations")}
                disabled={!onSelectTab}
                data-testid="overview-kpi-ai"
              >
                <span className="overviewSignalLabel">{tx("overviewKpiAi")}</span>
                <strong>{percent(aiConfigured, aiTotal)}%</strong>
                <small>{aiConfigured}/{aiTotal} · {tx("overviewAi")}</small>
              </button>

              <button
                type="button"
                className="overviewSignalCard"
                onClick={() => onSelectTab?.("backups")}
                disabled={!onSelectTab}
                data-testid="overview-kpi-resilience"
              >
                <span className="overviewSignalLabel">{tx("overviewKpiResilience")}</span>
                <strong>{lastBackup?.status === "success" ? tx("configured") : tx("none")}</strong>
                <small>{tx("overviewLastBackup")}: {formatStamp(lastBackup?.finished_at)}</small>
              </button>

              <button
                type="button"
                className="overviewSignalCard"
                onClick={() => onSelectTab?.("languages")}
                disabled={!onSelectTab}
                data-testid="overview-kpi-languages"
              >
                <span className="overviewSignalLabel">{tx("overviewKpiLanguages")}</span>
                <strong>{percent(enabledLanguages, totalLanguages)}%</strong>
                <small>{enabledLanguages}/{totalLanguages}{enabledLanguageCodes ? ` · ${enabledLanguageCodes}` : ""}</small>
              </button>
            </div>

            <div className="overviewSecondaryGrid">
              <section className="overviewStack">
                <article className="overviewSectionCard overviewSectionCardAccent">
                  <div className="overviewSectionHeader">
                    <div>
                      <h3>{tx("overviewCommandDeckTitle")}</h3>
                      <p className="subText">{tx("overviewCommandDeckSubtitle")}</p>
                    </div>
                    <button type="button" className="ghost" onClick={() => void onRefresh()} disabled={dashboardLoading}>
                      {dashboardLoading ? tx("loading") : tx("overviewRefresh")}
                    </button>
                  </div>

                  <div className="overviewRouteGrid">
                    <button
                      type="button"
                      className="overviewRouteCard"
                      onClick={() => onSelectTab?.("integrations")}
                      disabled={!onSelectTab}
                      data-testid="overview-route-integrations"
                    >
                      <span className="overviewRouteEyebrow">{l.aiControls}</span>
                      <strong>{dashboardSnapshot.integrations.ldap.enabled ? l.ldapSettings : l.aiControls}</strong>
                      <small>{tx("overviewDrilldown")}</small>
                    </button>

                    <button
                      type="button"
                      className="overviewRouteCard"
                      onClick={() => onSelectTab?.("rbac")}
                      disabled={!onSelectTab}
                      data-testid="overview-route-rbac"
                    >
                      <span className="overviewRouteEyebrow">{tx("rbac")}</span>
                      <strong>{l.usersRoles}</strong>
                      <small>{dashboardSnapshot.rbac.assignments_count} {tx("overviewAssignments").toLowerCase()}</small>
                    </button>

                    <button
                      type="button"
                      className="overviewRouteCard"
                      onClick={() => onSelectTab?.("university")}
                      disabled={!onSelectTab}
                      data-testid="overview-route-university"
                    >
                      <span className="overviewRouteEyebrow">{tx("overviewUniversityCore")}</span>
                      <strong>{tx("overviewUniversityFocus")}</strong>
                      <small>{tx("overviewDrilldown")}</small>
                    </button>

                    <button
                      type="button"
                      className="overviewRouteCard"
                      onClick={() => onSelectTab?.("audit")}
                      disabled={!onSelectTab}
                      data-testid="overview-route-audit"
                    >
                      <span className="overviewRouteEyebrow">{l.audit}</span>
                      <strong>{l.auditEvents}</strong>
                      <small>{dashboardSnapshot.audit.recent_events_count} {tx("overviewRecentAudit").toLowerCase()}</small>
                    </button>
                  </div>
                </article>

                {executiveMode ? null : (
                <article className="overviewSectionCard">
                  <div className="overviewSectionHeader">
                    <div>
                      <h3>{tx("overviewActivityTitle")}</h3>
                    </div>
                  </div>
                  <div className="overviewActivityRail">
                    <div className="overviewActivityItem">
                      <span className="badge badgeInfo">{tx("overviewActivitySnapshot")}</span>
                      <div>
                        <strong>{formatStamp(dashboardSnapshot.generated_at)}</strong>
                        <p>{tx("overviewLive")}</p>
                      </div>
                    </div>
                    <div className="overviewActivityItem">
                      <span className={`badge ${lastBackup?.status === "success" ? "badgeOk" : "badgeWarn"}`}>{tx("overviewActivityBackup")}</span>
                      <div>
                        <strong>{lastBackup?.profile_id || tx("none")}</strong>
                        <p>{formatStamp(lastBackup?.finished_at)} · {formatBytes(lastBackup?.size_bytes)}</p>
                      </div>
                    </div>
                    <div className="overviewActivityItem">
                      <span className={`badge ${lastAudit?.result === "failed" ? "badgeErr" : "badgeInfo"}`}>{tx("overviewActivityAudit")}</span>
                      <div>
                        <strong>{lastAudit?.actor || tx("none")}</strong>
                        <p>{lastAudit ? `${lastAudit.action} · ${formatStamp(lastAudit.timestamp)}` : tx("overviewNoData")}</p>
                      </div>
                    </div>
                    <div className="overviewActivityItem">
                      <span className="badge badgeInfo">{tx("overviewActivityLanguages")}</span>
                      <div>
                        <strong>{enabledLanguageCodes || tx("none")}</strong>
                        <p>{enabledLanguages}/{totalLanguages} · {l.keepI18n}</p>
                      </div>
                    </div>
                  </div>
                </article>
                )}
              </section>

              <section className="overviewStack">
                <article className="overviewSectionCard">
                  <div className="overviewSectionHeader">
                    <div>
                      <h3>{tx("overviewInsightsTitle")}</h3>
                      <p className="subText">{tx("overviewInsightsSubtitle")}</p>
                    </div>
                  </div>
                  <div className="overviewInsightList">
                    {decisionInsights.map((item) => {
                      const tone = item.impact === "high" ? "Error" : item.impact === "medium" ? "Warn" : "Info";
                      const badgeTone = item.impact === "high" ? "badgeErr" : item.impact === "medium" ? "badgeWarn" : "badgeInfo";

                      return (
                      <button
                        key={item.id}
                        type="button"
                        className={`overviewInsightCard overviewInsightCard${tone}`}
                        onClick={() => onSelectTab?.(item.tab)}
                        disabled={!onSelectTab}
                        data-testid={`overview-insight-${item.id}`}
                      >
                        <div className="overviewInsightMeta">
                          <span className={`badge ${badgeTone}`}>{item.impact.toUpperCase()}</span>
                          <span className="badge badgeInfo">{item.signal}</span>
                        </div>
                        <strong>{item.title}</strong>
                        <p className="overviewInsightBody">{item.explanation}</p>
                        <div className="overviewInsightAction">
                          <span className="overviewInsightActionLabel">{tx("overviewRecommendedAction")}</span>
                          <span>{item.recommendedAction}</span>
                        </div>
                        <div className="overviewInsightFooter">
                          <span className="overviewInsightFooterLabel">{tx("overviewOpenModule")}</span>
                          <span className="overviewInsightArrow" aria-hidden="true">→</span>
                        </div>
                      </button>
                      );
                    })}
                    {decisionInsights.length === 0 ? <p className="subText">{tx("overviewNoSignalsBody")}</p> : null}
                  </div>
                </article>

                {executiveMode ? null : (
                <article className="overviewSectionCard">
                  <div className="overviewSectionHeader">
                    <div>
                      <h3>{l.operationalFocus}</h3>
                    </div>
                  </div>
                  <ul className="plainList">
                    <li>{l.trackChanges}</li>
                    <li>{l.keepI18n}</li>
                    <li>{l.controlledExceptions}</li>
                    <li>{l.documentActions}</li>
                  </ul>
                </article>
                )}

                {executiveMode ? null : (
                <article className="overviewSectionCard">
                  <div className="overviewSectionHeader">
                    <div>
                      <h3>{l.platformModules}</h3>
                    </div>
                  </div>
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
                      <span>{tx("overviewRecentAudit")}</span>
                      <span className={`badge ${lastAudit?.result === "failed" ? "badgeErr" : dashboardSnapshot.audit.recent_events_count > 0 ? "badgeOk" : "badgeInfo"}`}>
                        {dashboardSnapshot.audit.recent_events_count}
                      </span>
                    </div>
                    <div className="statusItem">
                      <span>{tx("overviewLastBackup")}</span>
                      <span className={`badge ${lastBackup?.status === "success" ? "badgeOk" : lastBackup ? "badgeWarn" : "badgeInfo"}`}>
                        {lastBackup?.status || tx("none")}
                      </span>
                    </div>
                    <div className="statusItem">
                      <span>{tx("overviewEnabledLanguages")}</span>
                      <span className="badge badgeInfo">
                        {enabledLanguages}/{totalLanguages}
                      </span>
                    </div>
                  </div>
                </article>
                )}

                {executiveMode ? (
                  <article className="overviewSectionCard overviewSectionCardTechnicalToggle">
                    <div className="overviewSectionHeader">
                      <div>
                        <h3>{tx("overviewTechnicalDetailsTitle")}</h3>
                        <p className="subText">{tx("overviewTechnicalDetailsSubtitle")}</p>
                      </div>
                      <button
                        type="button"
                        className="ghost"
                        onClick={() => setShowTechnicalDetails((prev) => !prev)}
                        data-testid="overview-technical-toggle"
                      >
                        {showTechnicalDetails ? tx("overviewTechnicalDetailsHide") : tx("overviewTechnicalDetailsShow")}
                      </button>
                    </div>

                    {showTechnicalDetails ? (
                      <div className="overviewTechnicalDetails" data-testid="overview-technical-details">
                        <ul className="plainList">
                          <li>{l.trackChanges}</li>
                          <li>{l.keepI18n}</li>
                          <li>{l.controlledExceptions}</li>
                          <li>{l.documentActions}</li>
                        </ul>
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
                            <span>{tx("overviewLastBackup")}</span>
                            <span className={`badge ${lastBackup?.status === "success" ? "badgeOk" : lastBackup ? "badgeWarn" : "badgeInfo"}`}>
                              {lastBackup?.status || tx("none")}
                            </span>
                          </div>
                        </div>
                      </div>
                    ) : null}
                  </article>
                ) : null}
              </section>
            </div>
          </>
      </article>
    </div>
  );
}