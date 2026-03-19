"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import { buildCsrfHeaders } from "../components/csrf";
import { useLanguage } from "../components/LanguageProvider";
import { useAdminAudit } from "./hooks/useAdminAudit";
import { AdminAuditTab } from "./components/AdminAuditTab";
import { AdminBackupsTab } from "./components/AdminBackupsTab";
import { AdminExampleNotesTab } from "./components/AdminExampleNotesTab";
import { AdminFeatureFlagsTab } from "./components/AdminFeatureFlagsTab";
import { AdminIntegrationsTab } from "./components/AdminIntegrationsTab";
import { AdminLanguagesTab } from "./components/AdminLanguagesTab";
import { AdminLocalUsersTab } from "./components/AdminLocalUsersTab";
import { AdminOverviewTab } from "./components/AdminOverviewTab";
import { AdminRbacTab } from "./components/AdminRbacTab";
import { AdminShell, type AdminSection } from "./components/AdminShell";
import { useAdminFeatureFlags } from "./hooks/useAdminFeatureFlags";
import { useAdminLocalUsers } from "./hooks/useAdminLocalUsers";
import { useAdminOverview } from "./hooks/useAdminOverview";
import { useAdminLanguages } from "./hooks/useAdminLanguages";
import { adminTranslations, type AdminTranslationKey } from "../../i18n/admin";
import type {
  AdminTab,
  AiProviderForm,
  AiProviderStatus,
  AuditEvent,
  BackupJob,
  BackupProfile,
  InlineFeedback,
  LdapConfigForm,
  LdapStatus,
  RbacAssignmentEntry,
  RbacRoleEntry,
  RestoreCandidate,
  UiLang,
} from "./types";

const toUiLang = (value: string): UiLang => {
  if (value === "en" || value === "kk") {
    return value;
  }
  return "ru";
};

const defaultLdapConfigForm: LdapConfigForm = {
  enabled: false,
  server_uri: "",
  bind_dn: "",
  bind_password: "",
  base_dn: "",
  user_filter: "",
  display_name_attribute: "cn",
  login_attribute: "sAMAccountName",
  group_attribute: "memberOf",
  group_role_map_json: "{}",
  default_role: "student",
  timeout_seconds: "5",
};

export default function AdminPage() {
  const { t, language } = useLanguage();

  const [activeTab, setActiveTab] = useState<AdminTab>("overview");
  const [status, setStatus] = useState<string | null>(null);

  const [rbacFeedback, setRbacFeedback] = useState<InlineFeedback | null>(null);
  const [rbacRolesBusy, setRbacRolesBusy] = useState(false);
  const [rbacRoleSaveBusy, setRbacRoleSaveBusy] = useState(false);
  const [rbacAssignmentsBusy, setRbacAssignmentsBusy] = useState(false);
  const [rbacAssignBusy, setRbacAssignBusy] = useState(false);
  const [rbacRevokeBusyKey, setRbacRevokeBusyKey] = useState("");
  const [rbacRoles, setRbacRoles] = useState<RbacRoleEntry[]>([]);
  const [rbacAssignments, setRbacAssignments] = useState<RbacAssignmentEntry[]>([]);
  const [newRoleName, setNewRoleName] = useState("");
  const [newRolePermissions, setNewRolePermissions] = useState("admin.dashboard.read");
  const [assignUserId, setAssignUserId] = useState("");
  const [assignRoleName, setAssignRoleName] = useState("");
  const [assignmentUserFilter, setAssignmentUserFilter] = useState("");
  const [assignmentRoleFilter, setAssignmentRoleFilter] = useState("");

  const [integrationsLoading, setIntegrationsLoading] = useState(false);
  const [integrationsFeedback, setIntegrationsFeedback] = useState<InlineFeedback | null>(null);
  const [ldapFeedback, setLdapFeedback] = useState<InlineFeedback | null>(null);
  const [aiProviderFeedback, setAiProviderFeedback] = useState<Record<string, InlineFeedback | null>>({});
  const [ldapSaveBusy, setLdapSaveBusy] = useState(false);
  const [ldapTestServiceBusy, setLdapTestServiceBusy] = useState(false);
  const [ldapTestUserBusy, setLdapTestUserBusy] = useState(false);
  const [ldapStatus, setLdapStatus] = useState<LdapStatus | null>(null);
  const [ldapConfigForm, setLdapConfigForm] = useState<LdapConfigForm>(defaultLdapConfigForm);
  const [ldapTestLogin, setLdapTestLogin] = useState("");
  const [ldapTestPassword, setLdapTestPassword] = useState("");
  const [ldapTestResult, setLdapTestResult] = useState<string | null>(null);
  const [aiProviders, setAiProviders] = useState<AiProviderStatus[]>([]);
  const [aiConfigForm, setAiConfigForm] = useState<Record<string, AiProviderForm>>({});
  const [aiSaveBusyByProvider, setAiSaveBusyByProvider] = useState<Record<string, boolean>>({});
  const [aiValidateBusyByProvider, setAiValidateBusyByProvider] = useState<Record<string, boolean>>({});

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

  const uiLang = toUiLang(String(language));

  const l = adminTranslations[uiLang];
  const tx = useCallback((key: AdminTranslationKey, fallback?: string) => {
    const value = l[key] ?? adminTranslations.ru[key];
    if (value !== undefined) {
      return value;
    }
    if (fallback !== undefined) {
      return fallback;
    }
    if (process.env.NODE_ENV !== "production") {
      return `missing translation: ${String(key)}`;
    }
    return adminTranslations.ru.errorPrefix;
  }, [l]);

  const rbacFilterBadges = [
    assignmentUserFilter.trim() ? `${tx("rbacFilterUser")}: ${assignmentUserFilter.trim()}` : "",
    assignmentRoleFilter.trim() ? `${tx("rbacFilterRole")}: ${assignmentRoleFilter.trim()}` : "",
  ].filter(Boolean);
  const rbacAssignmentRows = useMemo(
    () => rbacAssignments.flatMap((row) => row.roles.map((role) => ({ user_id: row.user_id, role }))),
    [rbacAssignments],
  );
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


  const buildAuthHeaders = useCallback((): Record<string, string> => {
    const token = localStorage.getItem("app.token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, []);

  const {
    supportedLanguages,
    catalogQuery,
    availableCatalogLanguages,
    selectedCatalogCode,
    selectedCatalogLanguage,
    setCatalogQuery,
    setSelectedCatalogCode,
    addLanguage,
    setLanguageEnabled,
    deleteLanguage,
  } = useAdminLanguages({
    buildAuthHeaders,
    l,
    onStatusChange: setStatus,
  });

  const {
    dashboardLoading,
    overviewFeedback,
    dashboardSnapshot,
    exampleReferenceItems,
    dashboardStamp,
    enabledLanguageCodes,
    loadDashboard,
    touchDashboardStamp,
  } = useAdminOverview({
    activeTab,
    buildAuthHeaders,
    errorPrefix: l.errorPrefix,
    supportedLanguages,
    tx,
  });

  const {
    featureFlagsFeedback,
    featureFlagsLoading,
    featureFlagUpdateBusy,
    featureFlagSearch,
    featureFlagEnabledOnly,
    filteredFeatureFlags,
    featureFlagFilterBadges,
    hasActiveFeatureFlagFilters,
    featureFlagSummary,
    featureFlagsMutating,
    setFeatureFlagSearch,
    setFeatureFlagEnabledOnly,
    loadFeatureFlags,
    setFeatureFlagEnabled,
  } = useAdminFeatureFlags({
    activeTab,
    buildAuthHeaders,
    l,
    tx,
  });

  const {
    auditActor,
    auditAction,
    auditEntity,
    auditResult,
    auditCorrelationId,
    auditSince,
    auditEvents,
    auditFeedback,
    auditLoading,
    auditExportBusy,
    auditFilterBadges,
    hasActiveAuditFilters,
    auditLatestTimestamp,
    setAuditActor,
    setAuditAction,
    setAuditEntity,
    setAuditResult,
    setAuditCorrelationId,
    setAuditSince,
    loadAuditEvents,
    exportAudit,
    clearAuditFilters,
  } = useAdminAudit({
    activeTab,
    buildAuthHeaders,
    l,
    tx,
  });

  const enabledLanguages = supportedLanguages.filter((item) => item.enabled).length;
  const systemLanguages = supportedLanguages.filter((item) => item.system).length;

  const {
    localUsers,
    localFeedback,
    localCreateBusy,
    localListBusy,
    localDeleteBusy,
    localUpdateBusy,
    localPasswordBusy,
    localLogin,
    localPassword,
    localDisplayName,
    localRoles,
    localDefaultLanguage,
    localSearch,
    localRoleFilter,
    localLanguageFilter,
    selectedLocalUser,
    selectedLocalUserId,
    editLocalDisplayName,
    editLocalLanguage,
    editLocalRoles,
    editLocalPassword,
    editLocalPasswordConfirm,
    localFilterBadges,
    localUpdateHasChanges,
    setLocalLogin,
    setLocalPassword,
    setLocalDisplayName,
    setLocalRoles,
    setLocalDefaultLanguage,
    setLocalSearch,
    setLocalRoleFilter,
    setLocalLanguageFilter,
    setEditLocalDisplayName,
    setEditLocalLanguage,
    setEditLocalRoles,
    setEditLocalPassword,
    setEditLocalPasswordConfirm,
    loadLocalUsers,
    createLocalUser,
    selectLocalUser,
    revertLocalUserForm,
    clearLocalFilters,
    updateLocalUser,
    updateLocalUserPassword,
    deleteLocalUser,
  } = useAdminLocalUsers({
    activeTab,
    buildAuthHeaders,
    l,
    supportedLanguages,
    tx,
    onAfterCreate: async () => {
      await loadDashboard();
      touchDashboardStamp();
    },
    onAfterMutate: loadDashboard,
  });

  const loadIntegrationStatus = useCallback(async (showFeedback = false) => {
    setIntegrationsLoading(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const [ldapRes, aiRes, settingsRes] = await Promise.all([
        fetch(`${baseUrl}/admin/ldap/status`, {
          headers: buildAuthHeaders(),
          credentials: "include",
          cache: "no-store",
        }),
        fetch(`${baseUrl}/admin/ai/providers`, {
          headers: buildAuthHeaders(),
          credentials: "include",
          cache: "no-store",
        }),
        fetch(`${baseUrl}/admin/integrations/settings`, {
          headers: buildAuthHeaders(),
          credentials: "include",
          cache: "no-store",
        }),
      ]);

      if (ldapRes.ok) {
        const ldapJson = (await ldapRes.json()) as { ldap?: LdapStatus };
        setLdapStatus(ldapJson.ldap || null);
      }

      if (aiRes.ok) {
        const aiJson = (await aiRes.json()) as { providers?: AiProviderStatus[] };
        setAiProviders(aiJson.providers || []);
      }

      if (settingsRes.ok) {
        const settingsJson = (await settingsRes.json()) as {
          ldap?: {
            enabled?: boolean;
            server_uri?: string;
            bind_dn?: string;
            base_dn?: string;
            user_filter?: string;
            display_name_attribute?: string;
            login_attribute?: string;
            group_attribute?: string;
            group_role_map_json?: string;
            default_role?: string;
            timeout_seconds?: string | number;
          };
          ai_providers?: Array<{ provider: string; validation_url: string }>;
        };

        if (settingsJson.ldap) {
          setLdapConfigForm((current) => ({
            ...current,
            enabled: Boolean(settingsJson.ldap?.enabled),
            server_uri: settingsJson.ldap?.server_uri || "",
            bind_dn: settingsJson.ldap?.bind_dn || "",
            base_dn: settingsJson.ldap?.base_dn || "",
            user_filter: settingsJson.ldap?.user_filter || current.user_filter,
            display_name_attribute: settingsJson.ldap?.display_name_attribute || current.display_name_attribute,
            login_attribute: settingsJson.ldap?.login_attribute || current.login_attribute,
            group_attribute: settingsJson.ldap?.group_attribute || current.group_attribute,
            group_role_map_json: settingsJson.ldap?.group_role_map_json || current.group_role_map_json,
            default_role: settingsJson.ldap?.default_role || current.default_role,
            timeout_seconds: String(settingsJson.ldap?.timeout_seconds || current.timeout_seconds),
          }));
        }

        if (settingsJson.ai_providers) {
          const nextAiForm: Record<string, { apiKey: string; validationUrl: string }> = {};
          settingsJson.ai_providers.forEach((item) => {
            nextAiForm[item.provider] = {
              apiKey: "",
              validationUrl: item.validation_url || "",
            };
          });
          setAiConfigForm((current) => ({ ...current, ...nextAiForm }));
        }
      }

      const loadErrors: string[] = [];
      if (!ldapRes.ok) {
        loadErrors.push(`LDAP: ${ldapRes.status}`);
      }
      if (!aiRes.ok) {
        loadErrors.push(`AI: ${aiRes.status}`);
      }
      if (!settingsRes.ok) {
        loadErrors.push(`settings: ${settingsRes.status}`);
      }

      if (loadErrors.length > 0) {
        setIntegrationsFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${loadErrors.join(" | ")}`,
        });
      } else if (showFeedback) {
        setIntegrationsFeedback({ tone: "success", message: tx("integrationsReloaded") });
      } else {
        setIntegrationsFeedback(null);
      }
    } catch (error) {
      setIntegrationsFeedback({ tone: "error", message: String(error) });
    } finally {
      setIntegrationsLoading(false);
    }
  }, [buildAuthHeaders, l.errorPrefix, tx]);

  const loadRbacRoles = useCallback(async () => {
    setRbacRolesBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const res = await fetch(`${baseUrl}/admin/rbac/roles`, {
        headers: buildAuthHeaders(),
          credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      const json = (await res.json()) as { roles?: Record<string, string[]> };
      const rows = Object.entries(json.roles || {}).map(([name, permissions]) => ({
        name,
        permissions: permissions || [],
      }));
      setRbacRoles(rows);
      setAssignRoleName((current) => current || rows[0]?.name || "");
      setRbacFeedback(null);
    } catch (error) {
      setRbacFeedback({ tone: "error", message: String(error) });
    } finally {
      setRbacRolesBusy(false);
    }
  }, [buildAuthHeaders, l.errorPrefix]);

  const loadRbacAssignments = useCallback(async () => {
    setRbacAssignmentsBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const params = new URLSearchParams();
      if (assignmentUserFilter.trim()) {
        params.set("user_id", assignmentUserFilter.trim());
      }
      if (assignmentRoleFilter.trim()) {
        params.set("role", assignmentRoleFilter.trim());
      }

      const query = params.toString();
      const endpoint = query ? `${baseUrl}/admin/rbac/assignments?${query}` : `${baseUrl}/admin/rbac/assignments`;
      const res = await fetch(endpoint, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      const json = (await res.json()) as { assignments?: RbacAssignmentEntry[] };
      setRbacAssignments(json.assignments || []);
      setRbacFeedback(null);
    } catch (error) {
      setRbacFeedback({ tone: "error", message: String(error) });
    } finally {
      setRbacAssignmentsBusy(false);
    }
  }, [assignmentRoleFilter, assignmentUserFilter, buildAuthHeaders, l.errorPrefix]);

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

  const runRestore = async (dryRun: boolean) => {
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
  };

  useEffect(() => {
    if (activeTab !== "integrations") {
      return;
    }
    void loadIntegrationStatus();
  }, [activeTab, loadIntegrationStatus]);

  useEffect(() => {
    if (activeTab !== "rbac") {
      return;
    }
    void loadRbacRoles();
    void loadRbacAssignments();
  }, [activeTab, loadRbacAssignments, loadRbacRoles]);

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

  const saveRbacRole = async () => {
    setRbacFeedback(null);
    if (!newRoleName.trim()) {
      setRbacFeedback({ tone: "error", message: tx("rbacRoleRequired") });
      return;
    }

    setRbacRoleSaveBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/rbac/roles`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          name: newRoleName.trim(),
          permissions: newRolePermissions
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      setRbacFeedback({ tone: "success", message: tx("rbacRoleSaved") });
      setNewRoleName("");
      await loadRbacRoles();
    } catch (error) {
      setRbacFeedback({ tone: "error", message: String(error) });
    } finally {
      setRbacRoleSaveBusy(false);
    }
  };

  const assignRbacRole = async () => {
    setRbacFeedback(null);
    if (!assignUserId.trim() || !assignRoleName.trim()) {
      setRbacFeedback({ tone: "error", message: tx("rbacAssignRequired") });
      return;
    }

    setRbacAssignBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/rbac/assign`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          user_id: assignUserId.trim(),
          role: assignRoleName.trim(),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      setRbacFeedback({ tone: "success", message: tx("rbacAssigned") });
      await loadRbacAssignments();
      await loadDashboard();
    } catch (error) {
      setRbacFeedback({ tone: "error", message: String(error) });
    } finally {
      setRbacAssignBusy(false);
    }
  };

  const revokeRbacRole = async (userId: string, role: string) => {
    setRbacFeedback(null);
    const revokeLabel = `${userId} / ${role}`;
    const confirmed = window.confirm(
      tx("rbacRevokeConfirm") + `\n${revokeLabel}`,
    );
    if (!confirmed) {
      setRbacFeedback({ tone: "info", message: tx("rbacRevokeCancelled") });
      return;
    }

    setRbacRevokeBusyKey(`${userId}:${role}`);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(
        `${baseUrl}/admin/rbac/assignments/${encodeURIComponent(userId)}/${encodeURIComponent(role)}`,
        {
          method: "DELETE",
          headers: {
            ...buildAuthHeaders(),
            ...csrfHeaders,
          },
          credentials: "include",
        },
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      await loadRbacAssignments();
      await loadDashboard();
      setRbacFeedback({ tone: "success", message: tx("rbacRevoked") });
    } catch (error) {
      setRbacFeedback({ tone: "error", message: String(error) });
    } finally {
      setRbacRevokeBusyKey("");
    }
  };

  const clearRbacFilters = async () => {
    setAssignmentUserFilter("");
    setAssignmentRoleFilter("");
    setRbacFeedback(null);
    setRbacAssignmentsBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const res = await fetch(`${baseUrl}/admin/rbac/assignments`, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      const json = (await res.json()) as { assignments?: RbacAssignmentEntry[] };
      setRbacAssignments(json.assignments || []);
    } catch (error) {
      setRbacFeedback({ tone: "error", message: String(error) });
    } finally {
      setRbacAssignmentsBusy(false);
    }
  };

  const testLdapConnection = async (withUserBind: boolean) => {
    setLdapFeedback(null);
    setLdapTestResult(null);
    if (withUserBind) {
      setLdapTestUserBusy(true);
    } else {
      setLdapTestServiceBusy(true);
    }
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/ldap/test-connection`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify(
          withUserBind
            ? { username: ldapTestLogin, password: ldapTestPassword }
            : {},
        ),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setLdapFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      const json = (await res.json()) as { result?: { status?: string; user_check?: { user_id?: string; roles?: string[] } } };
      const details = json.result?.user_check
        ? `${l.validationOk}: ${json.result.user_check.user_id} (${(json.result.user_check.roles || []).join(", ")})`
        : l.serviceBindOk;
      setLdapTestResult(details);
      setLdapFeedback({ tone: "success", message: tx("validationOk") });
      await loadIntegrationStatus();
    } catch (error) {
      setLdapFeedback({ tone: "error", message: String(error) });
    } finally {
      if (withUserBind) {
        setLdapTestUserBusy(false);
      } else {
        setLdapTestServiceBusy(false);
      }
    }
  };

  const validateProvider = async (provider: string) => {
    setAiProviderFeedback((current) => ({ ...current, [provider]: null }));
    setAiValidateBusyByProvider((current) => ({ ...current, [provider]: true }));
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/ai/providers/${provider}/validate`, {
        method: "POST",
        headers: {
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setAiProviderFeedback((current) => ({
          ...current,
          [provider]: {
            tone: "error",
            message: `${l.errorPrefix}: ${String(err.detail || res.status)}`,
          },
        }));
        return;
      }

      const json = (await res.json()) as { result?: { http_status?: number } };
      setAiProviderFeedback((current) => ({
        ...current,
        [provider]: {
          tone: "success",
          message: `${l.validationOk} (${json.result?.http_status || 200})`,
        },
      }));
      await loadIntegrationStatus();
    } catch (error) {
      setAiProviderFeedback((current) => ({
        ...current,
        [provider]: { tone: "error", message: String(error) },
      }));
    } finally {
      setAiValidateBusyByProvider((current) => ({ ...current, [provider]: false }));
    }
  };

  const saveLdapConfig = async () => {
    setLdapFeedback(null);
    setLdapSaveBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const ldapPayload: Record<string, unknown> = {
        ...ldapConfigForm,
        timeout_seconds: Number(ldapConfigForm.timeout_seconds || "5"),
      };
      if (!ldapConfigForm.bind_password.trim()) {
        delete ldapPayload.bind_password;
      }
      const res = await fetch(`${baseUrl}/admin/integrations/ldap`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify(ldapPayload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setLdapFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      setLdapFeedback({ tone: "success", message: l.ldapSaved });
      await loadIntegrationStatus();
    } catch (error) {
      setLdapFeedback({ tone: "error", message: String(error) });
    } finally {
      setLdapSaveBusy(false);
    }
  };

  const saveProviderConfig = async (provider: string) => {
    setAiProviderFeedback((current) => ({ ...current, [provider]: null }));
    setAiSaveBusyByProvider((current) => ({ ...current, [provider]: true }));
    const form = aiConfigForm[provider] || { apiKey: "", validationUrl: "" };
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const providerPayload: Record<string, string> = {
        validation_url: form.validationUrl,
      };
      if (form.apiKey.trim()) {
        providerPayload.api_key = form.apiKey;
      }
      const res = await fetch(`${baseUrl}/admin/integrations/ai/${provider}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify(providerPayload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setAiProviderFeedback((current) => ({
          ...current,
          [provider]: {
            tone: "error",
            message: `${l.errorPrefix}: ${err.detail || res.status}`,
          },
        }));
        return;
      }

      setAiProviderFeedback((current) => ({
        ...current,
        [provider]: { tone: "success", message: l.providerSaved },
      }));
      setAiConfigForm((current) => ({
        ...current,
        [provider]: {
          ...form,
          apiKey: "",
        },
      }));
      await loadIntegrationStatus();
    } catch (error) {
      setAiProviderFeedback((current) => ({
        ...current,
        [provider]: { tone: "error", message: String(error) },
      }));
    } finally {
      setAiSaveBusyByProvider((current) => ({ ...current, [provider]: false }));
    }
  };

  const updateBackupProfile = (index: number, field: keyof BackupProfile, value: string) => {
    setBackupProfilesForm((current) =>
      current.map((profile, idx) => (idx === index ? { ...profile, [field]: value } : profile)),
    );
  };

  const addBackupProfile = () => {
    setBackupProfilesForm((current) => [
      ...current,
      { id: `profile${current.length + 1}`, label: "New profile", path: "/tmp/app-backups/new-profile" },
    ]);
  };

  const removeBackupProfile = (index: number) => {
    setBackupProfilesForm((current) => current.filter((_, idx) => idx !== index));
  };

  const saveBackupProfiles = async () => {
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
  };

  const applyRetention = async (dryRun: boolean) => {
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
  };

  const runBackupNow = async () => {
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
  };

  const adminSections: AdminSection[] = [
    { id: "overview", label: l.overview, icon: "◧" },
    { id: "languages", label: l.languages, icon: "⟲" },
    { id: "local-users", label: l.localUsers, icon: "◫" },
    { id: "rbac", label: tx("rbac"), icon: "◎" },
    { id: "integrations", label: l.integrations, icon: "◇" },
    { id: "backups", label: tx("backups"), icon: "▣" },
    { id: "audit", label: l.audit, icon: "◌" },
    { id: "feature-flags", label: tx("featureFlags"), icon: "✦" },
    { id: "example-notes", label: tx("exampleNotesTab", "Example Notes"), icon: "▤" },
  ];

  return (
    <AdminShell
      activeTab={activeTab}
      onTabChange={(tab) => setActiveTab(tab as AdminTab)}
      sections={adminSections}
      platformName={t("admin.title")}
      headerControls={
        <div className="shellHeaderMeta">
          <span>{l.adminUser}</span>
          <small>{tx("authManagedByBackend")}</small>
        </div>
      }
    >
    <main className="adminRoot" data-testid="admin-page-shell">
      <section className="hero cardFade">
        <div>
          <p className="kicker">{l.controlCenter}</p>
          <h1>{t("admin.title")}</h1>
          <p>{t("admin.subtitle")}</p>
          <p className="stamp">{l.lastChange}: {dashboardStamp}</p>
        </div>
        <div className="heroRight">
          <p>{l.adminUser}</p>
          <small>{tx("authManagedByBackend")}</small>
        </div>
      </section>

      <section className="statGrid cardFade">
        <article className="statCard">
          <span>{l.enabledLanguages}</span>
          <strong>{enabledLanguages}</strong>
          <small>{l.total}: {supportedLanguages.length}</small>
        </article>
        <article className="statCard">
          <span>{l.systemLanguages}</span>
          <strong>{systemLanguages}</strong>
          <small>{l.protectedCore}</small>
        </article>
        <article className="statCard">
          <span>{l.localUsers}</span>
          <strong>{dashboardSnapshot?.users.local_users_count ?? localUsers.length}</strong>
          <small>{l.nonAdAccounts}</small>
        </article>
        <article className="statCard">
          <span>{l.adminMode}</span>
          <strong>{l.adminActive}</strong>
          <small>{l.rbacEnforced}</small>
        </article>
      </section>

      <section className="panel cardFade">
        {activeTab === "overview" ? (
          <AdminOverviewTab
            l={l}
            tx={tx}
            dashboardStamp={dashboardStamp}
            dashboardLoading={dashboardLoading}
            overviewFeedback={overviewFeedback}
            dashboardSnapshot={dashboardSnapshot}
            enabledLanguageCodes={enabledLanguageCodes}
            exampleReferenceItems={exampleReferenceItems}
            onRefresh={loadDashboard}
          />
        ) : null}

        {activeTab === "languages" ? (
          <AdminLanguagesTab
            l={l}
            catalogQuery={catalogQuery}
            availableCatalogLanguages={availableCatalogLanguages}
            selectedCatalogCode={selectedCatalogCode}
            selectedCatalogLanguage={selectedCatalogLanguage}
            supportedLanguages={supportedLanguages}
            onCatalogQueryChange={setCatalogQuery}
            onSelectCatalogCode={setSelectedCatalogCode}
            onAddLanguage={addLanguage}
            onToggleLanguageEnabled={setLanguageEnabled}
            onDeleteLanguage={deleteLanguage}
          />
        ) : null}

        {activeTab === "local-users" ? (
          <AdminLocalUsersTab
            l={l}
            tx={tx}
            supportedLanguages={supportedLanguages}
            localFeedback={localFeedback}
            localLogin={localLogin}
            localPassword={localPassword}
            localDisplayName={localDisplayName}
            localRoles={localRoles}
            localDefaultLanguage={localDefaultLanguage}
            localCreateBusy={localCreateBusy}
            localListBusy={localListBusy}
            localSearch={localSearch}
            localRoleFilter={localRoleFilter}
            localLanguageFilter={localLanguageFilter}
            localUsers={localUsers}
            localFilterBadges={localFilterBadges}
            selectedLocalUser={selectedLocalUser}
            selectedLocalUserId={selectedLocalUserId}
            editLocalDisplayName={editLocalDisplayName}
            editLocalLanguage={editLocalLanguage}
            editLocalRoles={editLocalRoles}
            editLocalPassword={editLocalPassword}
            editLocalPasswordConfirm={editLocalPasswordConfirm}
            localUpdateHasChanges={localUpdateHasChanges}
            localUpdateBusy={localUpdateBusy}
            localDeleteBusy={localDeleteBusy}
            localPasswordBusy={localPasswordBusy}
            onLocalLoginChange={setLocalLogin}
            onLocalPasswordChange={setLocalPassword}
            onLocalDisplayNameChange={setLocalDisplayName}
            onLocalRolesChange={setLocalRoles}
            onLocalDefaultLanguageChange={setLocalDefaultLanguage}
            onCreateLocalUser={createLocalUser}
            onRefreshLocalUsers={() => loadLocalUsers()}
            onLocalSearchChange={setLocalSearch}
            onLocalRoleFilterChange={setLocalRoleFilter}
            onLocalLanguageFilterChange={setLocalLanguageFilter}
            onClearLocalFilters={clearLocalFilters}
            onSelectLocalUser={selectLocalUser}
            onEditLocalDisplayNameChange={setEditLocalDisplayName}
            onEditLocalLanguageChange={setEditLocalLanguage}
            onEditLocalRolesChange={setEditLocalRoles}
            onUpdateLocalUser={updateLocalUser}
            onRevertLocalUserForm={revertLocalUserForm}
            onDeleteLocalUser={deleteLocalUser}
            onEditLocalPasswordChange={setEditLocalPassword}
            onEditLocalPasswordConfirmChange={setEditLocalPasswordConfirm}
            onUpdateLocalUserPassword={updateLocalUserPassword}
          />
        ) : null}

        {activeTab === "rbac" ? (
          <AdminRbacTab
            l={l}
            tx={tx}
            rbacFeedback={rbacFeedback}
            newRoleName={newRoleName}
            newRolePermissions={newRolePermissions}
            rbacRoleSaveBusy={rbacRoleSaveBusy}
            rbacRolesBusy={rbacRolesBusy}
            rbacRoles={rbacRoles}
            assignUserId={assignUserId}
            assignRoleName={assignRoleName}
            rbacAssignBusy={rbacAssignBusy}
            rbacAssignmentsBusy={rbacAssignmentsBusy}
            assignmentUserFilter={assignmentUserFilter}
            assignmentRoleFilter={assignmentRoleFilter}
            rbacAssignmentRows={rbacAssignmentRows}
            rbacAssignmentsCount={rbacAssignments.length}
            rbacFilterBadges={rbacFilterBadges}
            rbacRevokeBusyKey={rbacRevokeBusyKey}
            onNewRoleNameChange={setNewRoleName}
            onNewRolePermissionsChange={setNewRolePermissions}
            onSaveRbacRole={saveRbacRole}
            onLoadRbacRoles={loadRbacRoles}
            onAssignUserIdChange={setAssignUserId}
            onAssignRoleNameChange={setAssignRoleName}
            onAssignRbacRole={assignRbacRole}
            onLoadRbacAssignments={loadRbacAssignments}
            onClearRbacFilters={clearRbacFilters}
            onAssignmentUserFilterChange={setAssignmentUserFilter}
            onAssignmentRoleFilterChange={setAssignmentRoleFilter}
            onRevokeRbacRole={revokeRbacRole}
          />
        ) : null}

        {activeTab === "integrations" ? (
          <AdminIntegrationsTab
            l={l}
            tx={tx}
            ldapStatus={ldapStatus}
            ldapConfigForm={ldapConfigForm}
            ldapTestLogin={ldapTestLogin}
            ldapTestPassword={ldapTestPassword}
            ldapTestResult={ldapTestResult}
            integrationsFeedback={integrationsFeedback}
            ldapFeedback={ldapFeedback}
            aiProviderFeedback={aiProviderFeedback}
            integrationsLoading={integrationsLoading}
            ldapSaveBusy={ldapSaveBusy}
            ldapTestServiceBusy={ldapTestServiceBusy}
            ldapTestUserBusy={ldapTestUserBusy}
            aiSaveBusyByProvider={aiSaveBusyByProvider}
            aiValidateBusyByProvider={aiValidateBusyByProvider}
            aiProviders={aiProviders}
            aiConfigForm={aiConfigForm}
            onReloadIntegrations={loadIntegrationStatus}
            onLdapConfigChange={setLdapConfigForm}
            onLdapTestLoginChange={setLdapTestLogin}
            onLdapTestPasswordChange={setLdapTestPassword}
            onSaveLdapConfig={saveLdapConfig}
            onTestLdapConnection={testLdapConnection}
            onAiConfigFormChange={(provider, value) => setAiConfigForm((current) => ({ ...current, [provider]: value }))}
            onSaveProviderConfig={saveProviderConfig}
            onValidateProvider={validateProvider}
          />
        ) : null}

        {activeTab === "backups" ? (
          <AdminBackupsTab
            tx={tx}
            backupAllowedRoots={backupAllowedRoots}
            backupFeedback={backupFeedback}
            backupActionsBusy={backupActionsBusy}
            backupListLoading={backupListLoading}
            backupActiveProfile={backupActiveProfile}
            backupProfilesForm={backupProfilesForm}
            retentionDays={retentionDays}
            retentionMinFiles={retentionMinFiles}
            restoreProfileId={restoreProfileId}
            restoreFileName={restoreFileName}
            restoreCandidates={restoreCandidates}
            backupJobsSorted={backupJobsSorted}
            backupSummaryCount={backupSummaryCount}
            backupSummaryLatest={backupSummaryLatest}
            backupSummaryStatus={backupSummaryStatus}
            restoreCandidateNames={restoreCandidateNames}
            onLoadBackupStatus={loadBackupStatus}
            onBackupActiveProfileChange={setBackupActiveProfile}
            onAddBackupProfile={addBackupProfile}
            onUpdateBackupProfile={updateBackupProfile}
            onRemoveBackupProfile={removeBackupProfile}
            onSaveBackupProfiles={saveBackupProfiles}
            onRunBackupNow={runBackupNow}
            onRetentionDaysChange={setRetentionDays}
            onRetentionMinFilesChange={setRetentionMinFiles}
            onApplyRetention={applyRetention}
            onRestoreProfileIdChange={(value) => {
              setRestoreProfileId(value);
              setRestoreFileName("");
            }}
            onRestoreFileNameChange={setRestoreFileName}
            onLoadRestoreCandidates={loadRestoreCandidates}
            onRunRestore={runRestore}
          />
        ) : null}

        {activeTab === "feature-flags" ? (
          <AdminFeatureFlagsTab
            tx={tx}
            featureFlagsLoading={featureFlagsLoading}
            featureFlagsMutating={featureFlagsMutating}
            featureFlagSearch={featureFlagSearch}
            featureFlagEnabledOnly={featureFlagEnabledOnly}
            featureFlagsFeedback={featureFlagsFeedback}
            featureFlagSummary={featureFlagSummary}
            hasActiveFeatureFlagFilters={hasActiveFeatureFlagFilters}
            featureFlagFilterBadges={featureFlagFilterBadges}
            filteredFeatureFlags={filteredFeatureFlags}
            featureFlagUpdateBusy={featureFlagUpdateBusy}
            onLoadFeatureFlags={loadFeatureFlags}
            onFeatureFlagSearchChange={setFeatureFlagSearch}
            onFeatureFlagEnabledOnlyChange={setFeatureFlagEnabledOnly}
            onSetFeatureFlagEnabled={setFeatureFlagEnabled}
          />
        ) : null}

        {activeTab === "example-notes" ? (
          <AdminExampleNotesTab
            baseUrl={process.env.NEXT_PUBLIC_API_BASE_URL || "/api"}
            buildAuthHeaders={buildAuthHeaders}
            tx={tx}
          />
        ) : null}

        {activeTab === "audit" ? (
          <AdminAuditTab
            l={l}
            tx={tx}
            auditActor={auditActor}
            auditAction={auditAction}
            auditEntity={auditEntity}
            auditResult={auditResult}
            auditCorrelationId={auditCorrelationId}
            auditSince={auditSince}
            auditLoading={auditLoading}
            auditExportBusy={auditExportBusy}
            auditFeedback={auditFeedback}
            hasActiveAuditFilters={hasActiveAuditFilters}
            auditEvents={auditEvents}
            auditLatestTimestamp={auditLatestTimestamp}
            auditFilterBadges={auditFilterBadges}
            onAuditActorChange={setAuditActor}
            onAuditActionChange={setAuditAction}
            onAuditEntityChange={setAuditEntity}
            onAuditResultChange={setAuditResult}
            onAuditCorrelationIdChange={setAuditCorrelationId}
            onAuditSinceChange={setAuditSince}
            onLoadAuditEvents={loadAuditEvents}
            onClearAuditFilters={clearAuditFilters}
            onExportAudit={exportAudit}
          />
        ) : null}

        {status ? <p className="statusLine">{status}</p> : null}
      </section>

      <style>{`
        .adminRoot {
          --paper: #f3f6fa;
          --sand: #efe7d3;
          --ink: #17212f;
          --muted: #5f6f84;
          --line: #dce4ef;
          --accent: #2563eb;
          --accent-2: #b45309;
          min-height: 100%;
          padding: 20px;
          background: transparent;
          color: var(--ink);
          font-family: "Space Grotesk", "IBM Plex Sans", "Segoe UI", sans-serif;
        }

        .shellHeaderMeta {
          display: grid;
          gap: 1px;
          text-align: right;
          color: #607085;
          font-size: 11px;
        }

        .shellHeaderMeta span,
        .shellHeaderMeta small {
          margin: 0;
        }

        .hero,
        .statGrid,
        .tabs,
        .panel {
          width: min(1220px, 100%);
          margin: 0 auto;
        }

        .hero {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 18px;
          background: #ffffff;
          border: 1px solid var(--line);
          border-radius: 14px;
          padding: 18px;
          box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
        }

        .kicker {
          margin: 0 0 6px;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--accent);
          font-size: 11px;
          font-weight: 700;
        }

        h1 {
          margin: 0;
          font-size: clamp(24px, 3.2vw, 34px);
          line-height: 1.15;
        }

        h2 {
          margin: 0 0 8px;
          font-size: 20px;
        }

        p {
          margin: 8px 0;
        }

        .stamp {
          color: var(--muted);
          font-size: 12px;
        }

        .heroRight {
          display: grid;
          gap: 6px;
          align-content: start;
          background: #f8fbff;
            border-radius: 12px;
2337c            border: 1px solid var(--line);
2338c            padding: 11px 12px;
2339,2340d
;2367s/0.07em/0.06em/;2372s/8px/7px/;2373s/28px/26px/;2389s/#ffffff/#f8fbff/;2390s/var(--ink)/#314256/;2403s/var(--ink)/#243449/;2405s/var(--ink)/#243449/;2410c          background: #ffffff;
;2411c          border: 1px solid var(--line);
;2412s/18px/14px/;2413s/18px/16px/;2414c          box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
;2430s/14px/12px/;2431s/14px/13px/
          border-radius: 14px;
          border: 1px solid var(--line);
          padding: 12px;
        }

        .heroRight p {
          margin: 0;
          color: var(--muted);
          font-size: 13px;
        }

        .statGrid {
          margin-top: 18px;
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
        }

        .statCard {
          background: #ffffff;
          border: 1px solid var(--line);
          border-radius: 14px;
          padding: 12px;
          box-shadow: 0 8px 22px rgba(23, 33, 47, 0.06);
        }

        .statCard span {
          display: block;
          color: var(--muted);
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.07em;
        }

        .statCard strong {
          display: block;
          margin-top: 8px;
          font-size: 28px;
        }

        .statCard small {
          color: var(--muted);
        }

        .tabs {
          margin-top: 14px;
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        .tabButton {
          border: 1px solid var(--line);
          background: #ffffff;
          color: var(--ink);
          border-radius: 999px;
          padding: 9px 14px;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s ease, background 0.2s ease;
        }

        .tabButton:hover {
          transform: translateY(-1px);
        }

        .tabButtonActive {
          background: var(--ink);
          color: #fff;
          border-color: var(--ink);
        }

        .panel {
          margin-top: 14px;
          background: rgba(255, 255, 255, 0.82);
          border: 1px solid rgba(255, 255, 255, 0.9);
          border-radius: 18px;
          padding: 18px;
          box-shadow: 0 20px 45px rgba(23, 33, 47, 0.09);
        }

        .subText {
          color: var(--muted);
          margin-top: 0;
        }

        .grid2 {
          display: grid;
          gap: 14px;
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .panelCard {
          border: 1px solid var(--line);
          border-radius: 14px;
          padding: 14px;
          background: #fff;
        }

        .integrationDetails {
          display: grid;
          gap: 8px;
          margin-top: 12px;
        }

        .toggleRow {
          display: inline-flex;
          gap: 8px;
          align-items: center;
          font-size: 14px;
        }

        .integrationDetails p {
          margin: 0;
        }

        .compactFormGrid {
          margin-top: 4px;
        }

        .providerStack {
          display: grid;
          gap: 10px;
          margin-top: 12px;
        }

        .providerCard {
          border: 1px solid var(--line);
          border-radius: 12px;
          padding: 12px;
          display: grid;
          gap: 8px;
        }

        .providerCard p {
          margin: 0;
        }

        .providerActions {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          align-items: center;
        }

        .plainList {
          margin: 0;
          padding-left: 18px;
          display: grid;
          gap: 6px;
        }

        .formGrid {
          display: grid;
          gap: 8px;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          margin-top: 10px;
        }

        .languagePickerGrid {
          display: grid;
          gap: 12px;
          grid-template-columns: 1.4fr 1fr;
          margin-top: 12px;
        }

        .catalogCard {
          border: 1px solid var(--line);
          border-radius: 14px;
          padding: 14px;
          background: #fff;
        }

        .catalogCard h3 {
          margin: 0 0 8px;
          font-size: 18px;
        }

        .catalogList {
          margin-top: 10px;
          max-height: 280px;
          overflow-y: auto;
          display: grid;
          gap: 8px;
          padding-right: 4px;
        }

        .catalogItem {
          display: grid;
          gap: 4px;
          text-align: left;
          padding: 10px 12px;
          border: 1px solid var(--line);
          border-radius: 12px;
          background: #fff;
          cursor: pointer;
        }

        .catalogItem small {
          color: var(--muted);
        }

        .catalogItemActive {
          border-color: var(--accent);
          background: #eef5ff;
          box-shadow: inset 0 0 0 1px rgba(15, 118, 110, 0.15);
        }

        .selectedLanguageCard {
          display: grid;
          gap: 8px;
        }

        .selectedLanguageCard p {
          margin: 0;
        }

        input,
        select,
        button {
          font: inherit;
        }

        input,
        select {
          border: 1px solid var(--line);
          background: #fff;
          border-radius: 10px;
          padding: 10px;
          color: var(--ink);
        }

        .rowButtons {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .primary {
          border: 0;
          border-radius: 10px;
          padding: 10px 14px;
          background: linear-gradient(135deg, var(--accent), #0ea5a3);
          color: #fff;
          font-weight: 700;
          cursor: pointer;
        }

        .ghost {
          border: 1px solid var(--line);
          border-radius: 10px;
          padding: 8px 10px;
          background: #fff;
          color: var(--ink);
          cursor: pointer;
        }

        .danger {
          color: var(--accent-2);
          border-color: #e9b9a8;
        }

        .tableWrap {
          overflow-x: auto;
          border: 1px solid var(--line);
          border-radius: 12px;
          margin-top: 14px;
          background: #fff;
        }

        table {
          width: 100%;
          border-collapse: collapse;
          min-width: 680px;
        }

        th,
        td {
          text-align: left;
          padding: 10px;
          border-bottom: 1px solid #ece6d4;
          vertical-align: top;
        }

        th {
          background: #f8f4e8;
          font-size: 13px;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: #495567;
        }

        .actionCell {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .badgeRow {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          margin-top: 12px;
        }

        .badge {
          display: inline-flex;
          padding: 5px 10px;
          border-radius: 999px;
          background: #eef2ff;
          color: #3730a3;
          border: 1px solid #c7d2fe;
          font-size: 12px;
          font-weight: 700;
        }

        .badgeOk {
          background: #ecfdf5;
          color: #065f46;
          border-color: #a7f3d0;
        }

        .badgeWarn {
          background: #fff7ed;
          color: #9a3412;
          border-color: #fdba74;
        }

        .badgeErr {
          background: #fef2f2;
          color: #991b1b;
          border-color: #fca5a5;
        }

        .badgeInfo {
          background: #eff6ff;
          color: #1d4ed8;
          border-color: #bfdbfe;
        }

        .statusGrid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 8px;
        }

        .statusItem {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          border: 1px solid var(--line);
          border-radius: 10px;
          padding: 8px 10px;
          background: #fafaf7;
          font-size: 14px;
        }

        .rowMeta {
          display: flex;
          flex-wrap: wrap;
          justify-content: space-between;
          align-items: center;
          gap: 8px;
          margin-top: 10px;
        }

        .inlineFeedback {
          margin: 8px 0 0;
          padding: 9px 11px;
          border-radius: 10px;
          border: 1px solid;
          font-size: 14px;
        }

        .inlineFeedbackSuccess {
          background: #ecfdf5;
          color: #065f46;
          border-color: #a7f3d0;
        }

        .inlineFeedbackError {
          background: #fef2f2;
          color: #991b1b;
          border-color: #fca5a5;
        }

        .inlineFeedbackInfo {
          background: #eff6ff;
          color: #1d4ed8;
          border-color: #bfdbfe;
        }

        .featureFlagList {
          display: grid;
          gap: 10px;
          margin-top: 12px;
        }

        .featureFlagRow {
          border: 1px solid var(--line);
          border-radius: 12px;
          padding: 12px;
          background: #fff;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }

        .featureFlagInfo {
          display: grid;
          gap: 6px;
        }

        .featureFlagKey {
          margin: 0;
          font-weight: 700;
          font-family: "IBM Plex Mono", "SFMono-Regular", Menlo, monospace;
          font-size: 14px;
        }

        .featureFlagBadges {
          margin-top: 0;
        }

        .featureFlagFilterBadges {
          margin-top: 0;
        }

        .featureFlagLastChanged {
          margin: 0;
        }

        .featureFlagActions {
          display: inline-flex;
          align-items: center;
          gap: 8px;
        }

        .featureFlagSwitch {
          width: 48px;
          height: 28px;
          border-radius: 999px;
          border: 1px solid #d1d5db;
          background: #e5e7eb;
          display: inline-flex;
          align-items: center;
          padding: 2px;
          cursor: pointer;
        }

        .featureFlagSwitchKnob {
          width: 22px;
          height: 22px;
          border-radius: 999px;
          background: #fff;
          border: 1px solid #d1d5db;
          transition: transform 0.2s ease;
        }

        .featureFlagSwitchOn {
          background: #99f6e4;
          border-color: #5eead4;
          justify-content: flex-end;
        }

        .featureFlagSwitch:disabled {
          cursor: not-allowed;
          opacity: 0.6;
        }

        .statusLine {
          margin: 14px 0 0;
          padding: 10px 12px;
          border-radius: 10px;
          background: #eef5ff;
          border: 1px solid #cfe0fb;
          color: #274265;
        }

        .truncateMono {
          max-width: 180px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          font-family: "IBM Plex Mono", "SFMono-Regular", Menlo, monospace;
          font-size: 12px;
        }

        .cardFade {
          animation: riseIn 520ms ease;
        }

        @keyframes riseIn {
          from {
            opacity: 0;
            transform: translateY(8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @media (max-width: 980px) {
          .hero {
            grid-template-columns: 1fr;
          }

          .statGrid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .grid2,
          .formGrid,
          .languagePickerGrid {
            grid-template-columns: 1fr;
          }

          .statusGrid {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 640px) {
          .adminRoot {
            padding: 14px;
          }

          .statGrid {
            grid-template-columns: 1fr;
          }

          .tabs {
            gap: 6px;
          }

          .tabButton {
            padding: 8px 12px;
          }

          .featureFlagRow {
            flex-direction: column;
            align-items: flex-start;
          }

          .featureFlagActions {
            width: 100%;
          }
        }
      `}</style>
    </main>
    </AdminShell>
  );
}
