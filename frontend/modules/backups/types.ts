export interface BackupProfile {
  id: string;
  label: string;
  path: string;
}

export interface BackupSettings {
  active_profile: string;
  profiles: BackupProfile[];
  allowed_roots: string[];
  retention_days: number;
  retention_min_files: number;
}

export interface BackupHistoryJob {
  job_id?: string;
  job_type?: string;
  status?: string;
  profile_id?: string;
  file_path?: string;
  started_at?: string;
  finished_at?: string;
  error?: string;
}

export interface BackupHistoryResponse {
  jobs: BackupHistoryJob[];
}

export interface BackupCandidate {
  file_name: string;
  file_path: string;
  size_bytes: number;
  modified_at: string;
}

export interface RestoreCandidatesResponse {
  profile_id: string;
  profile_label: string;
  profile_path: string;
  candidates: BackupCandidate[];
}

export interface BackupJobEnvelope {
  job: BackupHistoryJob;
}

export interface UpdateBackupSettingsPayload {
  active_profile: string;
  profiles: BackupProfile[];
  retention_days: number;
  retention_min_files: number;
}

export interface RestorePayload {
  profile_id?: string;
  file_name?: string;
  dry_run: boolean;
  confirm_text?: string;
}

export interface RetentionPayload {
  profile_id?: string;
  dry_run: boolean;
}
