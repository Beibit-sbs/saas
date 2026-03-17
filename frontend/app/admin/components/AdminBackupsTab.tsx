import type { AdminCopy, BackupJob, BackupProfile, InlineFeedback, RestoreCandidate, TxFn } from "../types";
import { backupStatusBadgeClass, fileNameFromPath, formatAuditTimestamp, formatBytes } from "../utils";

type AdminBackupsTabProps = {
  tx: TxFn;
  backupAllowedRoots: string[];
  backupFeedback: InlineFeedback | null;
  backupActionsBusy: boolean;
  backupListLoading: boolean;
  backupActiveProfile: string;
  backupProfilesForm: BackupProfile[];
  retentionDays: string;
  retentionMinFiles: string;
  restoreProfileId: string;
  restoreFileName: string;
  restoreCandidates: RestoreCandidate[];
  backupJobsSorted: BackupJob[];
  backupSummaryCount: number;
  backupSummaryLatest: string;
  backupSummaryStatus: string;
  restoreCandidateNames: Set<string>;
  onLoadBackupStatus: (force?: boolean) => void | Promise<void>;
  onBackupActiveProfileChange: (value: string) => void;
  onAddBackupProfile: () => void;
  onUpdateBackupProfile: (index: number, field: keyof BackupProfile, value: string) => void;
  onRemoveBackupProfile: (index: number) => void;
  onSaveBackupProfiles: () => void | Promise<void>;
  onRunBackupNow: () => void | Promise<void>;
  onRetentionDaysChange: (value: string) => void;
  onRetentionMinFilesChange: (value: string) => void;
  onApplyRetention: (dryRun: boolean) => void | Promise<void>;
  onRestoreProfileIdChange: (value: string) => void;
  onRestoreFileNameChange: (value: string) => void;
  onLoadRestoreCandidates: () => void | Promise<void>;
  onRunRestore: (dryRun: boolean) => void | Promise<void>;
};

export function AdminBackupsTab({
  tx,
  backupAllowedRoots,
  backupFeedback,
  backupActionsBusy,
  backupListLoading,
  backupActiveProfile,
  backupProfilesForm,
  retentionDays,
  retentionMinFiles,
  restoreProfileId,
  restoreFileName,
  restoreCandidates,
  backupJobsSorted,
  backupSummaryCount,
  backupSummaryLatest,
  backupSummaryStatus,
  restoreCandidateNames,
  onLoadBackupStatus,
  onBackupActiveProfileChange,
  onAddBackupProfile,
  onUpdateBackupProfile,
  onRemoveBackupProfile,
  onSaveBackupProfiles,
  onRunBackupNow,
  onRetentionDaysChange,
  onRetentionMinFilesChange,
  onApplyRetention,
  onRestoreProfileIdChange,
  onRestoreFileNameChange,
  onLoadRestoreCandidates,
  onRunRestore,
}: AdminBackupsTabProps) {
  return (
    <div className="grid2">
      <article className="panelCard">
        <h2>{tx("backupPlan", "Backup Plan")}</h2>
        <p className="subText">{tx("backupHelp", "Use storage profiles. Profile paths must stay inside allowed root directories.")}</p>
        <p className="subText"><b>{tx("allowedRoots", "Allowed root paths")}:</b> {backupAllowedRoots.join(", ") || "-"}</p>
        {backupFeedback ? (
          <p className={`inlineFeedback inlineFeedback${backupFeedback.tone === "error" ? "Error" : backupFeedback.tone === "success" ? "Success" : "Info"}`}>
            {backupFeedback.message}
          </p>
        ) : null}

        <div className="rowButtons" style={{ marginBottom: 8 }}>
          <button type="button" className="ghost" onClick={() => void onLoadBackupStatus(true)} disabled={backupActionsBusy}>
            {backupListLoading ? tx("backupLoading", "Loading...") : tx("backupReload", "Reload backup data")}
          </button>
        </div>

        <div className="formGrid compactFormGrid">
          <select value={backupActiveProfile} onChange={(e) => onBackupActiveProfileChange(e.target.value)}>
            {backupProfilesForm.map((profile) => (
              <option key={profile.id} value={profile.id}>{profile.label} ({profile.id})</option>
            ))}
          </select>
          <button type="button" onClick={onAddBackupProfile} className="ghost">{tx("addProfile", "Add profile")}</button>
        </div>

        <div className="providerStack">
          {backupProfilesForm.map((profile, index) => (
            <div key={`${profile.id}-${index}`} className="providerCard">
              <div className="formGrid compactFormGrid">
                <input value={profile.id} onChange={(e) => onUpdateBackupProfile(index, "id", e.target.value)} placeholder={tx("profileId", "Profile ID")} />
                <input value={profile.label} onChange={(e) => onUpdateBackupProfile(index, "label", e.target.value)} placeholder={tx("profileLabel", "Profile label")} />
                <input value={profile.path} onChange={(e) => onUpdateBackupProfile(index, "path", e.target.value)} placeholder={tx("profilePath", "Storage path")} style={{ gridColumn: "1 / -1" }} />
              </div>
              <div className="providerActions">
                <span className="badge">{profile.id === backupActiveProfile ? tx("activeBackupProfile", "Active profile") : tx("planned", "Planned")}</span>
                <button type="button" onClick={() => onRemoveBackupProfile(index)} className="ghost danger">{tx("removeProfile", "Remove profile")}</button>
              </div>
            </div>
          ))}
        </div>

        <div className="rowButtons">
          <button type="button" onClick={() => void onSaveBackupProfiles()} className="primary" disabled={backupActionsBusy}>{tx("saveBackupSettings", "Save profiles")}</button>
          <button type="button" onClick={() => void onRunBackupNow()} className="ghost" disabled={backupActionsBusy}>{tx("runBackupNow", "Run backup now")}</button>
        </div>

        <hr style={{ border: 0, borderTop: "1px solid var(--line)", margin: "14px 0" }} />
        <h3>{tx("retentionTitle", "Retention policy")}</h3>
        <p className="subText">{tx("retentionHelp", "Keep recent backups and delete old dump files by policy.")}</p>
        <div className="formGrid compactFormGrid">
          <input type="number" min={0} value={retentionDays} onChange={(e) => onRetentionDaysChange(e.target.value)} placeholder={tx("retentionDays", "Retention days")} />
          <input type="number" min={0} value={retentionMinFiles} onChange={(e) => onRetentionMinFilesChange(e.target.value)} placeholder={tx("retentionMinFiles", "Minimum files to keep")} />
        </div>
        <div className="rowButtons">
          <button type="button" className="ghost" onClick={() => void onApplyRetention(true)} disabled={backupActionsBusy}>{tx("retentionDryRun", "Retention dry-run")}</button>
          <button type="button" className="ghost danger" onClick={() => void onApplyRetention(false)} disabled={backupActionsBusy}>{tx("retentionApply", "Apply retention")}</button>
        </div>

        <hr style={{ border: 0, borderTop: "1px solid var(--line)", margin: "14px 0" }} />
        <h3>{tx("restoreTitle", "Restore")}</h3>
        <p className="subText">{tx("restoreHelp", "Choose backup file and run dry-run before real restore.")}</p>
        <div className="formGrid compactFormGrid">
          <select value={restoreProfileId} onChange={(e) => onRestoreProfileIdChange(e.target.value)}>
            {backupProfilesForm.map((profile) => (
              <option key={profile.id} value={profile.id}>{profile.label} ({profile.id})</option>
            ))}
          </select>
          <select value={restoreFileName} onChange={(e) => onRestoreFileNameChange(e.target.value)}>
            {restoreCandidates.length === 0 ? (
              <option value="">{tx("noRestoreCandidates", "No .dump files found")}</option>
            ) : (
              restoreCandidates.map((candidate) => (
                <option key={candidate.file_name} value={candidate.file_name}>{candidate.file_name}</option>
              ))
            )}
          </select>
        </div>
        <div className="rowButtons">
          <button type="button" className="ghost" onClick={() => void onLoadRestoreCandidates()} disabled={backupActionsBusy}>{tx("refreshRestoreFiles", "Refresh files")}</button>
          <button type="button" className="primary" onClick={() => void onRunRestore(true)} disabled={backupActionsBusy}>{tx("restoreDryRun", "Restore dry-run")}</button>
          <button type="button" className="ghost danger" onClick={() => void onRunRestore(false)} disabled={backupActionsBusy}>{tx("restoreNow", "Restore now")}</button>
        </div>
        <h3 style={{ marginTop: 14 }}>{tx("restoreCandidatesList", "Restore files")}</h3>
        {restoreCandidates.length === 0 ? (
          <p className="subText">{tx("noRestoreCandidates", "No .dump files found")}</p>
        ) : (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>{tx("backupFile", "File")}</th>
                  <th>{tx("backupSize", "Size")}</th>
                  <th>{tx("restoreModifiedAt", "Modified")}</th>
                  <th>{tx("actions", "Actions")}</th>
                </tr>
              </thead>
              <tbody>
                {restoreCandidates.map((candidate) => (
                  <tr key={candidate.file_name}>
                    <td>{candidate.file_name}</td>
                    <td>{formatBytes(candidate.size_bytes)}</td>
                    <td>{formatAuditTimestamp(candidate.modified_at)}</td>
                    <td>
                      <button type="button" className="ghost" onClick={() => onRestoreFileNameChange(candidate.file_name)} disabled={backupActionsBusy}>{tx("backupSelectForRestore", "Select")}</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>

      <article className="panelCard">
        <h2>{tx("backupHistory", "Backup history")}</h2>
        <div className="rowMeta">
          <span className="subText">{tx("backupHistorySummaryAvailable", "Backups available: {count}").replace("{count}", String(backupSummaryCount))}</span>
          <span className="subText">{tx("backupHistorySummaryLatest", "Latest backup: {value}").replace("{value}", formatAuditTimestamp(backupSummaryLatest))}</span>
          <span className="subText">{tx("backupHistorySummaryStatus", "Latest status: {value}").replace("{value}", backupSummaryStatus)}</span>
        </div>
        {backupJobsSorted.length === 0 ? (
          <p className="subText">{tx("noBackupJobs", "No backup jobs yet.")}</p>
        ) : (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>{tx("backupFile", "File")}</th>
                  <th>{tx("backupProfile", "Profile")}</th>
                  <th>{tx("backupSize", "Size")}</th>
                  <th>{tx("backupCreatedAt", "Created")}</th>
                  <th>{tx("status", "Status")}</th>
                  <th>{tx("backupJobType", "Type")}</th>
                  <th>{tx("restoreTitle", "Restore")}</th>
                </tr>
              </thead>
              <tbody>
                {backupJobsSorted.map((job) => (
                  <tr key={job.job_id}>
                    <td>{fileNameFromPath(job.file_path)}</td>
                    <td>{job.profile_id || "-"}</td>
                    <td>{formatBytes(job.size_bytes)}</td>
                    <td>{formatAuditTimestamp(job.started_at || job.finished_at)}</td>
                    <td>
                      <span className={`badge ${backupStatusBadgeClass(job.status || tx("backupStatusUnknown", "unknown"))}`}>
                        {job.status || tx("backupStatusUnknown", "unknown")}
                      </span>
                    </td>
                    <td>{job.job_type || "backup"}</td>
                    <td>
                      {restoreCandidateNames.has(fileNameFromPath(job.file_path)) ? (
                        <span className="badge badgeOk">{tx("backupRestoreAvailable", "Restore available")}</span>
                      ) : (
                        <span className="badge badgeInfo">{tx("backupRestoreNotAvailable", "Not in restore list")}</span>
                      )}
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