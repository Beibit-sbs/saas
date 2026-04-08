import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiPut } from "@/shared/api/client";
import type {
  BackupSettings,
  BackupHistoryResponse,
  RestoreCandidatesResponse,
  BackupJobEnvelope,
  UpdateBackupSettingsPayload,
  RestorePayload,
  RetentionPayload,
} from "./types";

const BASE = "/api/admin/backups";
export const BACKUP_SETTINGS_KEY = "backup-settings";
export const BACKUP_HISTORY_KEY = "backup-history";
export const RESTORE_CANDIDATES_KEY = "restore-candidates";

export function useBackupSettings() {
  return useQuery({
    queryKey: [BACKUP_SETTINGS_KEY],
    queryFn: () => apiGet<BackupSettings>(`${BASE}/settings`),
  });
}

export function useBackupHistory() {
  return useQuery({
    queryKey: [BACKUP_HISTORY_KEY],
    queryFn: () => apiGet<BackupHistoryResponse>(`${BASE}/history`),
  });
}

export function useRestoreCandidates(profileId?: string) {
  return useQuery({
    queryKey: [RESTORE_CANDIDATES_KEY, profileId ?? ""],
    queryFn: () =>
      apiGet<RestoreCandidatesResponse>(`${BASE}/restore-candidates`, profileId ? { profile_id: profileId } : undefined),
    enabled: Boolean(profileId),
  });
}

export function useUpdateBackupSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateBackupSettingsPayload) =>
      apiPut<BackupSettings>(`${BASE}/settings`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [BACKUP_SETTINGS_KEY] });
      qc.invalidateQueries({ queryKey: [RESTORE_CANDIDATES_KEY] });
    },
  });
}

export function useRunBackupNow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiPost<BackupJobEnvelope>(`${BASE}/run`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [BACKUP_HISTORY_KEY] }),
  });
}

export function useRunRestore() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: RestorePayload) =>
      apiPost<BackupJobEnvelope>(`${BASE}/restore`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [BACKUP_HISTORY_KEY] }),
  });
}

export function useApplyRetention() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: RetentionPayload) =>
      apiPost<BackupJobEnvelope>(`${BASE}/retention/apply`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [BACKUP_HISTORY_KEY] }),
  });
}
