import type { InlineFeedback, JobItem, TxFn } from "../types";
import { formatAuditTimestamp } from "../utils";

type AdminJobsTabProps = {
  tx: TxFn;
  jobsLoading: boolean;
  jobsMutating: boolean;
  jobsFeedback: InlineFeedback | null;
  jobsStatusFilter: string;
  filteredJobs: JobItem[];
  onStatusFilterChange: (value: string) => void;
  onLoadJobs: () => void | Promise<void>;
  onCreateJob: (jobType: string, payload?: Record<string, unknown>) => void | Promise<void>;
  onRetryJob: (jobId: number) => void | Promise<void>;
  onCancelJob: (jobId: number) => void | Promise<void>;
};

export function AdminJobsTab({
  tx,
  jobsLoading,
  jobsMutating,
  jobsFeedback,
  jobsStatusFilter,
  filteredJobs,
  onStatusFilterChange,
  onLoadJobs,
  onCreateJob,
  onRetryJob,
  onCancelJob,
}: AdminJobsTabProps) {
  return (
    <div className="grid2">
      <article className="panelCard">
        <div className="sectionHeader">
          <h2>{"Jobs"}</h2>
        </div>
        <p className="subText">{"Asynchronous job queue and execution state"}</p>
        {jobsFeedback ? (
          <p className={`inlineFeedback inlineFeedback${jobsFeedback.tone === "error" ? "Error" : jobsFeedback.tone === "success" ? "Success" : "Info"}`}>
            {jobsFeedback.message}
          </p>
        ) : null}

        <div className="formGrid compactFormGrid filterGrid">
          <select value={jobsStatusFilter} onChange={(e) => onStatusFilterChange(e.target.value)}>
            <option value="">{"All"}</option>
            <option value="queued">queued</option>
            <option value="running">running</option>
            <option value="succeeded">succeeded</option>
            <option value="failed">failed</option>
            <option value="cancelled">cancelled</option>
          </select>
          <button type="button" className="ghost" onClick={() => void onLoadJobs()} disabled={jobsLoading || jobsMutating}>
            {jobsLoading ? tx("loading", "Loading") : "Refresh jobs"}
          </button>
        </div>

        <div className="rowButtons">
          <button type="button" className="primary" onClick={() => void onCreateJob("backup.run", {})} disabled={jobsMutating}>
            {"Queue backup.run"}
          </button>
          <button type="button" className="ghost" onClick={() => void onCreateJob("audit.export", { format: "json", limit: 200 })} disabled={jobsMutating}>
            {"Queue audit.export"}
          </button>
        </div>
      </article>

      <article className="panelCard">
        <div className="sectionHeader">
          <h2>{"Job history"}</h2>
          <p className="subText">{`Rows: ${filteredJobs.length}`}</p>
        </div>
        {filteredJobs.length === 0 ? (
          <p className="subText">{"No jobs"}</p>
        ) : (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>{"Tenant"}</th>
                  <th>{"Job type"}</th>
                  <th>{"Status"}</th>
                  <th>{"Created at"}</th>
                  <th>{"Retry"}</th>
                  <th>{"Error"}</th>
                  <th>{"Actions"}</th>
                </tr>
              </thead>
              <tbody>
                {filteredJobs.map((job) => (
                  <tr key={job.id}>
                    <td>{job.id}</td>
                    <td>{job.tenant_id}</td>
                    <td>{job.job_type}</td>
                    <td><span className="badge badgeInfo">{job.status}</span></td>
                    <td>{formatAuditTimestamp(job.created_at)}</td>
                    <td>{job.retry_count}/{job.max_retries}</td>
                    <td>{job.error_message || "-"}</td>
                    <td className="actionCell">
                      <div className="rowButtons" style={{ gap: 6 }}>
                        <button
                          type="button"
                          className="ghost"
                          onClick={() => void onRetryJob(job.id)}
                          disabled={jobsMutating || job.status !== "failed"}
                        >
                          {"Retry"}
                        </button>
                        <button
                          type="button"
                          className="ghost danger"
                          onClick={() => void onCancelJob(job.id)}
                          disabled={jobsMutating || (job.status !== "queued" && job.status !== "running")}
                        >
                          {"Cancel"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </div>
  );
}
