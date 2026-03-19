import type { AdminTranslationDictionary, AdminTranslationKey } from "../../i18n/admin";

export type AdminTab = "overview" | "languages" | "local-users" | "rbac" | "integrations" | "backups" | "audit" | "feature-flags" | "example-notes" | "system" | "university" | "tenants";
export type UiLang = "ru" | "en" | "kk";
export type CatalogLanguage = { code: string; name: string; native_name: string };

export type LdapStatus = {
  enabled: boolean;
  configured: boolean;
  server_uri: string;
  bind_dn: string;
  base_dn: string;
  user_filter: string;
  display_name_attribute: string;
  login_attribute: string;
  group_attribute: string;
  group_role_map_count: number;
  default_role: string;
  timeout_seconds: number;
};

export type AiProviderStatus = {
  provider: string;
  configured: boolean;
  validation_url: string;
  has_api_key?: boolean;
};

export type BackupProfile = {
  id: string;
  label: string;
  path: string;
};

export type BackupJob = {
  job_id: string;
  job_type?: string;
  status: string;
  profile_id: string;
  file_path: string;
  size_bytes: number;
  started_at: string;
  finished_at: string;
  error?: string;
};

export type RestoreCandidate = {
  file_name: string;
  file_path: string;
  size_bytes: number;
  modified_at: string;
};

export type AuditEvent = {
  event_id: string;
  timestamp: string;
  actor: string;
  action: string;
  entity?: string;
  path: string;
  ip?: string;
  client_ip: string;
  result?: string;
  correlation_id: string;
  metadata?: Record<string, unknown>;
};

export type FeatureFlag = {
  key: string;
  enabled: boolean;
  description?: string;
  scope: string;
  updated_at?: string;
  updated_by?: string;
  last_changed_at?: string;
  last_changed_by?: string;
  metadata?: Record<string, unknown>;
};

export type ExampleReferenceItem = {
  key: string;
  title: string;
  required_permission: string;
  audit_action: string;
};

export type RbacRoleEntry = {
  name: string;
  permissions: string[];
};

export type RbacAssignmentEntry = {
  user_id: string;
  roles: string[];
};

export type DashboardSnapshot = {
  status: string;
  generated_at: string;
  system: {
    backend_health: string;
    api_health: string;
    metrics_available: boolean;
  };
  users: {
    local_users_count: number;
  };
  rbac: {
    roles_count: number;
    assignments_count: number;
  };
  languages: {
    total_count: number;
    enabled_count: number;
    system_count: number;
  };
  integrations: {
    ldap: {
      enabled: boolean;
      configured: boolean;
    };
    ai_providers: {
      total_count: number;
      configured_count: number;
    };
  };
  backups: {
    active_profile: string;
    profiles_count: number;
    last_job: BackupJob | null;
  };
  audit: {
    recent_events_count: number;
    last_event: AuditEvent | null;
  };
};

export type InlineFeedback = {
  tone: "success" | "error" | "info";
  message: string;
};

export type LocalUser = {
  user_id: string;
  login: string;
  display_name: string;
  roles: string[];
  default_language: string;
  auth_source: string;
  sync_with_ad: boolean;
};

export type LdapConfigForm = {
  enabled: boolean;
  server_uri: string;
  bind_dn: string;
  bind_password: string;
  base_dn: string;
  user_filter: string;
  display_name_attribute: string;
  login_attribute: string;
  group_attribute: string;
  group_role_map_json: string;
  default_role: string;
  timeout_seconds: string;
};

export type AiProviderForm = {
  apiKey: string;
  validationUrl: string;
};

export type SupportedLanguage = {
  code: string;
  name: string;
  native_name: string;
  enabled: boolean;
  system: boolean;
};

export type AdminCopy = AdminTranslationDictionary;
export type TxFn = (key: AdminTranslationKey, fallback?: string) => string;
export type AuditExportBusy = "" | "csv" | "json";