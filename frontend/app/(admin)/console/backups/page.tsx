"use client";

import { useState } from "react";
import { Archive } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { PermissionGate, RequirePermission } from "@/shared/ui/permission-gate";
import { useLanguage } from "@/app/components/LanguageProvider";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { PERMISSIONS } from "@/shared/config/permissions";
import {
  useApplyRetention,
  useBackupHistory,
  useBackupSettings,
  useRestoreCandidates,
  useRunBackupNow,
  useRunRestore,
  useUpdateBackupSettings,
} from "@/modules/backups/hooks";
import type { BackupCandidate, BackupHistoryJob } from "@/modules/backups/types";

export default function BackupsPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const { getHandlers } = useMutationFeedback();

  const settingsQuery = useBackupSettings();
  const historyQuery = useBackupHistory();
  const activeProfile = settingsQuery.data?.active_profile;
  const restoreCandidatesQuery = useRestoreCandidates(activeProfile);

  const [retentionDays, setRetentionDays] = useState("14");
  const [retentionMinFiles, setRetentionMinFiles] = useState("3");
  const [selectedProfile, setSelectedProfile] = useState("");
  const [selectedFile, setSelectedFile] = useState("");

  const updateSettings = useUpdateBackupSettings();
  const runBackupNow = useRunBackupNow();
  const runRestore = useRunRestore();
  const applyRetention = useApplyRetention();

  const settings = settingsQuery.data;
  const jobs = historyQuery.data?.jobs ?? [];
  const candidates = restoreCandidatesQuery.data?.candidates ?? [];

  const loadingAny = settingsQuery.isLoading || historyQuery.isLoading;
  const errorAny = settingsQuery.error || historyQuery.error;

  const canSaveSettings =
    settings != null &&
    Number.isFinite(Number.parseInt(retentionDays, 10)) &&
    Number.isFinite(Number.parseInt(retentionMinFiles, 10));

  const effectiveProfile = selectedProfile || settings?.active_profile || "";
  const latestCandidate = candidates[0];
  const effectiveFile = selectedFile || latestCandidate?.file_name || "";

  if (errorAny) {
    return <ErrorState title="Failed to load backups" onRetry={() => {
      settingsQuery.refetch();
      historyQuery.refetch();
    }} />;
  }

  const jobColumns: Column<BackupHistoryJob>[] = [
    {
      key: "job_type",
      header: tAny("backupJobType"),
      cell: (r) => r.job_type ?? "-",
      sortValue: (r) => r.job_type ?? "",
    },
    {
      key: "profile_id",
      header: tAny("backupProfile"),
      cell: (r) => r.profile_id ?? "-",
      sortValue: (r) => r.profile_id ?? "",
    },
    {
      key: "status",
      header: tAny("status"),
      cell: (r) => r.status ?? tAny("backupStatusUnknown"),
      sortValue: (r) => r.status ?? "",
    },
    {
      key: "started_at",
      header: tAny("backupCreatedAt"),
      cell: (r) => r.started_at ?? "-",
      sortValue: (r) => r.started_at ?? "",
    },
  ];

  const candidateColumns: Column<BackupCandidate>[] = [
    {
      key: "file_name",
      header: tAny("backupFile"),
      cell: (r) => r.file_name,
      sortValue: (r) => r.file_name,
    },
    {
      key: "size_bytes",
      header: tAny("backupSize"),
      cell: (r) => String(r.size_bytes),
      sortValue: (r) => r.size_bytes,
    },
    {
      key: "modified_at",
      header: tAny("restoreModifiedAt"),
      cell: (r) => r.modified_at,
      sortValue: (r) => r.modified_at,
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.BACKUP_MANAGE}>
    <div className="space-y-6" data-testid="backups-page">
      <PageHeader
        title={t("nav.backups")}
        description={tAny("backupHelp")}
        icon={Archive}
      />

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-sm font-semibold">{tAny("backupPlan")}</h2>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="space-y-1.5">
            <Label htmlFor="active-profile">{tAny("backupProfile")}</Label>
            <select
              id="active-profile"
              className="h-9 rounded-md border px-3 text-sm"
              value={selectedProfile || settings?.active_profile || ""}
              onChange={(e) => setSelectedProfile(e.target.value)}
            >
              {(settings?.profiles ?? []).map((p) => (
                <option key={p.id} value={p.id}>{p.label} ({p.id})</option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="retention-days">{tAny("retentionDays")}</Label>
            <Input
              id="retention-days"
              type="number"
              min={0}
              value={retentionDays}
              onChange={(e) => setRetentionDays(e.target.value)}
              placeholder={String(settings?.retention_days ?? 14)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="retention-min-files">{tAny("retentionMinFiles")}</Label>
            <Input
              id="retention-min-files"
              type="number"
              min={0}
              value={retentionMinFiles}
              onChange={(e) => setRetentionMinFiles(e.target.value)}
              placeholder={String(settings?.retention_min_files ?? 3)}
            />
          </div>
        </div>
        <PermissionGate permission={PERMISSIONS.BACKUP_MANAGE}>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              disabled={!canSaveSettings || updateSettings.isPending || settings == null}
              onClick={() => {
                if (!settings) return;
                updateSettings.mutate(
                  {
                    active_profile: selectedProfile || settings.active_profile,
                    profiles: settings.profiles,
                    retention_days: Number.parseInt(retentionDays, 10),
                    retention_min_files: Number.parseInt(retentionMinFiles, 10),
                  },
                  getHandlers({ successTitle: tAny("backupSaved") }),
                );
              }}
            >
              {tAny("saveBackupSettings")}
            </Button>
            <Button
              disabled={runBackupNow.isPending}
              onClick={() => runBackupNow.mutate(undefined, getHandlers({ successTitle: tAny("backupCompleted") }))}
            >
              {tAny("runBackupNow")}
            </Button>
            <Button
              variant="outline"
              disabled={applyRetention.isPending || !effectiveProfile}
              onClick={() =>
                applyRetention.mutate(
                  { profile_id: effectiveProfile, dry_run: true },
                  getHandlers({ successTitle: tAny("retentionDryRun") }),
                )
              }
            >
              {tAny("retentionDryRun")}
            </Button>
          </div>
        </PermissionGate>
      </section>

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-sm font-semibold">{tAny("restoreTitle")}</h2>
        <p className="text-sm text-muted-foreground">{tAny("restoreHelp")}</p>
        <div className="grid gap-3 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="restore-file">{tAny("backupFile")}</Label>
            <select
              id="restore-file"
              className="h-9 rounded-md border px-3 text-sm"
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
            >
              <option value="">{latestCandidate?.file_name ?? "-"}</option>
              {candidates.map((c) => (
                <option key={c.file_name} value={c.file_name}>{c.file_name}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label>{tAny("backupProfile")}</Label>
            <div className="h-9 rounded-md border px-3 text-sm flex items-center">
              {effectiveProfile || "-"}
            </div>
          </div>
        </div>
        <PermissionGate permission={PERMISSIONS.BACKUP_MANAGE}>
          <Button
            variant="outline"
            disabled={runRestore.isPending || !effectiveProfile || !effectiveFile}
            onClick={() =>
              runRestore.mutate(
                {
                  profile_id: effectiveProfile,
                  file_name: effectiveFile,
                  dry_run: true,
                },
                getHandlers({ successTitle: tAny("restoreDryRunOk") }),
              )
            }
          >
            {tAny("restoreDryRun")}
          </Button>
        </PermissionGate>

        <DataTable
          columns={candidateColumns}
          data={candidates}
          isLoading={restoreCandidatesQuery.isLoading}
          getRowKey={(r) => r.file_name}
          emptyTitle={tAny("backupRestoreNotAvailable")}
        />
      </section>

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-sm font-semibold">{tAny("backupHistory")}</h2>
        <DataTable
          columns={jobColumns}
          data={jobs}
          isLoading={loadingAny}
          getRowKey={(r) => `${r.job_id ?? r.started_at ?? r.file_path ?? "row"}`}
          emptyTitle={tAny("noBackupJobs")}
        />
      </section>
    </div>
    </RequirePermission>
  );
}
