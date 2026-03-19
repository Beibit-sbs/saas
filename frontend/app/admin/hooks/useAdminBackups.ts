import { useCallback, useEffect, useMemo, useState } from "react";

import { buildCsrfHeaders } from "../../components/csrf";
import type { AdminCopy, BackupJob, BackupProfile, InlineFeedback, RestoreCandidate, TxFn } from "../types";

type UseAdminBackupsParams = {
  activeTab: string;
  buildAuthHeaders: () => Record<string, string>;
  l: AdminCopy;
  tx: TxFn;
};

type UseAdminBackupsResult = {
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
  setBackupActiveProfile: (value: string) => void;
  setRetentionDays: (value: string) => void;
  setRetentionMinFiles: (value: string) => void;
  setRestoreProfileId: (value: string) => void;
  setRestoreFileName: (value: string) => void;
  loadBackupStatus: (showFeedback?: boolean) => Promise<void>;
  addBackupProfile: () => void;
  updateBackupProfile: (index: number, field: keyof BackupProfile, value: string) => void;
  removeBackupProfile: (index: number) => void;
  saveBackupProfiles: () => Promise<void>;
  runBackupNow: () => Promise<void>;
  applyRetention: (dryRun: boolean) => Promise<void>;
  loadRestoreCandidates: (profileId?: string) => Promise<void>;
  runRestore: (dryRun: boolean) => Promise<void>;
};

export function useAdminBackups({
  activeTab,
  buildAuthHeaders,
  l,
  tx,
}: UseAdminBackupsParams): UseAdminBackupsResult {
  const [backupFeedback, setBackupFeedback] = useState<InlineFeedback | null>(null);
  const [backupListLoading, setBackupListLoading] = useState(false);
  const [backupRunBusy, setBackupRunBusy] = useState(false);
  const [backupRestoreBusy, setBackupRestoreBusy] = useState(false);
  const [backupRetentionBusy, setBackupRetentionBusy] = useState(false);
  const [backupProfilesForm, setBackupProfilesForm] = useState<BackupProfile[]>([]);
  const [backupJobs, setBackupJobs] = useState<BackupJob[]>([]);
  const [backupAllowedRoots, setBackupAllowedRoots] = useState<string[]>([]);
  const [backupActiveProfile, setBackupActiveProfile] = useState("");
  const [retentionDays, setRetentionDays] = useState("14");
  const [retentionMinFiles, setRetentionMinFiles] = useState("3");
  const [restoreCandidates, setRestoreCandidates] = useState<RestoreCandidate[]>([]);
  const [restoreProfileId, setRestoreProfileId] = useState("");
  const [restoreFileName, setRestoreFileName] = useState("");

  const backupJobsSorted = useMemo(
    () => [...backupJobs].sort((a, b) => new Date(b.started_at || b.finished_at || 0).getTime() - new Date(a.started_at || a.finished_at || 0).getTime()),
    [backupJobs],
  );
  const restoreCandidateNames = useMemo(
    () => new Set(restoreCandidates.map((item) => item.file_name)),
    [restoreCandidates],
  );
  const backupLatestJob = backupJobsSorted[0] || null;
  const backupSummaryCount = backupJobsSorted.length > 0 ? backupJobsSorted.length : restoreCandidates.length;
  const backupSummaryLatest = backupLatestJob?.started_at || restoreCandidates[0]?.modified_at || "-";
  const backupSummaryStatus = backupLatestJob?.status || tx("backupStatusUnknown");
  const backupActionsBusy = backupListLoading || backupRunBusy || backupRestoreBusy || backupRetentionBusy;

  const loadBackupStatus = useCallback(async (showFeedback = false) => {
    setBackupListLoading(true);
    if (!showFeedback) {
      setBackupFeedback(null);
    }
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const [settingsRes, historyRes] = await Promise.all([
        fetch(`${baseUrl}/admin/backups/settings`, {
          headers: buildAuthHeaders(),
          credentials: "include",
          cache: "no-store",
        }),
        fetch(`${baseUrl}/admin/backups/history`, {
          headers: buildAuthHeaders(),
          credentials: "include",
          cache: "no-store",
        }),
      ]);

      if (settingsRes.ok) {
        const settingsJson = (await settingsRes.json()) as {
          active_profile?: string;
          profiles?: BackupProfile[];
          allowed_roots?: string[];
          retention_days?: number;
          retention_min_files?: number;
        };
        setBackupProfilesForm(settingsJson.profiles || []);
        setBackupActiveProfile(settingsJson.active_profile || "");
        setBackupAllowedRoots(settingsJson.allowed_roots || []);
        setRetentionDays(String(settingsJson.retention_days ?? 14));
        setRetentionMinFiles(String(settingsJson.retention_min_files ?? 3));
        setRestoreProfileId((current) => current || settingsJson.active_profile || "");
      }

      if (historyRes.ok) {
        const historyJson = (await historyRes.json()) as { jobs?: BackupJob[] };
        setBackupJobs(historyJson.jobs || []);
      }

      const errors: string[] = [];
      if (!settingsRes.ok) {
        errors.push(`settings: ${settingsRes.status}`);
      }
      if (!historyRes.ok) {
        errors.push(`history: ${historyRes.status}`);
      }
      if (errors.length > 0) {
        setBackupFeedback({ tone: "error", message: `${l.errorPrefix}: ${errors.join(" | ")}` });
      } else if (showFeedback) {
        setBackupFeedback({ tone: "success", message: tx("backupReload") });
      }
    } catch (error) {
      setBackupFeedback({ tone: "error", message: String(error) });
    } finally {
      setBackupListLoading(false);
    }
  }, [buildAuthHeaders, l.errorPrefix, tx]);

  const loadRestoreCandidates = useCallback(async (profileId?: string) => {
    const targetProfile = (profileId || restoreProfileId || backupActiveProfile).trim();
    if (!targetProfile) {
      setRestoreCandidates([]);
      return;
    }

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const res = await fetch(
        `${baseUrl}/admin/backups/restore-candidates?profile_id=${encodeURIComponent(targetProfile)}`,
        {
          headers: buildAuthHeaders(),
          credentials: "include",
          cache: "no-store",
        },
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setBackupFeedback({ tone: "error", message: `${l.errorPrefix}: ${err.detail || res.status}` });
        return;
      }

      const json = (await res.json()) as { candidates?: RestoreCandidate[] };
      const candidates = json.candidates || [];
      setRestoreCandidates(candidates);
      setRestoreFileName((current) => {
        if (current && candidates.some((row) => row.file_name === current)) {
          return current;
        }
        return candidates[0]?.file_name || "";
      });
    } catch (error) {
      setBackupFeedback({ tone: "error", message: String(error) });
    }
  }, [buildAuthHeaders, restoreProfileId, backupActiveProfile, l.errorPrefix]);

  const runRestore = useCallback(async (dryRun: boolean) => {
    setBackupFeedback(null);
    if (!restoreProfileId) {
      setBackupFeedback({ tone: "error", message: tx("restoreProfileRequired") });
      return;
    }
    if (!restoreFileName) {
      setBackupFeedback({ tone: "error", message: tx("restoreFileRequired") });
      return;
    }

    if (!dryRun) {
      const confirmed = window.confirm(
        tx("backupRestoreConfirmByFile").replace("{file}", restoreFileName),
      );
      if (!confirmed) {
        setBackupFeedback({ tone: "info", message: tx("restoreCancelled") });
        return;
      }
    }

    setBackupRestoreBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/backups/restore`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          profile_id: restoreProfileId,
          file_name: restoreFileName,
          dry_run: dryRun,
          confirm_text: dryRun ? undefined : "RESTORE",
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setBackupFeedback({ tone: "error", message: `${l.errorPrefix}: ${err.detail || res.status}` });
        return;
      }

      const json = (await res.json()) as { job?: { status?: string } };
      setBackupFeedback({
        tone: "success",
        message: dryRun
          ? tx("restoreDryRunOk")
          : tx("restoreCompleted"),
      });
      if (json.job?.status) {
        await loadBackupStatus();
      }
      await loadRestoreCandidates();
    } catch (error) {
      setBackupFeedback({ tone: "error", message: String(error) });
    } finally {
      setBackupRestoreBusy(false);
    }
  }, [buildAuthHeaders, l.errorPrefix, loadBackupStatus, loadRestoreCandidates, restoreFileName, restoreProfileId, tx]);

  const updateBackupProfile = useCallback((index: number, field: keyof BackupProfile, value: string) => {
    setBackupProfilesForm((current) =>
      current.map((profile, idx) => (idx === index ? { ...profile, [field]: value } : profile)),
    );
  }, []);

  const addBackupProfile = useCallback(() => {
    setBackupProfilesForm((current) => [
      ...current,
      { id: `profile${current.length + 1}`, label: "New profile", path: "/tmp/app-backups/new-profile" },
    ]);
  }, []);

  const removeBackupProfile = useCallback((index: number) => {
    setBackupProfilesForm((current) => current.filter((_, idx) => idx !== index));
  }, []);

  const saveBackupProfiles = useCallback(async () => {
    setBackupFeedback(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/backups/settings`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          active_profile: backupActiveProfile,
          profiles: backupProfilesForm,
          retention_days: Number(retentionDays || "14"),
          retention_min_files: Number(retentionMinFiles || "3"),
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setBackupFeedback({ tone: "error", message: `${l.errorPrefix}: ${err.detail || res.status}` });
        return;
      }

      setBackupFeedback({ tone: "success", message: tx("backupSaved") });
      await loadBackupStatus();
    } catch (error) {
      setBackupFeedback({ tone: "error", message: String(error) });
    }
  }, [backupActiveProfile, backupProfilesForm, buildAuthHeaders, l.errorPrefix, loadBackupStatus, retentionDays, retentionMinFiles, tx]);

  const applyRetention = useCallback(async (dryRun: boolean) => {
    setBackupFeedback(null);

    if (!dryRun) {
      const confirmed = window.confirm(
        tx("backupRetentionConfirm"),
      );
      if (!confirmed) {
        setBackupFeedback({ tone: "info", message: tx("retentionCancelled") });
        return;
      }
    }

    setBackupRetentionBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/backups/retention/apply`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          profile_id: backupActiveProfile,
          dry_run: dryRun,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setBackupFeedback({ tone: "error", message: `${l.errorPrefix}: ${err.detail || res.status}` });
        return;
      }

      const json = (await res.json()) as { job?: { deleted_count?: number; status?: string } };
      const deleted = json.job?.deleted_count ?? 0;
      const retentionStatusTemplate = dryRun
        ? tx("retentionDryRunDone")
        : tx("retentionApplied");
      setBackupFeedback({ tone: "success", message: retentionStatusTemplate.replace("{count}", String(deleted)) });
      await loadBackupStatus();
      await loadRestoreCandidates();
    } catch (error) {
      setBackupFeedback({ tone: "error", message: String(error) });
    } finally {
      setBackupRetentionBusy(false);
    }
  }, [backupActiveProfile, buildAuthHeaders, l.errorPrefix, loadBackupStatus, loadRestoreCandidates, tx]);

  const runBackupNow = useCallback(async () => {
    const confirmed = window.confirm(tx("backupRunConfirm"));
    if (!confirmed) {
      setBackupFeedback({ tone: "info", message: tx("backupRunCancelled") });
      return;
    }

    setBackupFeedback(null);
    setBackupRunBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/backups/run`, {
        method: "POST",
        headers: {
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setBackupFeedback({ tone: "error", message: `${l.errorPrefix}: ${err.detail || res.status}` });
        return;
      }

      setBackupFeedback({ tone: "success", message: tx("backupCompleted") });
      await loadBackupStatus();
      await loadRestoreCandidates();
    } catch (error) {
      setBackupFeedback({ tone: "error", message: String(error) });
    } finally {
      setBackupRunBusy(false);
    }
  }, [buildAuthHeaders, l.errorPrefix, loadBackupStatus, loadRestoreCandidates, tx]);

  useEffect(() => {
    if (activeTab !== "backups") {
      return;
    }
    void loadBackupStatus();
  }, [activeTab, loadBackupStatus]);

  useEffect(() => {
    if (activeTab !== "backups") {
      return;
    }
    void loadRestoreCandidates();
  }, [activeTab, loadRestoreCandidates, restoreProfileId]);

  return {
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
    setBackupActiveProfile,
    setRetentionDays,
    setRetentionMinFiles,
    setRestoreProfileId,
    setRestoreFileName,
    loadBackupStatus,
    addBackupProfile,
    updateBackupProfile,
    removeBackupProfile,
    saveBackupProfiles,
    runBackupNow,
    applyRetention,
    loadRestoreCandidates,
    runRestore,
  };
}