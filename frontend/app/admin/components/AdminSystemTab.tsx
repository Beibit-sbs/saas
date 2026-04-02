import type { InlineFeedback, SystemHealthResponse } from "../types";

type AdminSystemTabProps = {
  systemHealth: SystemHealthResponse | null;
  loading: boolean;
  feedback: InlineFeedback | null;
  lastUpdated: string;
  onRefresh: () => void | Promise<void>;
};

const formatBytes = (size: number) => {
  if (!Number.isFinite(size) || size < 0) {
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
};

export function AdminSystemTab({
  systemHealth,
  loading,
  feedback,
  lastUpdated,
  onRefresh,
}: AdminSystemTabProps) {
  return (
    <div className="grid2">
      <article className="panelCard">
        <h2>System Health</h2>
        <p className="subText">Last refresh: {lastUpdated}{loading ? " · Loading..." : ""}</p>
        {feedback ? (
          <p className={`inlineFeedback inlineFeedback${feedback.tone === "error" ? "Error" : feedback.tone === "success" ? "Success" : "Info"}`}>
            {feedback.message}
          </p>
        ) : null}
        <div className="statusGrid mt-3">
          <div className="statusItem">
            <span>Status</span>
            <span className={`badge ${(systemHealth?.status || "").toLowerCase() === "ok" ? "badgeOk" : "badgeWarn"}`}>
              {systemHealth?.status || "-"}
            </span>
          </div>
          {Object.entries(systemHealth?.services || {}).map(([name, value]) => (
            <div key={name} className="statusItem">
              <span>{name}</span>
              <span className={`badge ${String(value).toLowerCase() === "ok" || String(value).toLowerCase() === "available" ? "badgeOk" : "badgeWarn"}`}>
                {String(value)}
              </span>
            </div>
          ))}
        </div>
        <div className="rowButtons mt-3">
          <button type="button" className="ghost" onClick={() => void onRefresh()} disabled={loading}>
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>
      </article>

      <article className="panelCard">
        <h2>Metrics</h2>
        {systemHealth ? (
          <ul className="plainList">
            {Object.entries(systemHealth.metrics).map(([key, value]) => (
              <li key={key}><b>{key}</b>: {String(value)}</li>
            ))}
          </ul>
        ) : (
          <p className="subText">No metrics loaded yet.</p>
        )}
      </article>

      <article className="panelCard">
        <h2>Queues</h2>
        {systemHealth ? (
          <ul className="plainList">
            {Object.entries(systemHealth.queues).map(([key, value]) => (
              <li key={key}><b>{key}</b>: {String(value)}</li>
            ))}
          </ul>
        ) : (
          <p className="subText">No queue data loaded yet.</p>
        )}
      </article>

      <article className="panelCard">
        <h2>Disk Usage</h2>
        {systemHealth ? (
          <ul className="plainList">
            <li><b>path</b>: {systemHealth.disk.path}</li>
            <li><b>usage_percent</b>: {systemHealth.disk.usage_percent}%</li>
            <li><b>total</b>: {formatBytes(systemHealth.disk.total_bytes)}</li>
            <li><b>used</b>: {formatBytes(systemHealth.disk.used_bytes)}</li>
            <li><b>free</b>: {formatBytes(systemHealth.disk.free_bytes)}</li>
          </ul>
        ) : (
          <p className="subText">No disk data loaded yet.</p>
        )}
      </article>
    </div>
  );
}
