"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import { buildCsrfHeaders } from "../components/csrf";
import { useLanguage } from "../components/LanguageProvider";
import { AdminAuditTab } from "./components/AdminAuditTab";
import { AdminBackupsTab } from "./components/AdminBackupsTab";
import { AdminFeatureFlagsTab } from "./components/AdminFeatureFlagsTab";
import { AdminIntegrationsTab } from "./components/AdminIntegrationsTab";
import { AdminLanguagesTab } from "./components/AdminLanguagesTab";
import { AdminLocalUsersTab } from "./components/AdminLocalUsersTab";
import { AdminOverviewTab } from "./components/AdminOverviewTab";
import { AdminRbacTab } from "./components/AdminRbacTab";
import type {
  AdminCopy,
  AdminTab,
  AiProviderForm,
  AiProviderStatus,
  AuditEvent,
  BackupJob,
  BackupProfile,
  CatalogLanguage,
  DashboardSnapshot,
  ExampleReferenceItem,
  FeatureFlag,
  InlineFeedback,
  LdapConfigForm,
  LdapStatus,
  LocalUser,
  RbacAssignmentEntry,
  RbacRoleEntry,
  RestoreCandidate,
  SupportedLanguage,
  UiLang,
} from "./types";

const toUiLang = (value: string): UiLang => {
  if (value === "en" || value === "kk" || value === "zh") {
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
  const [supportedLanguages, setSupportedLanguages] = useState<SupportedLanguage[]>([]);
  const [languageCatalog, setLanguageCatalog] = useState<CatalogLanguage[]>([]);
  const [selectedCatalogCode, setSelectedCatalogCode] = useState("");
  const [catalogQuery, setCatalogQuery] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [overviewFeedback, setOverviewFeedback] = useState<InlineFeedback | null>(null);
  const [dashboardSnapshot, setDashboardSnapshot] = useState<DashboardSnapshot | null>(null);
  const [exampleReferenceItems, setExampleReferenceItems] = useState<ExampleReferenceItem[]>([]);
  const [dashboardStamp, setDashboardStamp] = useState(() => new Date().toLocaleString());

  const [localUsers, setLocalUsers] = useState<LocalUser[]>([]);
  const [localFeedback, setLocalFeedback] = useState<InlineFeedback | null>(null);
  const [localCreateBusy, setLocalCreateBusy] = useState(false);
  const [localListBusy, setLocalListBusy] = useState(false);
  const [localDeleteBusy, setLocalDeleteBusy] = useState(false);
  const [localUpdateBusy, setLocalUpdateBusy] = useState(false);
  const [localPasswordBusy, setLocalPasswordBusy] = useState(false);
  const [localLogin, setLocalLogin] = useState("");
  const [localPassword, setLocalPassword] = useState("");
  const [localDisplayName, setLocalDisplayName] = useState("");
  const [localRoles, setLocalRoles] = useState("student");
  const [localDefaultLanguage, setLocalDefaultLanguage] = useState("ru");
  const [localSearch, setLocalSearch] = useState("");
  const [localRoleFilter, setLocalRoleFilter] = useState("");
  const [localLanguageFilter, setLocalLanguageFilter] = useState("");
  const [selectedLocalUserId, setSelectedLocalUserId] = useState("");
  const [editLocalDisplayName, setEditLocalDisplayName] = useState("");
  const [editLocalLanguage, setEditLocalLanguage] = useState("ru");
  const [editLocalRoles, setEditLocalRoles] = useState("student");
  const [editLocalPassword, setEditLocalPassword] = useState("");
  const [editLocalPasswordConfirm, setEditLocalPasswordConfirm] = useState("");

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

  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [auditFeedback, setAuditFeedback] = useState<InlineFeedback | null>(null);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditExportBusy, setAuditExportBusy] = useState<"" | "csv" | "json">("");
  const [auditActor, setAuditActor] = useState("");
  const [auditAction, setAuditAction] = useState("");
  const [auditEntity, setAuditEntity] = useState("");
  const [auditResult, setAuditResult] = useState("");
  const [auditCorrelationId, setAuditCorrelationId] = useState("");
  const [auditSince, setAuditSince] = useState("");

  const [featureFlags, setFeatureFlags] = useState<FeatureFlag[]>([]);
  const [featureFlagsFeedback, setFeatureFlagsFeedback] = useState<InlineFeedback | null>(null);
  const [featureFlagsLoading, setFeatureFlagsLoading] = useState(false);
  const [featureFlagUpdateBusy, setFeatureFlagUpdateBusy] = useState<Record<string, boolean>>({});
  const [featureFlagSearch, setFeatureFlagSearch] = useState("");
  const [featureFlagEnabledOnly, setFeatureFlagEnabledOnly] = useState(false);

  const uiLang = toUiLang(String(language));

  const labels: Record<UiLang, AdminCopy> = {
    ru: {
      controlCenter: "Платформенный центр управления",
      lastChange: "Последнее изменение",
      adminUser: "Администратор",
      enabledLanguages: "Включенные языки",
      total: "Всего",
      systemLanguages: "Системные языки",
      protectedCore: "Защищенное ядро",
      localUsers: "Локальные пользователи",
      nonAdAccounts: "Аккаунты без AD",
      adminMode: "Режим админа",
      adminActive: "Активен",
      rbacEnforced: "RBAC активен",
      overview: "Обзор",
      languages: "Языки",
      integrations: "Интеграции",
      backups: "Бэкапы",
      audit: "Аудит",
      platformModules: "Платформенные модули",
      operationalFocus: "Операционный фокус",
      usersRoles: "Пользователи и роли",
      ldapSettings: "LDAP/AD настройки",
      aiControls: "Управление AI-провайдерами",
      auditEvents: "Аудит и события безопасности",
      trackChanges: "Отслеживай изменения ролей и привилегированные действия",
      keepI18n: "Поддерживай i18n-ядро (`kk`, `ru`, `en`) в рабочем состоянии",
      controlledExceptions: "Используй local users только как контролируемое исключение",
      documentActions: "Документируй каждое важное админ-действие",
      languageManagement: "Управление языками",
      langHelp: "Добавляй языки без ломки ядра. Системные языки защищены.",
      catalogTitle: "Каталог языков",
      catalogHelp: "Выбери язык из справочника. Список прокручивается и ищется по коду, английскому и native имени.",
      searchLanguagePlaceholder: "Поиск языка: zh, Chinese, 中文",
      selectedLanguage: "Выбранный язык",
      noLanguageSelected: "Выбери язык из каталога справа от поиска.",
      noCatalogResults: "По запросу ничего не найдено.",
      code: "Код",
      name: "Название",
      type: "Тип",
      status: "Статус",
      actions: "Действия",
      system: "Системный",
      custom: "Пользовательский",
      enabled: "Включен",
      disabled: "Выключен",
      disable: "Выключить",
      enable: "Включить",
      delete: "Удалить",
      localUsersNoAd: "Локальные пользователи (без синхронизации с AD)",
      localUsersHelp: "Для сервисных и исключительных сценариев. Поля AD не синхронизируются.",
      loginPlaceholder: "Логин (local.registrar)",
      passwordPlaceholder: "Пароль",
      displayNamePlaceholder: "Отображаемое имя",
      rolesPlaceholder: "Роли: registrar,auditor",
      addLocalUser: "Добавить локального пользователя",
      refreshList: "Обновить список",
      noLocalUsers: "Пока нет локальных пользователей.",
      user: "Пользователь",
      userId: "User ID",
      roles: "Роли",
      source: "Источник",
      adSync: "ad_sync",
      on: "вкл",
      off: "выкл",
      directoryIdentity: "Directory и идентификация",
      directoryHelp: "Проверки LDAP/AD и тесты подключений.",
      planned: "Планируется",
      aiProviders: "AI-провайдеры",
      aiHelp: "Ключи провайдеров, policy маршрутизации и контроль квот.",
      configured: "Сконфигурирован",
      notConfigured: "Не настроен",
      enabledFlag: "Флаг enabled",
      yes: "Да",
      no: "Нет",
      testConnection: "Проверить соединение",
      testUserBind: "Проверить bind пользователя",
      saveSettings: "Сохранить настройки",
      ldapConfigTitle: "LDAP/AD конфигурация",
      ldapEnabled: "Включить LDAP",
      ldapServerUri: "LDAP server URI",
      ldapBindDn: "Bind DN",
      ldapBindPassword: "Bind password",
      ldapBaseDn: "Base DN",
      ldapUserFilter: "User filter",
      ldapDisplayAttr: "Display name attribute",
      ldapLoginAttr: "Login attribute",
      ldapGroupAttr: "Group attribute",
      ldapRoleMapJson: "Group->Role map JSON",
      ldapDefaultRole: "Default role",
      ldapTimeout: "Timeout (seconds)",
      providerApiKey: "API key",
      ldapLoginPlaceholder: "LDAP login",
      ldapPasswordPlaceholder: "LDAP password",
      validationEndpoint: "Endpoint проверки",
      validateProvider: "Проверить провайдера",
      providerSaved: "Настройки провайдера сохранены",
      ldapSaved: "LDAP настройки сохранены",
      validationOk: "Проверка успешна",
      serviceBindOk: "Service bind успешен",
      noProviders: "Пока нет провайдеров для отображения.",
      featureFlagsLoading: "Загрузка...",
      featureFlagUpdating: "Обновление...",
      featureFlagSearch: "Поиск по ключу или описанию",
      featureFlagsEnabledOnly: "Показать только включенные",
      featureFlagsShowing: "Показано флагов: {count}",
      featureFlagsShowingFiltered: "Показано отфильтрованных флагов: {count}",
      featureFlagsNoFiltersActive: "Фильтры не активны",
      featureFlagFilterSearch: "Поиск",
      featureFlagFilterEnabledOnly: "Только включенные",
      featureFlagEnableConfirm: "Включить feature flag {flag}?",
      featureFlagDisableConfirm: "Выключить feature flag {flag}?",
      featureFlagUpdateCancelled: "Изменение feature flag отменено",
      featureFlagUpdated: "Feature flag {flag} переключен: {status}",
      featureFlagLastChanged: "Последнее изменение",
      auditVisibility: "Видимость аудита",
      auditHelp: "Отслеживай actor, action, entity и correlation ID для критичных изменений.",
      export: "Экспорт CSV/JSON",
      filter: "Фильтр по пользователю/действию/дате",
      investigate: "Расследование по correlation ID",
      securityPosture: "Состояние безопасности",
      securityHelp: "Админ-действия должны быть аудируемыми и защищенными правами.",
      auditRequired: "Audit обязателен",
      backupPlan: "План бэкапов",
      backupHelp: "Используйте профили хранилищ. Путь должен быть внутри разрешенных root-директорий.",
      activeBackupProfile: "Активный профиль",
      profileId: "ID профиля",
      profileLabel: "Название профиля",
      profilePath: "Путь хранения",
      allowedRoots: "Разрешенные root-пути",
      addProfile: "Добавить профиль",
      removeProfile: "Удалить профиль",
      saveBackupSettings: "Сохранить профили",
      runBackupNow: "Запустить backup сейчас",
      backupHistory: "История backup",
      backupHistorySummaryAvailable: "Бэкапов доступно: {count}",
      backupHistorySummaryLatest: "Последний backup: {value}",
      backupHistorySummaryStatus: "Последний статус: {value}",
      backupReload: "Обновить backup данные",
      backupLoading: "Загрузка...",
      backupRunning: "Запуск...",
      backupRestoring: "Восстановление...",
      backupApplying: "Применение...",
      backupRunConfirm: "Запустить backup сейчас?",
      backupRunCancelled: "Запуск backup отменен",
      backupRestoreConfirmByFile: "Восстановить backup {file}?",
      backupRetentionConfirm: "Применить политику retention?",
      backupRestoreAvailable: "Доступно для restore",
      backupRestoreNotAvailable: "Нет в restore списке",
      backupCreatedAt: "Создан",
      backupProfile: "Профиль",
      backupStatusUnknown: "unknown",
      backupStatusRunning: "running",
      backupStatusFailed: "failed",
      backupStatusSuccess: "success",
      backupSelectForRestore: "Выбрать",
      restoreCandidatesList: "Файлы для восстановления",
      restoreModifiedAt: "Изменен",
      backupSaved: "Профили backup сохранены",
      backupCompleted: "Backup выполнен",
      noBackupJobs: "Пока нет backup задач.",
      backupFile: "Файл",
      backupSize: "Размер",
      finishedAt: "Завершено",
      addLanguage: "Добавить язык",
      languageAdded: "Язык добавлен.",
      languageEnabledMsg: "Язык {code} включен.",
      languageDisabledMsg: "Язык {code} выключен.",
      languageDeletedMsg: "Язык {code} удален.",
      languageRequired: "Выбери язык из каталога.",
      localUserRequired: "Для локального пользователя заполни login, password и display name.",
      localUserCreated: "Локальный пользователь создан (без AD sync).",
      restoreConfirmPrompt: "Восстановление перезапишет состояние базы данных. Продолжить?",
      restoreCancelled: "Восстановление отменено",
      retentionConfirmPrompt: "Применение политики удалит старые файлы бэкапов безвозвратно. Продолжить?",
      retentionCancelled: "Применение политики отменено",
      auditAction: "Action",
      auditActionFilter: "Filter by action",
      auditActor: "Actor",
      auditActorFilter: "Filter by actor",
      auditCorrelation: "Correlation ID",
      auditEntity: "Entity",
      auditPath: "Path",
      auditResult: "Result",
      auditSinceFilter: "Since (ISO, e.g. 2026-03-15T00:00:00Z)",
      auditTs: "Timestamp",
      auditClearFilters: "Очистить фильтры",
      auditNoFiltersActive: "Активных фильтров нет",
      auditShowingEvents: "Показано событий: {count}",
      auditShowingFilteredEvents: "Показано отфильтрованных событий: {count}",
      auditLastEvent: "Последнее событие",
      auditLoading: "Загрузка...",
      auditExportingCsv: "Экспорт CSV...",
      auditExportingJson: "Экспорт JSON...",
      authManagedByBackend: "Identity and roles are resolved by backend auth.",
      backupJobType: "Type",
      exportCsv: "Export CSV",
      exportJson: "Export JSON",
      keepSecretHint: "Оставьте пустым, чтобы сохранить существующий секрет",
      loadAuditEvents: "Load events",
      localApplyFilters: "Apply filters",
      localDelete: "Delete user",
      localEditDisplayName: "Display name",
      localEditRoles: "Roles: registrar,auditor",
      localLanguageAll: "All languages",
      localPasswordAction: "Set password",
      localPasswordRequired: "Password is required.",
      localPasswordUpdated: "Password updated",
      localRoleFilter: "Filter by role",
      localSearch: "Search by login, user id, display name",
      localSetPassword: "New password",
      localUpdate: "Update user",
      localUserDeleted: "Local user deleted",
      localUserOps: "Local user operations",
      localUserSelectRequired: "Select a local user first.",
      localUserUpdated: "Local user updated",
      noAuditEvents: "No audit events found.",
      noRestoreCandidates: "No .dump files found",
      overviewAi: "Configured AI providers",
      overviewApi: "API health",
      overviewAssignments: "Assignments",
      overviewBackend: "Backend health",
      overviewLive: "Live operational snapshot",
      overviewNoData: "No snapshot loaded yet.",
      overviewRefresh: "Refresh snapshot",
      overviewRoles: "Roles",
      overviewUsers: "Local users",
      rbac: "RBAC",
      rbacAssign: "Assign role",
      rbacAssignHelp: "Assign a role to a specific user ID.",
      rbacAssignRequired: "User ID and role are required.",
      rbacAssignTitle: "Assign role",
      rbacAssigned: "Role assigned",
      rbacFilterRole: "Filter by role",
      rbacFilterUser: "Filter by user ID",
      rbacNoAssignments: "No assignments found.",
      rbacNoRoles: "No roles found.",
      rbacPermissions: "Permissions: admin.dashboard.read,admin.audit.read",
      rbacPerms: "Permissions",
      rbacRefresh: "Refresh",
      rbacRefreshAssignments: "Refresh assignments",
      rbacRevoke: "Revoke",
      rbacRevoked: "Role revoked",
      rbacRole: "Role",
      rbacRoleName: "Role name",
      rbacRoleRequired: "Role name is required.",
      rbacRoleSaved: "Role saved",
      rbacRolesHelp: "Create or update role with comma-separated permissions.",
      rbacRolesTitle: "Roles and permissions",
      rbacSaveRole: "Save role",
      rbacUserId: "User ID",
      refreshRestoreFiles: "Refresh files",
      restoreCompleted: "Restore completed",
      restoreDryRun: "Restore dry-run",
      restoreDryRunOk: "Restore dry-run prepared",
      restoreFileRequired: "Select backup file for restore.",
      restoreHelp: "Choose backup file and run dry-run before real restore.",
      restoreNow: "Restore now",
      restoreProfileRequired: "Select restore profile.",
      restoreTitle: "Restore",
      retentionApplied: "Retention applied: {count} file(s) deleted",
      retentionApply: "Apply retention",
      retentionDays: "Retention days",
      retentionDryRun: "Retention dry-run",
      retentionDryRunDone: "Retention dry-run: {count} file(s) can be deleted",
      retentionHelp: "Keep recent backups and delete old dump files by policy.",
      retentionMinFiles: "Minimum files to keep",
      retentionTitle: "Retention policy",
      errorPrefix: "Ошибка",
    },
    en: {
      controlCenter: "University Platform Control Center",
      lastChange: "Last change",
      adminUser: "Admin user",
      enabledLanguages: "Enabled languages",
      total: "Total",
      systemLanguages: "System languages",
      protectedCore: "Protected core",
      localUsers: "Local users",
      nonAdAccounts: "Non-AD accounts",
      adminMode: "Admin mode",
      adminActive: "Active",
      rbacEnforced: "RBAC enforced",
      overview: "Overview",
      languages: "Languages",
      integrations: "Integrations",
      backups: "Backups",
      audit: "Audit",
      platformModules: "Platform Modules",
      operationalFocus: "Operational Focus",
      usersRoles: "Users and Roles",
      ldapSettings: "LDAP/AD integration settings",
      aiControls: "AI provider controls",
      auditEvents: "Audit and security events",
      trackChanges: "Track role changes and privileged actions",
      keepI18n: "Keep i18n core (`kk`, `ru`, `en`) healthy",
      controlledExceptions: "Use local users only for controlled exceptions",
      documentActions: "Document every major admin action",
      languageManagement: "Language Management",
      langHelp: "Add languages without breaking the core. System languages are protected.",
      catalogTitle: "Language catalog",
      catalogHelp: "Pick a language from the catalog. The list supports scrolling and search by code, English name, and native name.",
      searchLanguagePlaceholder: "Search language: zh, Chinese, 中文",
      selectedLanguage: "Selected language",
      noLanguageSelected: "Choose a language from the catalog list.",
      noCatalogResults: "No languages found for this query.",
      code: "Code",
      name: "Name",
      type: "Type",
      status: "Status",
      actions: "Actions",
      system: "System",
      custom: "Custom",
      enabled: "Enabled",
      disabled: "Disabled",
      disable: "Disable",
      enable: "Enable",
      delete: "Delete",
      localUsersNoAd: "Local Users (No AD Sync)",
      localUsersHelp: "For service or exception flows. AD fields are not synchronized.",
      loginPlaceholder: "Login (local.registrar)",
      passwordPlaceholder: "Password",
      displayNamePlaceholder: "Display name",
      rolesPlaceholder: "Roles: registrar,auditor",
      addLocalUser: "Add local user",
      refreshList: "Refresh list",
      noLocalUsers: "No local users yet.",
      user: "User",
      userId: "User ID",
      roles: "Roles",
      source: "Source",
      adSync: "ad_sync",
      on: "on",
      off: "off",
      directoryIdentity: "Directory and Identity",
      directoryHelp: "LDAP/AD integration checks and connection tests.",
      planned: "Planned",
      aiProviders: "AI Providers",
      aiHelp: "Provider keys, routing policy, and quota controls.",
      configured: "Configured",
      notConfigured: "Not configured",
      enabledFlag: "Enabled flag",
      yes: "Yes",
      no: "No",
      testConnection: "Test connection",
      testUserBind: "Test user bind",
      saveSettings: "Save settings",
      ldapConfigTitle: "LDAP/AD configuration",
      ldapEnabled: "Enable LDAP",
      ldapServerUri: "LDAP server URI",
      ldapBindDn: "Bind DN",
      ldapBindPassword: "Bind password",
      ldapBaseDn: "Base DN",
      ldapUserFilter: "User filter",
      ldapDisplayAttr: "Display name attribute",
      ldapLoginAttr: "Login attribute",
      ldapGroupAttr: "Group attribute",
      ldapRoleMapJson: "Group->Role map JSON",
      ldapDefaultRole: "Default role",
      ldapTimeout: "Timeout (seconds)",
      providerApiKey: "API key",
      ldapLoginPlaceholder: "LDAP login",
      ldapPasswordPlaceholder: "LDAP password",
      validationEndpoint: "Validation endpoint",
      validateProvider: "Validate provider",
      providerSaved: "Provider settings saved",
      ldapSaved: "LDAP settings saved",
      validationOk: "Validation passed",
      serviceBindOk: "Service bind passed",
      noProviders: "No providers to display yet.",
      featureFlagsLoading: "Loading...",
      featureFlagUpdating: "Updating...",
      featureFlagSearch: "Search by key or description",
      featureFlagsEnabledOnly: "Show enabled only",
      featureFlagsShowing: "Showing {count} flags",
      featureFlagsShowingFiltered: "Showing {count} filtered flags",
      featureFlagsNoFiltersActive: "No active filters",
      featureFlagFilterSearch: "Search",
      featureFlagFilterEnabledOnly: "Enabled only",
      featureFlagEnableConfirm: "Enable feature flag {flag}?",
      featureFlagDisableConfirm: "Disable feature flag {flag}?",
      featureFlagUpdateCancelled: "Feature flag update cancelled",
      featureFlagUpdated: "Feature flag {flag} set to {status}",
      featureFlagLastChanged: "Last changed",
      auditVisibility: "Audit Visibility",
      auditHelp: "Track actor, action, entity, and correlation ID for critical changes.",
      export: "Export CSV/JSON",
      filter: "Filter by user/action/date",
      investigate: "Investigate by correlation ID",
      securityPosture: "Security Posture",
      securityHelp: "Admin actions must remain auditable and permission-protected.",
      auditRequired: "Audit required",
      backupPlan: "Backup Plan",
      backupHelp: "Use storage profiles. Profile paths must stay inside allowed root directories.",
      activeBackupProfile: "Active profile",
      profileId: "Profile ID",
      profileLabel: "Profile label",
      profilePath: "Storage path",
      allowedRoots: "Allowed root paths",
      addProfile: "Add profile",
      removeProfile: "Remove profile",
      saveBackupSettings: "Save profiles",
      runBackupNow: "Run backup now",
      backupHistory: "Backup history",
      backupHistorySummaryAvailable: "Backups available: {count}",
      backupHistorySummaryLatest: "Latest backup: {value}",
      backupHistorySummaryStatus: "Latest status: {value}",
      backupReload: "Reload backup data",
      backupLoading: "Loading...",
      backupRunning: "Running...",
      backupRestoring: "Restoring...",
      backupApplying: "Applying...",
      backupRunConfirm: "Run backup now?",
      backupRunCancelled: "Backup run cancelled",
      backupRestoreConfirmByFile: "Restore backup {file}?",
      backupRetentionConfirm: "Apply retention policy?",
      backupRestoreAvailable: "Restore available",
      backupRestoreNotAvailable: "Not in restore list",
      backupCreatedAt: "Created",
      backupProfile: "Profile",
      backupStatusUnknown: "unknown",
      backupStatusRunning: "running",
      backupStatusFailed: "failed",
      backupStatusSuccess: "success",
      backupSelectForRestore: "Select",
      restoreCandidatesList: "Restore files",
      restoreModifiedAt: "Modified",
      backupSaved: "Backup profiles saved",
      backupCompleted: "Backup completed",
      noBackupJobs: "No backup jobs yet.",
      backupFile: "File",
      backupSize: "Size",
      finishedAt: "Finished at",
      addLanguage: "Add language",
      languageAdded: "Language added.",
      languageEnabledMsg: "Language {code} enabled.",
      languageDisabledMsg: "Language {code} disabled.",
      languageDeletedMsg: "Language {code} deleted.",
      languageRequired: "Choose a language from the catalog.",
      localUserRequired: "For local user fill login, password and display name.",
      localUserCreated: "Local user created (without AD sync).",
      restoreConfirmPrompt: "Restore will overwrite database state. Continue?",
      restoreCancelled: "Restore cancelled",
      retentionConfirmPrompt: "Apply retention will permanently delete old backup files. Continue?",
      retentionCancelled: "Retention cancelled",
      auditAction: "Action",
      auditActionFilter: "Filter by action",
      auditActor: "Actor",
      auditActorFilter: "Filter by actor",
      auditCorrelation: "Correlation ID",
      auditEntity: "Entity",
      auditPath: "Path",
      auditResult: "Result",
      auditSinceFilter: "Since (ISO, e.g. 2026-03-15T00:00:00Z)",
      auditTs: "Timestamp",
      auditClearFilters: "Clear filters",
      auditNoFiltersActive: "No active filters",
      auditShowingEvents: "Showing {count} events",
      auditShowingFilteredEvents: "Showing {count} filtered events",
      auditLastEvent: "Last event",
      auditLoading: "Loading...",
      auditExportingCsv: "Exporting CSV...",
      auditExportingJson: "Exporting JSON...",
      authManagedByBackend: "Identity and roles are resolved by backend auth.",
      backupJobType: "Type",
      exportCsv: "Export CSV",
      exportJson: "Export JSON",
      keepSecretHint: "Leave blank to keep existing secret",
      loadAuditEvents: "Load events",
      localApplyFilters: "Apply filters",
      localDelete: "Delete user",
      localEditDisplayName: "Display name",
      localEditRoles: "Roles: registrar,auditor",
      localLanguageAll: "All languages",
      localPasswordAction: "Set password",
      localPasswordRequired: "Password is required.",
      localPasswordUpdated: "Password updated",
      localRoleFilter: "Filter by role",
      localSearch: "Search by login, user id, display name",
      localSetPassword: "New password",
      localUpdate: "Update user",
      localUserDeleted: "Local user deleted",
      localUserOps: "Local user operations",
      localUserSelectRequired: "Select a local user first.",
      localUserUpdated: "Local user updated",
      noAuditEvents: "No audit events found.",
      noRestoreCandidates: "No .dump files found",
      overviewAi: "Configured AI providers",
      overviewApi: "API health",
      overviewAssignments: "Assignments",
      overviewBackend: "Backend health",
      overviewLive: "Live operational snapshot",
      overviewNoData: "No snapshot loaded yet.",
      overviewRefresh: "Refresh snapshot",
      overviewRoles: "Roles",
      overviewUsers: "Local users",
      rbac: "RBAC",
      rbacAssign: "Assign role",
      rbacAssignHelp: "Assign a role to a specific user ID.",
      rbacAssignRequired: "User ID and role are required.",
      rbacAssignTitle: "Assign role",
      rbacAssigned: "Role assigned",
      rbacFilterRole: "Filter by role",
      rbacFilterUser: "Filter by user ID",
      rbacNoAssignments: "No assignments found.",
      rbacNoRoles: "No roles found.",
      rbacPermissions: "Permissions: admin.dashboard.read,admin.audit.read",
      rbacPerms: "Permissions",
      rbacRefresh: "Refresh",
      rbacRefreshAssignments: "Refresh assignments",
      rbacRevoke: "Revoke",
      rbacRevoked: "Role revoked",
      rbacRole: "Role",
      rbacRoleName: "Role name",
      rbacRoleRequired: "Role name is required.",
      rbacRoleSaved: "Role saved",
      rbacRolesHelp: "Create or update role with comma-separated permissions.",
      rbacRolesTitle: "Roles and permissions",
      rbacSaveRole: "Save role",
      rbacUserId: "User ID",
      refreshRestoreFiles: "Refresh files",
      restoreCompleted: "Restore completed",
      restoreDryRun: "Restore dry-run",
      restoreDryRunOk: "Restore dry-run prepared",
      restoreFileRequired: "Select backup file for restore.",
      restoreHelp: "Choose backup file and run dry-run before real restore.",
      restoreNow: "Restore now",
      restoreProfileRequired: "Select restore profile.",
      restoreTitle: "Restore",
      retentionApplied: "Retention applied: {count} file(s) deleted",
      retentionApply: "Apply retention",
      retentionDays: "Retention days",
      retentionDryRun: "Retention dry-run",
      retentionDryRunDone: "Retention dry-run: {count} file(s) can be deleted",
      retentionHelp: "Keep recent backups and delete old dump files by policy.",
      retentionMinFiles: "Minimum files to keep",
      retentionTitle: "Retention policy",
      errorPrefix: "Error",
    },
    kk: {
      controlCenter: "Университет платформасын басқару орталығы",
      lastChange: "Соңғы өзгеріс",
      adminUser: "Әкімші",
      enabledLanguages: "Қосылған тілдер",
      total: "Жалпы",
      systemLanguages: "Жүйелік тілдер",
      protectedCore: "Қорғалған өзек",
      localUsers: "Жергілікті қолданушылар",
      nonAdAccounts: "AD-сыз аккаунттар",
      adminMode: "Әкімші режимі",
      adminActive: "Белсенді",
      rbacEnforced: "RBAC қосулы",
      overview: "Шолу",
      languages: "Тілдер",
      integrations: "Интеграциялар",
      backups: "Backup",
      audit: "Аудит",
      platformModules: "Платформа модульдері",
      operationalFocus: "Операциялық фокус",
      usersRoles: "Қолданушылар мен рөлдер",
      ldapSettings: "LDAP/AD баптаулары",
      aiControls: "AI провайдер бақылауы",
      auditEvents: "Аудит және қауіпсіздік оқиғалары",
      trackChanges: "Рөл өзгерістерін және артықшылықты әрекеттерді қадағала",
      keepI18n: "i18n өзегін (`kk`, `ru`, `en`) тұрақты ұста",
      controlledExceptions: "local users тек бақыланатын ерекше жағдай үшін",
      documentActions: "Әр маңызды әкімші әрекетін құжатта",
      languageManagement: "Тілдерді басқару",
      langHelp: "Өзекті бұзбай жаңа тілдерді қос.",
      catalogTitle: "Тілдер каталогы",
      catalogHelp: "Каталогтан тілді таңда. Тізім код, ағылшынша атау және native name бойынша ізделеді.",
      searchLanguagePlaceholder: "Тілді іздеу: zh, Chinese, 中文",
      selectedLanguage: "Таңдалған тіл",
      noLanguageSelected: "Каталог тізімінен тілді таңда.",
      noCatalogResults: "Сұрауыңыз бойынша тіл табылмады.",
      code: "Код",
      name: "Атауы",
      type: "Түр",
      status: "Күй",
      actions: "Эрекеттер",
      system: "Жүйелік",
      custom: "Қосымша",
      enabled: "Қосулы",
      disabled: "Өшік",
      disable: "Өшіру",
      enable: "Қосу",
      delete: "Жою",
      localUsersNoAd: "Жергілікті қолданушылар (AD sync жоқ)",
      localUsersHelp: "Сервистік не ерекше сценарийлер үшін.",
      loginPlaceholder: "Логин (local.registrar)",
      passwordPlaceholder: "Құпия сөз",
      displayNamePlaceholder: "Көрсетілетін аты",
      rolesPlaceholder: "Рөлдер: registrar,auditor",
      addLocalUser: "Жергілікті қолданушы қосу",
      refreshList: "Тізімді жаңарту",
      noLocalUsers: "Әзірше жергілікті қолданушы жоқ.",
      user: "Қолданушы",
      userId: "User ID",
      roles: "Рөлдер",
      source: "Дереккөз",
      adSync: "ad_sync",
      on: "қосулы",
      off: "өшік",
      directoryIdentity: "Directory және идентификация",
      directoryHelp: "LDAP/AD тексеру және байланыс тесттері.",
      planned: "Жоспарда",
      aiProviders: "AI провайдерлер",
      aiHelp: "Кілттер, маршрут саясаты және квота бақылауы.",
      configured: "Бапталған",
      notConfigured: "Бапталмаған",
      enabledFlag: "Enabled жалауы",
      yes: "Иә",
      no: "Жоқ",
      testConnection: "Байланысты тексеру",
      testUserBind: "Пайдаланушы bind тексеру",
      saveSettings: "Баптауларды сақтау",
      ldapConfigTitle: "LDAP/AD баптауы",
      ldapEnabled: "LDAP қосу",
      ldapServerUri: "LDAP server URI",
      ldapBindDn: "Bind DN",
      ldapBindPassword: "Bind password",
      ldapBaseDn: "Base DN",
      ldapUserFilter: "User filter",
      ldapDisplayAttr: "Display name attribute",
      ldapLoginAttr: "Login attribute",
      ldapGroupAttr: "Group attribute",
      ldapRoleMapJson: "Group->Role map JSON",
      ldapDefaultRole: "Default role",
      ldapTimeout: "Timeout (секунд)",
      providerApiKey: "API кілті",
      ldapLoginPlaceholder: "LDAP логин",
      ldapPasswordPlaceholder: "LDAP құпия сөзі",
      validationEndpoint: "Тексеру endpoint",
      validateProvider: "Провайдерді тексеру",
      providerSaved: "Провайдер баптаулары сақталды",
      ldapSaved: "LDAP баптаулары сақталды",
      validationOk: "Тексеру сәтті өтті",
      serviceBindOk: "Service bind сәтті өтті",
      noProviders: "Көрсетілетін провайдер жоқ.",
      featureFlagsLoading: "Жүктелуде...",
      featureFlagUpdating: "Жаңартылуда...",
      featureFlagSearch: "Кілт немесе сипаттама бойынша іздеу",
      featureFlagsEnabledOnly: "Тек қосылғандарын көрсету",
      featureFlagsShowing: "Көрсетілген флагтар: {count}",
      featureFlagsShowingFiltered: "Көрсетілген сүзілген флагтар: {count}",
      featureFlagsNoFiltersActive: "Белсенді фильтр жоқ",
      featureFlagFilterSearch: "Іздеу",
      featureFlagFilterEnabledOnly: "Тек қосылған",
      featureFlagEnableConfirm: "{flag} feature flag-ін қосу керек пе?",
      featureFlagDisableConfirm: "{flag} feature flag-ін өшіру керек пе?",
      featureFlagUpdateCancelled: "Feature flag өзгерісі тоқтатылды",
      featureFlagUpdated: "Feature flag {flag} күйі: {status}",
      featureFlagLastChanged: "Соңғы өзгеріс",
      auditVisibility: "Аудит көрінісі",
      auditHelp: "Маңызды өзгерістер үшін actor/action/entity/correlation ID қара.",
      export: "CSV/JSON экспорт",
      filter: "Пайдаланушы/әрекет/күн бойынша сүзгі",
      investigate: "correlation ID бойынша талдау",
      securityPosture: "Қауіпсіздік жағдайы",
      securityHelp: "Әкімші әрекеттері аудиттеліп, құқықпен қорғалуы керек.",
      auditRequired: "Audit міндетті",
      backupPlan: "Backup жоспары",
      backupHelp: "Сақтау профильдерін қолданыңыз. Жол рұқсат етілген root ішінде болуы керек.",
      activeBackupProfile: "Белсенді профиль",
      profileId: "Профиль ID",
      profileLabel: "Профиль атауы",
      profilePath: "Сақтау жолы",
      allowedRoots: "Рұқсат етілген root жолдар",
      addProfile: "Профиль қосу",
      removeProfile: "Профиль өшіру",
      saveBackupSettings: "Профильдерді сақтау",
      runBackupNow: "Backup іске қосу",
      backupHistory: "Backup тарихы",
      backupHistorySummaryAvailable: "Қолжетімді backup: {count}",
      backupHistorySummaryLatest: "Соңғы backup: {value}",
      backupHistorySummaryStatus: "Соңғы күй: {value}",
      backupReload: "Backup деректерін жаңарту",
      backupLoading: "Жүктелуде...",
      backupRunning: "Іске қосылуда...",
      backupRestoring: "Қалпына келтірілуде...",
      backupApplying: "Қолданылуда...",
      backupRunConfirm: "Backup қазір іске қосылсын ба?",
      backupRunCancelled: "Backup іске қосу тоқтатылды",
      backupRestoreConfirmByFile: "{file} backup-ын қалпына келтіру керек пе?",
      backupRetentionConfirm: "Retention саясатын қолдану керек пе?",
      backupRestoreAvailable: "Restore үшін қолжетімді",
      backupRestoreNotAvailable: "Restore тізімінде жоқ",
      backupCreatedAt: "Құрылған",
      backupProfile: "Профиль",
      backupStatusUnknown: "unknown",
      backupStatusRunning: "running",
      backupStatusFailed: "failed",
      backupStatusSuccess: "success",
      backupSelectForRestore: "Таңдау",
      restoreCandidatesList: "Қалпына келтіру файлдары",
      restoreModifiedAt: "Өзгертілген",
      backupSaved: "Backup профильдері сақталды",
      backupCompleted: "Backup орындалды",
      noBackupJobs: "Әзірше backup тапсырмасы жоқ.",
      backupFile: "Файл",
      backupSize: "Көлем",
      finishedAt: "Аяқталды",
      addLanguage: "Тілді қосу",
      languageAdded: "Тіл қосылды.",
      languageEnabledMsg: "{code} тілі қосылды.",
      languageDisabledMsg: "{code} тілі өшірілді.",
      languageDeletedMsg: "{code} тілі жойылды.",
      languageRequired: "Каталогтан тілді таңда.",
      localUserRequired: "login, password және display name толтыр.",
      localUserCreated: "Жергілікті қолданушы қосылды (AD sync жоқ).",
      restoreConfirmPrompt: "Қалпына келтіру дерекқор күйін қайта жазады. Жалғастыру?",
      restoreCancelled: "Қалпына келтіру тоқтатылды",
      retentionConfirmPrompt: "Саясатты қолдану ескі бэкап файлдарын жояды. Жалғастыру?",
      retentionCancelled: "Саясатты қолдану тоқтатылды",
      auditAction: "Action",
      auditActionFilter: "Filter by action",
      auditActor: "Actor",
      auditActorFilter: "Filter by actor",
      auditCorrelation: "Correlation ID",
      auditEntity: "Entity",
      auditPath: "Path",
      auditResult: "Result",
      auditSinceFilter: "Since (ISO, e.g. 2026-03-15T00:00:00Z)",
      auditTs: "Timestamp",
      auditClearFilters: "Фильтрлерді тазалау",
      auditNoFiltersActive: "Белсенді фильтр жоқ",
      auditShowingEvents: "Көрсетілген оқиғалар: {count}",
      auditShowingFilteredEvents: "Көрсетілген сүзілген оқиғалар: {count}",
      auditLastEvent: "Соңғы оқиға",
      auditLoading: "Жүктелуде...",
      auditExportingCsv: "CSV экспорт...",
      auditExportingJson: "JSON экспорт...",
      authManagedByBackend: "Identity and roles are resolved by backend auth.",
      backupJobType: "Type",
      exportCsv: "Export CSV",
      exportJson: "Export JSON",
      keepSecretHint: "Бар құпияны сақтау үшін бос қалдырыңыз",
      loadAuditEvents: "Load events",
      localApplyFilters: "Apply filters",
      localDelete: "Delete user",
      localEditDisplayName: "Display name",
      localEditRoles: "Roles: registrar,auditor",
      localLanguageAll: "All languages",
      localPasswordAction: "Set password",
      localPasswordRequired: "Password is required.",
      localPasswordUpdated: "Password updated",
      localRoleFilter: "Filter by role",
      localSearch: "Search by login, user id, display name",
      localSetPassword: "New password",
      localUpdate: "Update user",
      localUserDeleted: "Local user deleted",
      localUserOps: "Local user operations",
      localUserSelectRequired: "Select a local user first.",
      localUserUpdated: "Local user updated",
      noAuditEvents: "No audit events found.",
      noRestoreCandidates: "No .dump files found",
      overviewAi: "Configured AI providers",
      overviewApi: "API health",
      overviewAssignments: "Assignments",
      overviewBackend: "Backend health",
      overviewLive: "Live operational snapshot",
      overviewNoData: "No snapshot loaded yet.",
      overviewRefresh: "Refresh snapshot",
      overviewRoles: "Roles",
      overviewUsers: "Local users",
      rbac: "RBAC",
      rbacAssign: "Assign role",
      rbacAssignHelp: "Assign a role to a specific user ID.",
      rbacAssignRequired: "User ID and role are required.",
      rbacAssignTitle: "Assign role",
      rbacAssigned: "Role assigned",
      rbacFilterRole: "Filter by role",
      rbacFilterUser: "Filter by user ID",
      rbacNoAssignments: "No assignments found.",
      rbacNoRoles: "No roles found.",
      rbacPermissions: "Permissions: admin.dashboard.read,admin.audit.read",
      rbacPerms: "Permissions",
      rbacRefresh: "Refresh",
      rbacRefreshAssignments: "Refresh assignments",
      rbacRevoke: "Revoke",
      rbacRevoked: "Role revoked",
      rbacRole: "Role",
      rbacRoleName: "Role name",
      rbacRoleRequired: "Role name is required.",
      rbacRoleSaved: "Role saved",
      rbacRolesHelp: "Create or update role with comma-separated permissions.",
      rbacRolesTitle: "Roles and permissions",
      rbacSaveRole: "Save role",
      rbacUserId: "User ID",
      refreshRestoreFiles: "Refresh files",
      restoreCompleted: "Restore completed",
      restoreDryRun: "Restore dry-run",
      restoreDryRunOk: "Restore dry-run prepared",
      restoreFileRequired: "Select backup file for restore.",
      restoreHelp: "Choose backup file and run dry-run before real restore.",
      restoreNow: "Restore now",
      restoreProfileRequired: "Select restore profile.",
      restoreTitle: "Restore",
      retentionApplied: "Retention applied: {count} file(s) deleted",
      retentionApply: "Apply retention",
      retentionDays: "Retention days",
      retentionDryRun: "Retention dry-run",
      retentionDryRunDone: "Retention dry-run: {count} file(s) can be deleted",
      retentionHelp: "Keep recent backups and delete old dump files by policy.",
      retentionMinFiles: "Minimum files to keep",
      retentionTitle: "Retention policy",
      errorPrefix: "Қате",
    },
    zh: {
      controlCenter: "平台控制中心",
      lastChange: "最后更新",
      adminUser: "管理员",
      enabledLanguages: "已启用语言",
      total: "总数",
      systemLanguages: "系统语言",
      protectedCore: "受保护核心",
      localUsers: "本地用户",
      nonAdAccounts: "非 AD 账户",
      adminMode: "管理模式",
      adminActive: "已启用",
      rbacEnforced: "RBAC 已启用",
      overview: "概览",
      languages: "语言",
      integrations: "集成",
      backups: "备份",
      audit: "审计",
      platformModules: "平台模块",
      operationalFocus: "运维重点",
      usersRoles: "用户与角色",
      ldapSettings: "LDAP/AD 设置",
      aiControls: "AI 提供商控制",
      auditEvents: "审计与安全事件",
      trackChanges: "跟踪角色变更和特权操作",
      keepI18n: "保持 i18n 核心（`kk`, `ru`, `en`, `zh`）可用",
      controlledExceptions: "本地用户仅用于受控例外场景",
      documentActions: "记录每个重要管理员操作",
      languageManagement: "语言管理",
      langHelp: "在不破坏核心的情况下添加新语言。系统语言受保护。",
      catalogTitle: "语言目录",
      catalogHelp: "从目录中选择语言。列表支持滚动，并可按代码、英文名和本地名搜索。",
      searchLanguagePlaceholder: "搜索语言：zh, Chinese, 中文",
      selectedLanguage: "已选语言",
      noLanguageSelected: "请从目录列表中选择语言。",
      noCatalogResults: "没有找到匹配的语言。",
      code: "代码",
      name: "名称",
      type: "类型",
      status: "状态",
      actions: "操作",
      system: "系统",
      custom: "自定义",
      enabled: "启用",
      disabled: "停用",
      disable: "停用",
      enable: "启用",
      delete: "删除",
      localUsersNoAd: "本地用户（不与 AD 同步）",
      localUsersHelp: "用于服务账户或特殊场景。AD 字段不会同步。",
      loginPlaceholder: "登录名（local.registrar）",
      passwordPlaceholder: "密码",
      displayNamePlaceholder: "显示名称",
      rolesPlaceholder: "角色：registrar,auditor",
      addLocalUser: "添加本地用户",
      refreshList: "刷新列表",
      noLocalUsers: "暂无本地用户。",
      user: "用户",
      userId: "用户 ID",
      roles: "角色",
      source: "来源",
      adSync: "ad_sync",
      on: "开",
      off: "关",
      directoryIdentity: "目录与身份",
      directoryHelp: "LDAP/AD 集成检查与连接测试。",
      planned: "计划中",
      aiProviders: "AI 提供商",
      aiHelp: "提供商密钥、路由策略和配额控制。",
      configured: "已配置",
      notConfigured: "未配置",
      enabledFlag: "启用标志",
      yes: "是",
      no: "否",
      testConnection: "测试连接",
      testUserBind: "测试用户绑定",
      saveSettings: "保存设置",
      ldapConfigTitle: "LDAP/AD 配置",
      ldapEnabled: "启用 LDAP",
      ldapServerUri: "LDAP server URI",
      ldapBindDn: "Bind DN",
      ldapBindPassword: "Bind password",
      ldapBaseDn: "Base DN",
      ldapUserFilter: "User filter",
      ldapDisplayAttr: "Display name attribute",
      ldapLoginAttr: "Login attribute",
      ldapGroupAttr: "Group attribute",
      ldapRoleMapJson: "Group->Role map JSON",
      ldapDefaultRole: "Default role",
      ldapTimeout: "Timeout（秒）",
      providerApiKey: "API 密钥",
      ldapLoginPlaceholder: "LDAP 登录名",
      ldapPasswordPlaceholder: "LDAP 密码",
      validationEndpoint: "验证端点",
      validateProvider: "验证提供商",
      providerSaved: "提供商设置已保存",
      ldapSaved: "LDAP 设置已保存",
      validationOk: "验证成功",
      serviceBindOk: "服务账号绑定成功",
      noProviders: "暂无可显示的提供商。",
      auditVisibility: "审计可见性",
      auditHelp: "为关键变更跟踪 actor、action、entity 和 correlation ID。",
      export: "导出 CSV/JSON",
      filter: "按用户/操作/日期筛选",
      investigate: "按 correlation ID 调查",
      securityPosture: "安全态势",
      securityHelp: "管理员操作必须可审计且受权限保护。",
      auditRequired: "必须审计",
      backupPlan: "备份计划",
      backupHelp: "请使用存储配置档。路径必须位于允许的根目录内。",
      activeBackupProfile: "当前配置档",
      profileId: "配置档 ID",
      profileLabel: "配置档名称",
      profilePath: "存储路径",
      allowedRoots: "允许的根路径",
      addProfile: "新增配置档",
      removeProfile: "删除配置档",
      saveBackupSettings: "保存配置档",
      runBackupNow: "立即执行备份",
      backupHistory: "备份历史",
      backupSaved: "备份配置档已保存",
      backupCompleted: "备份已完成",
      noBackupJobs: "暂无备份任务。",
      backupFile: "文件",
      backupSize: "大小",
      finishedAt: "完成时间",
      addLanguage: "添加语言",
      languageAdded: "语言已添加。",
      languageEnabledMsg: "语言 {code} 已启用。",
      languageDisabledMsg: "语言 {code} 已停用。",
      languageDeletedMsg: "语言 {code} 已删除。",
      languageRequired: "请先从目录中选择语言。",
      localUserRequired: "本地用户必须填写 login、password 和 display name。",
      localUserCreated: "本地用户已创建（无 AD sync）。",
      restoreConfirmPrompt: "恢复将覆盖当前数据库状态。是否继续?",
      restoreCancelled: "恢复已取消",
      retentionConfirmPrompt: "应用保留策略将永久删除旧备份文件。是否继续?",
      retentionCancelled: "保留策略已取消",
      auditAction: "Action",
      auditActionFilter: "Filter by action",
      auditActor: "Actor",
      auditActorFilter: "Filter by actor",
      auditCorrelation: "Correlation ID",
      auditEntity: "Entity",
      auditPath: "Path",
      auditResult: "Result",
      auditSinceFilter: "Since (ISO, e.g. 2026-03-15T00:00:00Z)",
      auditTs: "Timestamp",
      authManagedByBackend: "Identity and roles are resolved by backend auth.",
      backupJobType: "Type",
      exportCsv: "Export CSV",
      exportJson: "Export JSON",
      keepSecretHint: "留空以保留现有密钥",
      loadAuditEvents: "Load events",
      localApplyFilters: "Apply filters",
      localDelete: "Delete user",
      localEditDisplayName: "Display name",
      localEditRoles: "Roles: registrar,auditor",
      localLanguageAll: "All languages",
      localPasswordAction: "Set password",
      localPasswordRequired: "Password is required.",
      localPasswordUpdated: "Password updated",
      localRoleFilter: "Filter by role",
      localSearch: "Search by login, user id, display name",
      localSetPassword: "New password",
      localUpdate: "Update user",
      localUserDeleted: "Local user deleted",
      localUserOps: "Local user operations",
      localUserSelectRequired: "Select a local user first.",
      localUserUpdated: "Local user updated",
      noAuditEvents: "No audit events found.",
      noRestoreCandidates: "No .dump files found",
      overviewAi: "Configured AI providers",
      overviewApi: "API health",
      overviewAssignments: "Assignments",
      overviewBackend: "Backend health",
      overviewLive: "Live operational snapshot",
      overviewNoData: "No snapshot loaded yet.",
      overviewRefresh: "Refresh snapshot",
      overviewRoles: "Roles",
      overviewUsers: "Local users",
      rbac: "RBAC",
      rbacAssign: "Assign role",
      rbacAssignHelp: "Assign a role to a specific user ID.",
      rbacAssignRequired: "User ID and role are required.",
      rbacAssignTitle: "Assign role",
      rbacAssigned: "Role assigned",
      rbacFilterRole: "Filter by role",
      rbacFilterUser: "Filter by user ID",
      rbacNoAssignments: "No assignments found.",
      rbacNoRoles: "No roles found.",
      rbacPermissions: "Permissions: admin.dashboard.read,admin.audit.read",
      rbacPerms: "Permissions",
      rbacRefresh: "Refresh",
      rbacRefreshAssignments: "Refresh assignments",
      rbacRevoke: "Revoke",
      rbacRevoked: "Role revoked",
      rbacRole: "Role",
      rbacRoleName: "Role name",
      rbacRoleRequired: "Role name is required.",
      rbacRoleSaved: "Role saved",
      rbacRolesHelp: "Create or update role with comma-separated permissions.",
      rbacRolesTitle: "Roles and permissions",
      rbacSaveRole: "Save role",
      rbacUserId: "User ID",
      refreshRestoreFiles: "Refresh files",
      restoreCompleted: "Restore completed",
      restoreDryRun: "Restore dry-run",
      restoreDryRunOk: "Restore dry-run prepared",
      restoreFileRequired: "Select backup file for restore.",
      restoreHelp: "Choose backup file and run dry-run before real restore.",
      restoreNow: "Restore now",
      restoreProfileRequired: "Select restore profile.",
      restoreTitle: "Restore",
      retentionApplied: "Retention applied: {count} file(s) deleted",
      retentionApply: "Apply retention",
      retentionDays: "Retention days",
      retentionDryRun: "Retention dry-run",
      retentionDryRunDone: "Retention dry-run: {count} file(s) can be deleted",
      retentionHelp: "Keep recent backups and delete old dump files by policy.",
      retentionMinFiles: "Minimum files to keep",
      retentionTitle: "Retention policy",
      errorPrefix: "错误",
    },
  };

  const l = labels[uiLang];
  const tx = useCallback((key: string, fallback: string) => l[key] || fallback, [l]);

  const enabledLanguages = supportedLanguages.filter((item) => item.enabled).length;
  const enabledLanguageCodes = supportedLanguages
    .filter((item) => item.enabled)
    .map((item) => item.code)
    .join(", ");
  const systemLanguages = supportedLanguages.filter((item) => item.system).length;
  const selectedLocalUser = localUsers.find((item) => item.user_id === selectedLocalUserId) || null;
  const localFilterBadges = [
    localSearch.trim() ? `${tx("localFilterSearch", "Search")}: ${localSearch.trim()}` : "",
    localRoleFilter.trim() ? `${tx("localFilterRole", "Role")}: ${localRoleFilter.trim()}` : "",
    localLanguageFilter.trim() ? `${tx("localFilterLanguage", "Language")}: ${localLanguageFilter.trim()}` : "",
  ].filter(Boolean);
  const rbacFilterBadges = [
    assignmentUserFilter.trim() ? `${tx("rbacFilterUser", "Filter by user ID")}: ${assignmentUserFilter.trim()}` : "",
    assignmentRoleFilter.trim() ? `${tx("rbacFilterRole", "Filter by role")}: ${assignmentRoleFilter.trim()}` : "",
  ].filter(Boolean);
  const rbacAssignmentRows = useMemo(
    () => rbacAssignments.flatMap((row) => row.roles.map((role) => ({ user_id: row.user_id, role }))),
    [rbacAssignments],
  );
  const auditFilterBadges = [
    auditActor.trim() ? `${tx("auditActor", "Actor")}: ${auditActor.trim()}` : "",
    auditAction.trim() ? `${tx("auditAction", "Action")}: ${auditAction.trim()}` : "",
    auditEntity.trim() ? `${tx("auditEntity", "Entity")}: ${auditEntity.trim()}` : "",
    auditResult.trim() ? `${tx("auditResult", "Result")}: ${auditResult.trim()}` : "",
    auditSince.trim() ? `${tx("auditTs", "Timestamp")}: ${auditSince.trim()}` : "",
    auditCorrelationId.trim() ? `${tx("auditCorrelation", "Correlation ID")}: ${auditCorrelationId.trim()}` : "",
  ].filter(Boolean);
  const normalizedFeatureFlagSearch = featureFlagSearch.trim().toLowerCase();
  const filteredFeatureFlags = useMemo(() => {
    return featureFlags.filter((flag) => {
      if (featureFlagEnabledOnly && !flag.enabled) {
        return false;
      }
      if (!normalizedFeatureFlagSearch) {
        return true;
      }
      const haystack = `${flag.key} ${flag.description || ""}`.toLowerCase();
      return haystack.includes(normalizedFeatureFlagSearch);
    });
  }, [featureFlags, featureFlagEnabledOnly, normalizedFeatureFlagSearch]);
  const featureFlagFilterBadges = [
    normalizedFeatureFlagSearch ? `${tx("featureFlagFilterSearch", "Search")}: ${featureFlagSearch.trim()}` : "",
    featureFlagEnabledOnly ? tx("featureFlagFilterEnabledOnly", "Enabled only") : "",
  ].filter(Boolean);
  const hasActiveFeatureFlagFilters = featureFlagFilterBadges.length > 0;
  const featureFlagSummary = hasActiveFeatureFlagFilters
    ? tx("featureFlagsShowingFiltered", "Showing {count} filtered flags").replace("{count}", String(filteredFeatureFlags.length))
    : tx("featureFlagsShowing", "Showing {count} flags").replace("{count}", String(filteredFeatureFlags.length));
  const featureFlagsMutating = useMemo(
    () => Object.values(featureFlagUpdateBusy).some(Boolean),
    [featureFlagUpdateBusy],
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
  const backupSummaryStatus = backupLatestJob?.status || tx("backupStatusUnknown", "unknown");
  const backupActionsBusy = backupListLoading || backupRunBusy || backupRestoreBusy || backupRetentionBusy;
  const hasActiveAuditFilters = auditFilterBadges.length > 0;
  const auditLatestTimestamp = useMemo(() => {
    if (auditEvents.length === 0) {
      return "-";
    }
    let latest = auditEvents[0].timestamp;
    for (const item of auditEvents) {
      if (new Date(item.timestamp).getTime() > new Date(latest).getTime()) {
        latest = item.timestamp;
      }
    }
    return latest;
  }, [auditEvents]);

  const localUpdateHasChanges = useMemo(() => {
    if (!selectedLocalUser) {
      return false;
    }

    const displayChanged = selectedLocalUser.display_name.trim() !== editLocalDisplayName.trim();
    const languageChanged = selectedLocalUser.default_language.trim().toLowerCase() !== editLocalLanguage.trim().toLowerCase();

    const originalRoles = [...selectedLocalUser.roles].map((item) => item.trim()).filter(Boolean).sort();
    const editedRoles = editLocalRoles
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
      .sort();
    const rolesChanged = JSON.stringify(originalRoles) !== JSON.stringify(editedRoles);

    return displayChanged || languageChanged || rolesChanged;
  }, [editLocalDisplayName, editLocalLanguage, editLocalRoles, selectedLocalUser]);
  const availableCatalogLanguages = languageCatalog.filter((item) => {
    const exists = supportedLanguages.some((lang) => lang.code === item.code);
    if (exists) {
      return false;
    }

    if (!catalogQuery.trim()) {
      return true;
    }

    const haystack = `${item.code} ${item.name} ${item.native_name}`.toLowerCase();
    return haystack.includes(catalogQuery.trim().toLowerCase());
  });
  const selectedCatalogLanguage = languageCatalog.find((item) => item.code === selectedCatalogCode) || null;

  const loadLanguageCatalog = useCallback(async () => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const res = await fetch(`${baseUrl}/i18n/catalog`, { cache: "no-store" });
      if (!res.ok) {
        return;
      }

      const json = (await res.json()) as { languages?: CatalogLanguage[] };
      if (json.languages && json.languages.length > 0) {
        setLanguageCatalog(json.languages);
      }
    } catch {
      // Keep local fallback catalog when backend catalog is unavailable.
    }
  }, []);

  const buildAuthHeaders = useCallback((): Record<string, string> => {
    const token = localStorage.getItem("app.token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, []);

  const reloadLanguages = useCallback(async () => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const res = await fetch(`${baseUrl}/admin/i18n/languages`, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setStatus(`${l.errorPrefix}: ${err.detail || res.status}`);
        return;
      }

      const json = (await res.json()) as { items?: SupportedLanguage[] };
      const items = json.items || [];
      setSupportedLanguages(items);
      setLocalDefaultLanguage((current) => current || items.find((item) => item.enabled)?.code || "ru");
    } catch (error) {
      setStatus(String(error));
    }
  }, [buildAuthHeaders, l.errorPrefix]);

  const loadDashboard = useCallback(async () => {
    setOverviewFeedback(null);
    setDashboardLoading(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const res = await fetch(`${baseUrl}/admin/dashboard`, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setOverviewFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      const json = (await res.json()) as DashboardSnapshot;
      setDashboardSnapshot(json);
      setDashboardStamp(new Date(json.generated_at).toLocaleString());

      const exampleRes = await fetch(`${baseUrl}/admin/example-slice/reference-items`, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });
      if (exampleRes.ok) {
        const exampleJson = (await exampleRes.json()) as { items?: ExampleReferenceItem[] };
        setExampleReferenceItems(exampleJson.items || []);
      }

      setOverviewFeedback({ tone: "success", message: tx("overviewRefreshed", "Snapshot refreshed") });
    } catch (error) {
      setOverviewFeedback({ tone: "error", message: String(error) });
    } finally {
      setDashboardLoading(false);
    }
  }, [buildAuthHeaders, l.errorPrefix, tx]);

  const loadLocalUsers = useCallback(async (overrides?: { search?: string; role?: string; language?: string }) => {
    setLocalListBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const effectiveSearch = overrides?.search ?? localSearch;
      const effectiveRole = overrides?.role ?? localRoleFilter;
      const effectiveLanguage = overrides?.language ?? localLanguageFilter;
      const params = new URLSearchParams();
      if (effectiveSearch.trim()) {
        params.set("search", effectiveSearch.trim());
      }
      if (effectiveRole.trim()) {
        params.set("role", effectiveRole.trim());
      }
      if (effectiveLanguage.trim()) {
        params.set("language", effectiveLanguage.trim());
      }

      const query = params.toString();
      const endpoint = query ? `${baseUrl}/admin/local-users?${query}` : `${baseUrl}/admin/local-users`;
      const res = await fetch(endpoint, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setLocalFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      const json = (await res.json()) as { users?: typeof localUsers };
      setLocalUsers(json.users || []);
    } catch (error) {
      setLocalFeedback({ tone: "error", message: String(error) });
    } finally {
      setLocalListBusy(false);
    }
  }, [buildAuthHeaders, l.errorPrefix, localLanguageFilter, localRoleFilter, localSearch]);

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
        setIntegrationsFeedback({ tone: "success", message: tx("integrationsReloaded", "Integrations status refreshed") });
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
        setBackupFeedback({ tone: "success", message: tx("backupReload", "Reload backup data") });
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
      setBackupFeedback({ tone: "error", message: tx("restoreProfileRequired", "Select restore profile.") });
      return;
    }
    if (!restoreFileName) {
      setBackupFeedback({ tone: "error", message: tx("restoreFileRequired", "Select backup file for restore.") });
      return;
    }

    if (!dryRun) {
      const confirmed = window.confirm(
        tx("backupRestoreConfirmByFile", "Restore backup {file}?").replace("{file}", restoreFileName),
      );
      if (!confirmed) {
        setBackupFeedback({ tone: "info", message: tx("restoreCancelled", "Restore cancelled") });
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
          ? tx("restoreDryRunOk", "Restore dry-run prepared")
          : tx("restoreCompleted", "Restore completed"),
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

  const loadFeatureFlags = useCallback(async (preserveFeedback = false) => {
    setFeatureFlagsLoading(true);
    if (!preserveFeedback) {
      setFeatureFlagsFeedback(null);
    }
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const res = await fetch(`${baseUrl}/admin/feature-flags`, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setFeatureFlagsFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      const json = (await res.json()) as { flags?: FeatureFlag[] };
      setFeatureFlags(json.flags || []);
    } catch (error) {
      setFeatureFlagsFeedback({ tone: "error", message: String(error) });
    } finally {
      setFeatureFlagsLoading(false);
    }
  }, [buildAuthHeaders, l.errorPrefix]);

  const setFeatureFlagEnabled = async (flag: FeatureFlag, enabled: boolean) => {
    const confirmed = window.confirm(
      (enabled
        ? tx("featureFlagEnableConfirm", "Enable feature flag {flag}?")
        : tx("featureFlagDisableConfirm", "Disable feature flag {flag}?"))
        .replace("{flag}", flag.key),
    );
    if (!confirmed) {
      setFeatureFlagsFeedback({ tone: "info", message: tx("featureFlagUpdateCancelled", "Feature flag update cancelled") });
      return;
    }

    setFeatureFlagUpdateBusy((prev) => ({ ...prev, [flag.key]: true }));
    setFeatureFlagsFeedback(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/feature-flags`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          key: flag.key,
          enabled,
          description: flag.description || "",
          scope: flag.scope || "global",
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setFeatureFlagsFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      await loadFeatureFlags(true);
      const statusLabel = enabled ? tx("enabled", "Enabled") : tx("disabled", "Disabled");
      setFeatureFlagsFeedback({
        tone: "success",
        message: tx("featureFlagUpdated", "Feature flag {flag} set to {status}")
          .replace("{flag}", flag.key)
          .replace("{status}", statusLabel),
      });
    } catch (error) {
      setFeatureFlagsFeedback({ tone: "error", message: String(error) });
    } finally {
      setFeatureFlagUpdateBusy((prev) => ({ ...prev, [flag.key]: false }));
    }
  };

  const loadAuditEvents = useCallback(async (overrides?: {
    actor?: string;
    action?: string;
    entity?: string;
    result?: string;
    correlationId?: string;
    since?: string;
  }) => {
    setAuditLoading(true);
    setAuditFeedback(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const effectiveActor = overrides?.actor ?? auditActor;
      const effectiveAction = overrides?.action ?? auditAction;
      const effectiveEntity = overrides?.entity ?? auditEntity;
      const effectiveResult = overrides?.result ?? auditResult;
      const effectiveCorrelationId = overrides?.correlationId ?? auditCorrelationId;
      const effectiveSince = overrides?.since ?? auditSince;
      const params = new URLSearchParams();
      if (effectiveActor.trim()) {
        params.set("actor", effectiveActor.trim());
      }
      if (effectiveAction.trim()) {
        params.set("action", effectiveAction.trim());
      }
      if (effectiveEntity.trim()) {
        params.set("entity", effectiveEntity.trim());
      }
      if (effectiveResult.trim()) {
        params.set("result", effectiveResult.trim());
      }
      if (effectiveCorrelationId.trim()) {
        params.set("correlation_id", effectiveCorrelationId.trim());
      }
      if (effectiveSince.trim()) {
        params.set("since", effectiveSince.trim());
      }
      params.set("limit", "200");

      const res = await fetch(`${baseUrl}/admin/audit/events?${params.toString()}`, {
        headers: buildAuthHeaders(),
          credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setAuditFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      const json = (await res.json()) as { events?: AuditEvent[] };
      const rows = json.events || [];
      setAuditEvents(rows);
      setAuditFeedback({
        tone: "success",
        message: tx("auditShowingEvents", "Showing {count} events").replace("{count}", String(rows.length)),
      });
    } catch (error) {
      setAuditFeedback({ tone: "error", message: String(error) });
    } finally {
      setAuditLoading(false);
    }
  }, [buildAuthHeaders, auditActor, auditAction, auditEntity, auditResult, auditCorrelationId, auditSince, l.errorPrefix, tx]);

  const exportAudit = async (format: "json" | "csv") => {
    setAuditFeedback(null);
    setAuditExportBusy(format);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const params = new URLSearchParams();
      params.set("format", format);
      if (auditActor.trim()) {
        params.set("actor", auditActor.trim());
      }
      if (auditAction.trim()) {
        params.set("action", auditAction.trim());
      }
      if (auditEntity.trim()) {
        params.set("entity", auditEntity.trim());
      }
      if (auditResult.trim()) {
        params.set("result", auditResult.trim());
      }
      if (auditCorrelationId.trim()) {
        params.set("correlation_id", auditCorrelationId.trim());
      }
      if (auditSince.trim()) {
        params.set("since", auditSince.trim());
      }

      const res = await fetch(`${baseUrl}/admin/audit/export?${params.toString()}`, {
        headers: buildAuthHeaders(),
          credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setAuditFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      const text = await res.text();
      const blob = new Blob([text], { type: format === "csv" ? "text/csv" : "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = format === "csv" ? "audit-events.csv" : "audit-events.json";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setAuditFeedback({
        tone: "success",
        message: tx("export", "Export CSV/JSON"),
      });
    } catch (error) {
      setAuditFeedback({ tone: "error", message: String(error) });
    } finally {
      setAuditExportBusy("");
    }
  };

  const clearAuditFilters = async () => {
    setAuditActor("");
    setAuditAction("");
    setAuditEntity("");
    setAuditResult("");
    setAuditCorrelationId("");
    setAuditSince("");
    setAuditFeedback({ tone: "info", message: tx("auditNoFiltersActive", "No active filters") });
    await loadAuditEvents({
      actor: "",
      action: "",
      entity: "",
      result: "",
      correlationId: "",
      since: "",
    });
  };

  useEffect(() => {
    if (activeTab !== "overview") {
      return;
    }
    void loadDashboard();
  }, [activeTab, loadDashboard]);

  useEffect(() => {
    if (activeTab !== "local-users") {
      return;
    }
    void loadLocalUsers();
  }, [activeTab, loadLocalUsers]);

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
    if (localUsers.length === 0) {
      setSelectedLocalUserId("");
      setEditLocalDisplayName("");
      setEditLocalLanguage("ru");
      setEditLocalRoles("student");
      return;
    }

    const selected = localUsers.find((item) => item.user_id === selectedLocalUserId) || localUsers[0];
    setSelectedLocalUserId(selected.user_id);
    setEditLocalDisplayName(selected.display_name);
    setEditLocalLanguage(selected.default_language);
    setEditLocalRoles(selected.roles.join(","));
  }, [localUsers, selectedLocalUserId]);

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

  useEffect(() => {
    if (activeTab !== "audit") {
      return;
    }
    void loadAuditEvents();
  }, [activeTab, loadAuditEvents]);

  useEffect(() => {
    if (activeTab !== "feature-flags") {
      return;
    }
    void loadFeatureFlags();
  }, [activeTab, loadFeatureFlags]);

  useEffect(() => {
    void loadLanguageCatalog();
  }, [loadLanguageCatalog]);

  useEffect(() => {
    const enabledCodes = new Set(supportedLanguages.map((item) => item.code));
    if (selectedCatalogCode && enabledCodes.has(selectedCatalogCode)) {
      setSelectedCatalogCode("");
      return;
    }

    if (!selectedCatalogCode) {
      const firstAvailable = languageCatalog.find((item) => !enabledCodes.has(item.code));
      if (firstAvailable) {
        setSelectedCatalogCode(firstAvailable.code);
      }
    }
  }, [languageCatalog, selectedCatalogCode, supportedLanguages]);

  const addLanguage = async () => {
    setStatus(null);

    if (!selectedCatalogLanguage) {
      setStatus(l.languageRequired);
      return;
    }

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/i18n/languages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          code: selectedCatalogLanguage.code,
          name: selectedCatalogLanguage.name,
          native_name: selectedCatalogLanguage.native_name,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setStatus(`${l.errorPrefix}: ${err.detail || res.status}`);
        return;
      }

      setSelectedCatalogCode("");
      setCatalogQuery("");
      await reloadLanguages();
      setStatus(l.languageAdded);
    } catch (error) {
      setStatus(String(error));
    }
  };

  const setLanguageEnabled = async (codeToUpdate: string, enabled: boolean) => {
    setStatus(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/i18n/languages/${codeToUpdate}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({ enabled }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setStatus(`${l.errorPrefix}: ${err.detail || res.status}`);
        return;
      }

      await reloadLanguages();
      setStatus(
        enabled
          ? l.languageEnabledMsg.replace("{code}", codeToUpdate)
          : l.languageDisabledMsg.replace("{code}", codeToUpdate),
      );
    } catch (error) {
      setStatus(String(error));
    }
  };

  const deleteLanguage = async (codeToDelete: string) => {
    setStatus(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/i18n/languages/${codeToDelete}`, {
        method: "DELETE",
        headers: {
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setStatus(`${l.errorPrefix}: ${err.detail || res.status}`);
        return;
      }

      await reloadLanguages();
      setStatus(l.languageDeletedMsg.replace("{code}", codeToDelete));
    } catch (error) {
      setStatus(String(error));
    }
  };

  const createLocalUser = async () => {
    setLocalFeedback(null);
    if (!localLogin.trim() || !localPassword.trim() || !localDisplayName.trim()) {
      setLocalFeedback({ tone: "error", message: l.localUserRequired });
      return;
    }

    setLocalCreateBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/local-users`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          login: localLogin,
          password: localPassword,
          display_name: localDisplayName,
          roles: localRoles
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
          default_language: localDefaultLanguage,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setLocalFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      setLocalLogin("");
      setLocalPassword("");
      setLocalDisplayName("");
      setLocalRoles("student");
      setLocalDefaultLanguage("ru");
      await loadLocalUsers();
      await loadDashboard();
      setLocalFeedback({ tone: "success", message: l.localUserCreated });
      setDashboardStamp(new Date().toLocaleString());
    } catch (error) {
      setLocalFeedback({ tone: "error", message: String(error) });
    } finally {
      setLocalCreateBusy(false);
    }
  };

  const selectLocalUser = (userId: string) => {
    const selected = localUsers.find((item) => item.user_id === userId);
    if (!selected) {
      return;
    }
    setSelectedLocalUserId(selected.user_id);
    setEditLocalDisplayName(selected.display_name);
    setEditLocalLanguage(selected.default_language);
    setEditLocalRoles(selected.roles.join(","));
    setEditLocalPassword("");
    setEditLocalPasswordConfirm("");
  };

  const revertLocalUserForm = () => {
    if (!selectedLocalUser) {
      return;
    }

    setEditLocalDisplayName(selectedLocalUser.display_name);
    setEditLocalLanguage(selectedLocalUser.default_language);
    setEditLocalRoles(selectedLocalUser.roles.join(","));
    setEditLocalPassword("");
    setEditLocalPasswordConfirm("");
    setLocalFeedback({ tone: "info", message: tx("localFormReverted", "Changes reverted") });
  };

  const clearLocalFilters = async () => {
    setLocalSearch("");
    setLocalRoleFilter("");
    setLocalLanguageFilter("");
    setLocalFeedback(null);
    await loadLocalUsers({ search: "", role: "", language: "" });
  };

  const updateLocalUser = async () => {
    setLocalFeedback(null);
    if (!selectedLocalUserId) {
      setLocalFeedback({ tone: "error", message: tx("localUserSelectRequired", "Select a local user first.") });
      return;
    }
    if (!localUpdateHasChanges) {
      setLocalFeedback({ tone: "info", message: tx("localNoChanges", "No changes to save") });
      return;
    }

    setLocalUpdateBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/local-users/${encodeURIComponent(selectedLocalUserId)}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          display_name: editLocalDisplayName,
          language: editLocalLanguage,
          roles: editLocalRoles
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setLocalFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      await loadLocalUsers();
      await loadDashboard();
      setLocalFeedback({ tone: "success", message: tx("localUserUpdated", "Local user updated") });
    } catch (error) {
      setLocalFeedback({ tone: "error", message: String(error) });
    } finally {
      setLocalUpdateBusy(false);
    }
  };

  const updateLocalUserPassword = async () => {
    setLocalFeedback(null);
    if (!selectedLocalUserId) {
      setLocalFeedback({ tone: "error", message: tx("localUserSelectRequired", "Select a local user first.") });
      return;
    }
    if (!editLocalPassword.trim()) {
      setLocalFeedback({ tone: "error", message: tx("localPasswordRequired", "Password is required.") });
      return;
    }
    if (editLocalPassword.trim().length < 6) {
      setLocalFeedback({ tone: "error", message: tx("localPasswordMinLength", "Password must be at least 6 characters") });
      return;
    }
    if (editLocalPassword !== editLocalPasswordConfirm) {
      setLocalFeedback({ tone: "error", message: tx("localPasswordMismatch", "Passwords do not match") });
      return;
    }

    setLocalPasswordBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/local-users/${encodeURIComponent(selectedLocalUserId)}/password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({ password: editLocalPassword }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setLocalFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      setEditLocalPassword("");
      setEditLocalPasswordConfirm("");
      setLocalFeedback({ tone: "success", message: tx("localPasswordUpdated", "Password updated") });
    } catch (error) {
      setLocalFeedback({ tone: "error", message: String(error) });
    } finally {
      setLocalPasswordBusy(false);
    }
  };

  const deleteLocalUser = async () => {
    setLocalFeedback(null);
    if (!selectedLocalUserId) {
      setLocalFeedback({ tone: "error", message: tx("localUserSelectRequired", "Select a local user first.") });
      return;
    }

    const target = localUsers.find((item) => item.user_id === selectedLocalUserId);
    const confirmed = window.confirm(
      tx("localDeleteConfirm", "Delete selected local user?") +
      (target ? `\n${target.display_name} (${target.login}) [${target.user_id}]` : ""),
    );
    if (!confirmed) {
      setLocalFeedback({ tone: "info", message: tx("localDeleteCancelled", "Delete cancelled") });
      return;
    }

    setLocalDeleteBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/local-users/${encodeURIComponent(selectedLocalUserId)}`, {
        method: "DELETE",
        headers: {
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setLocalFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      await loadLocalUsers();
      await loadDashboard();
      setLocalFeedback({ tone: "success", message: tx("localUserDeleted", "Local user deleted") });
    } catch (error) {
      setLocalFeedback({ tone: "error", message: String(error) });
    } finally {
      setLocalDeleteBusy(false);
    }
  };

  const saveRbacRole = async () => {
    setRbacFeedback(null);
    if (!newRoleName.trim()) {
      setRbacFeedback({ tone: "error", message: tx("rbacRoleRequired", "Role name is required.") });
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

      setRbacFeedback({ tone: "success", message: tx("rbacRoleSaved", "Role saved") });
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
      setRbacFeedback({ tone: "error", message: tx("rbacAssignRequired", "User ID and role are required.") });
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

      setRbacFeedback({ tone: "success", message: tx("rbacAssigned", "Role assigned") });
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
      tx("rbacRevokeConfirm", "Revoke selected role assignment?") + `\n${revokeLabel}`,
    );
    if (!confirmed) {
      setRbacFeedback({ tone: "info", message: tx("rbacRevokeCancelled", "Revoke cancelled") });
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
      setRbacFeedback({ tone: "success", message: tx("rbacRevoked", "Role revoked") });
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
      setLdapFeedback({ tone: "success", message: tx("validationOk", "Validation passed") });
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

      setBackupFeedback({ tone: "success", message: tx("backupSaved", "Backup profiles saved") });
      await loadBackupStatus();
    } catch (error) {
      setBackupFeedback({ tone: "error", message: String(error) });
    }
  };

  const applyRetention = async (dryRun: boolean) => {
    setBackupFeedback(null);

    if (!dryRun) {
      const confirmed = window.confirm(
        tx("backupRetentionConfirm", "Apply retention policy?"),
      );
      if (!confirmed) {
        setBackupFeedback({ tone: "info", message: tx("retentionCancelled", "Retention cancelled") });
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
        ? tx("retentionDryRunDone", "Retention dry-run: {count} file(s) can be deleted")
        : tx("retentionApplied", "Retention applied: {count} file(s) deleted");
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
    const confirmed = window.confirm(tx("backupRunConfirm", "Run backup now?"));
    if (!confirmed) {
      setBackupFeedback({ tone: "info", message: tx("backupRunCancelled", "Backup run cancelled") });
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

      setBackupFeedback({ tone: "success", message: tx("backupCompleted", "Backup completed") });
      await loadBackupStatus();
      await loadRestoreCandidates();
    } catch (error) {
      setBackupFeedback({ tone: "error", message: String(error) });
    } finally {
      setBackupRunBusy(false);
    }
  };

  const tabButtonClass = (tab: AdminTab) => (activeTab === tab ? "tabButton tabButtonActive" : "tabButton");

  return (
    <main className="adminRoot">
      <section className="hero cardFade">
        <div>
          <p className="kicker">{l.controlCenter}</p>
          <h1>{t("admin.title")}</h1>
          <p>{t("admin.subtitle")}</p>
          <p className="stamp">{l.lastChange}: {dashboardStamp}</p>
        </div>
        <div className="heroRight">
          <p>{l.adminUser}</p>
          <small>{tx("authManagedByBackend", "Identity and roles are resolved by backend auth.")}</small>
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

      <section className="tabs cardFade">
        <button type="button" onClick={() => setActiveTab("overview")} className={tabButtonClass("overview")}>{l.overview}</button>
        <button type="button" onClick={() => setActiveTab("languages")} className={tabButtonClass("languages")}>{l.languages}</button>
        <button type="button" onClick={() => setActiveTab("local-users")} className={tabButtonClass("local-users")}>{l.localUsers}</button>
        <button type="button" onClick={() => setActiveTab("rbac")} className={tabButtonClass("rbac")}>{tx("rbac", "RBAC")}</button>
        <button type="button" onClick={() => setActiveTab("integrations")} className={tabButtonClass("integrations")}>{l.integrations}</button>
        <button type="button" onClick={() => setActiveTab("feature-flags")} className={tabButtonClass("feature-flags")}>{tx("featureFlags", "Feature Flags")}</button>
        <button type="button" onClick={() => setActiveTab("backups")} className={tabButtonClass("backups")}>{tx("backups", "Backups")}</button>
        <button type="button" onClick={() => setActiveTab("audit")} className={tabButtonClass("audit")}>{l.audit}</button>
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

      <style jsx>{`
        .adminRoot {
          --paper: #f7f4ea;
          --sand: #efe7d3;
          --ink: #17212f;
          --muted: #5d6a79;
          --line: #d8ceb5;
          --accent: #0f766e;
          --accent-2: #9a3412;
          min-height: 100vh;
          padding: 24px;
          background:
            radial-gradient(circle at 12% 12%, #fff2cc 0%, transparent 36%),
            radial-gradient(circle at 88% 10%, #dbeafe 0%, transparent 34%),
            linear-gradient(160deg, var(--paper), #f5efe0);
          color: var(--ink);
          font-family: "Space Grotesk", "IBM Plex Sans", "Segoe UI", sans-serif;
        }

        .hero,
        .statGrid,
        .tabs,
        .panel {
          width: min(1140px, 100%);
          margin: 0 auto;
        }

        .hero {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 20px;
          background: rgba(255, 255, 255, 0.75);
          border: 1px solid rgba(255, 255, 255, 0.9);
          border-radius: 20px;
          padding: 22px;
          box-shadow: 0 20px 45px rgba(23, 33, 47, 0.08);
        }

        .kicker {
          margin: 0 0 6px;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--accent);
          font-size: 12px;
          font-weight: 700;
        }

        h1 {
          margin: 0;
          font-size: clamp(28px, 4vw, 42px);
          line-height: 1.1;
        }

        h2 {
          margin: 0 0 8px;
          font-size: 22px;
        }

        p {
          margin: 8px 0;
        }

        .stamp {
          color: var(--muted);
          font-size: 13px;
        }

        .heroRight {
          display: grid;
          gap: 8px;
          align-content: start;
          background: linear-gradient(180deg, #ffffff, #f8fafc);
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
          font-size: 12px;
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
          gap: 12px;
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
          background: #ecfeff;
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
          background: #ecfeff;
          border: 1px solid #a5f3fc;
          color: #155e75;
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
  );
}
