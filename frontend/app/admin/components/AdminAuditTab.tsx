import type { AdminCopy, AuditEvent, AuditExportBusy, InlineFeedback, TxFn } from "../types";
import { formatAuditTimestamp } from "../utils";

type AdminAuditTabProps = {
  l: AdminCopy;
  tx: TxFn;
  auditActor: string;
  auditAction: string;
  auditEntity: string;
  auditResult: string;
  auditCorrelationId: string;
  auditSince: string;
  auditLoading: boolean;
  auditExportBusy: AuditExportBusy;
  auditFeedback: InlineFeedback | null;
  hasActiveAuditFilters: boolean;
  auditEvents: AuditEvent[];
  auditLatestTimestamp: string;
  auditFilterBadges: string[];
  onAuditActorChange: (value: string) => void;
  onAuditActionChange: (value: string) => void;
  onAuditEntityChange: (value: string) => void;
  onAuditResultChange: (value: string) => void;
  onAuditCorrelationIdChange: (value: string) => void;
  onAuditSinceChange: (value: string) => void;
  onLoadAuditEvents: () => void | Promise<void>;
  onClearAuditFilters: () => void;
  onExportAudit: (format: "csv" | "json") => void | Promise<void>;
};

export function AdminAuditTab({
  l,
  tx,
  auditActor,
  auditAction,
  auditEntity,
  auditResult,
  auditCorrelationId,
  auditSince,
  auditLoading,
  auditExportBusy,
  auditFeedback,
  hasActiveAuditFilters,
  auditEvents,
  auditLatestTimestamp,
  auditFilterBadges,
  onAuditActorChange,
  onAuditActionChange,
  onAuditEntityChange,
  onAuditResultChange,
  onAuditCorrelationIdChange,
  onAuditSinceChange,
  onLoadAuditEvents,
  onClearAuditFilters,
  onExportAudit,
}: AdminAuditTabProps) {
  return (
    <div className="grid2">
      <article className="panelCard">
        <div className="sectionHeader">
          <h2>{l.auditVisibility}</h2>
        </div>
        <p className="subText">{l.auditHelp}</p>
        <div className="formGrid compactFormGrid filterGrid">
          <input value={auditActor} onChange={(e) => onAuditActorChange(e.target.value)} placeholder={tx("auditActorFilter")} />
          <input value={auditAction} onChange={(e) => onAuditActionChange(e.target.value)} placeholder={tx("auditActionFilter")} />
          <input value={auditEntity} onChange={(e) => onAuditEntityChange(e.target.value)} placeholder={tx("auditEntityFilter")} />
          <input value={auditResult} onChange={(e) => onAuditResultChange(e.target.value)} placeholder={tx("auditResultFilter")} />
          <input value={auditCorrelationId} onChange={(e) => onAuditCorrelationIdChange(e.target.value)} placeholder={tx("auditCorrelationFilter")} />
          <input value={auditSince} onChange={(e) => onAuditSinceChange(e.target.value)} placeholder={tx("auditSinceFilter")} />
        </div>
        <div className="rowButtons">
          <button type="button" className="primary" onClick={() => void onLoadAuditEvents()} disabled={auditLoading || auditExportBusy !== ""}>{auditLoading ? tx("auditLoading") : tx("loadAuditEvents")}</button>
          <button type="button" className="ghost" onClick={onClearAuditFilters} disabled={auditLoading || auditExportBusy !== ""}>{tx("auditClearFilters")}</button>
          <button type="button" className="ghost" onClick={() => void onExportAudit("csv")} disabled={auditLoading || auditExportBusy !== ""}>{auditExportBusy === "csv" ? tx("auditExportingCsv") : tx("exportCsv")}</button>
          <button type="button" className="ghost" onClick={() => void onExportAudit("json")} disabled={auditLoading || auditExportBusy !== ""}>{auditExportBusy === "json" ? tx("auditExportingJson") : tx("exportJson")}</button>
        </div>
        {auditFeedback ? (
          <p className={`inlineFeedback inlineFeedback${auditFeedback.tone === "error" ? "Error" : auditFeedback.tone === "success" ? "Success" : "Info"}`}>
            {auditFeedback.message}
          </p>
        ) : null}
        <div className="rowMeta">
          <span className="subText">
            {hasActiveAuditFilters ? tx("auditShowingFilteredEvents").replace("{count}", String(auditEvents.length)) : tx("auditShowingEvents").replace("{count}", String(auditEvents.length))}
          </span>
          <span className="subText">{tx("auditLastEvent")}: {formatAuditTimestamp(auditLatestTimestamp)}</span>
        </div>
        <div className="rowMeta">
          {hasActiveAuditFilters ? (
            <div className="badgeRow">
              {auditFilterBadges.map((item) => (
                <span key={item} className="badge badgeInfo">{item}</span>
              ))}
            </div>
          ) : (
            <span className="subText">{tx("auditNoFiltersActive")}</span>
          )}
        </div>

        {auditEvents.length === 0 ? (
          <p className="subText">{tx("noAuditEvents")}</p>
        ) : (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>{tx("auditTs")}</th>
                  <th>{tx("auditActor")}</th>
                  <th>{tx("auditAction")}</th>
                  <th>{tx("auditEntity")}</th>
                  <th>{tx("auditPath")}</th>
                  <th>{tx("auditResult")}</th>
                  <th>{tx("auditCorrelation")}</th>
                </tr>
              </thead>
              <tbody>
                {auditEvents.map((event) => (
                  <tr key={event.event_id}>
                    <td title={event.timestamp}>{formatAuditTimestamp(event.timestamp)}</td>
                    <td>{event.actor}</td>
                    <td><span className="badge badgeInfo">{event.action}</span></td>
                    <td>{event.entity || "admin"}</td>
                    <td>{event.path}</td>
                    <td>
                      <span className={`badge ${(event.result || "success").toLowerCase() === "success" ? "badgeOk" : (event.result || "").toLowerCase().includes("deny") || (event.result || "").toLowerCase().includes("error") ? "badgeErr" : "badgeWarn"}`}>
                        {event.result || "success"}
                      </span>
                    </td>
                    <td className="truncateMono" title={event.correlation_id}>{event.correlation_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>
      <article className="panelCard">
        <div className="sectionHeader">
          <h2>{l.securityPosture}</h2>
        </div>
        <p className="subText">{l.securityHelp}</p>
        <div className="badgeRow"><span className="badge">{l.rbacEnforced}</span><span className="badge">{l.auditRequired}</span></div>
      </article>
    </div>
  );
}