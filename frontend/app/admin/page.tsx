"use client";
import { useCallback, useState } from "react";
import { adminTranslations, type AdminTranslationKey } from "../../i18n/admin";
import "./admin-legacy.css";
import { useLanguage } from "../components/LanguageProvider";
import { AdminAuditTab } from "./components/AdminAuditTab";
import { AdminBackupsTab } from "./components/AdminBackupsTab";
import { AdminExampleNotesTab } from "./components/AdminExampleNotesTab";
import { AdminFeatureFlagsTab } from "./components/AdminFeatureFlagsTab";
import { AdminIntegrationsTab } from "./components/AdminIntegrationsTab";
import { AdminJobsTab } from "./components/AdminJobsTab";
import { AdminLanguagesTab } from "./components/AdminLanguagesTab";
import { AdminLocalUsersTab } from "./components/AdminLocalUsersTab";
import { AdminOverviewTab } from "./components/AdminOverviewTab";
import { AdminRbacTab } from "./components/AdminRbacTab";
import { AdminSystemTab } from "./components/AdminSystemTab";
import { AdminTenantsTab } from "./components/AdminTenantsTab";
import { AdminUniversityTab } from "./components/AdminUniversityTab";
import { AdminShell, type AdminSection } from "./components/AdminShell";
import { useAdminAudit } from "./hooks/useAdminAudit";
import { useAdminBackups } from "./hooks/useAdminBackups";
import { useAdminFeatureFlags } from "./hooks/useAdminFeatureFlags";
import { useAdminIntegrations } from "./hooks/useAdminIntegrations";
import { useAdminJobs } from "./hooks/useAdminJobs";
import { useAdminLanguages } from "./hooks/useAdminLanguages";
import { useAdminLocalUsers } from "./hooks/useAdminLocalUsers";
import { useAdminOverview } from "./hooks/useAdminOverview";
import { useAdminRbac } from "./hooks/useAdminRbac";
import { useAdminSystemHealth } from "./hooks/useAdminSystemHealth";
import { useAdminTenants } from "./hooks/useAdminTenants";
import { useAdminUniversity } from "./hooks/useAdminUniversity";
import type { AdminTab, UiLang } from "./types";

const toUiLang = (value: string): UiLang => {
  const normalized = String(value || "").toLowerCase();
  const base = normalized.split(/[-_]/)[0];

  if (base === "en" || base === "kk" || base === "ru") {
    return base;
  }

  return "ru";
};

export default function AdminPage() {
  const { t, language } = useLanguage();

  const [activeTab, setActiveTab] = useState<AdminTab>("overview");
  const [status, setStatus] = useState<string | null>(null);

  const uiLang = toUiLang(String(language));

  const l = adminTranslations[uiLang];
  const tx = useCallback((key: AdminTranslationKey, fallback?: string) => {
    const value = l?.[key] ?? adminTranslations.ru[key];
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

  const buildAuthHeaders = useCallback((): Record<string, string> => ({}), []);

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

  const {
    rbacFeedback,
    rbacRolesBusy,
    rbacRoleSaveBusy,
    rbacAssignmentsBusy,
    rbacAssignBusy,
    rbacRevokeBusyKey,
    rbacRoles,
    rbacAssignments,
    newRoleName,
    newRolePermissions,
    assignUserId,
    assignRoleName,
    assignmentUserFilter,
    assignmentRoleFilter,
    rbacFilterBadges,
    rbacAssignmentRows,
    setNewRoleName,
    setNewRolePermissions,
    setAssignUserId,
    setAssignRoleName,
    setAssignmentUserFilter,
    setAssignmentRoleFilter,
    loadRbacRoles,
    loadRbacAssignments,
    saveRbacRole,
    assignRbacRole,
    revokeRbacRole,
    clearRbacFilters,
  } = useAdminRbac({
    activeTab,
    buildAuthHeaders,
    l,
    tx,
    onAfterMutate: loadDashboard,
  });

  const {
    ldapStatus,
    ldapConfigForm,
    ldapTestLogin,
    ldapTestPassword,
    ldapTestResult,
    integrationsFeedback,
    ldapFeedback,
    aiProviderFeedback,
    integrationsLoading,
    ldapSaveBusy,
    ldapTestServiceBusy,
    ldapTestUserBusy,
    aiSaveBusyByProvider,
    aiValidateBusyByProvider,
    aiProviders,
    aiConfigForm,
    setLdapConfigForm,
    setLdapTestLogin,
    setLdapTestPassword,
    setAiConfigForm,
    loadIntegrationStatus,
    saveLdapConfig,
    testLdapConnection,
    saveProviderConfig,
    validateProvider,
  } = useAdminIntegrations({
    activeTab,
    buildAuthHeaders,
    l,
    tx,
  });

  const {
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
  } = useAdminBackups({
    activeTab,
    buildAuthHeaders,
    l,
    tx,
  });

  const {
    jobsLoading,
    jobsMutating,
    jobsFeedback,
    jobsStatusFilter,
    filteredJobs,
    setJobsStatusFilter,
    loadJobs,
    createJob,
    retryJob,
    cancelJob,
  } = useAdminJobs({
    activeTab,
    buildAuthHeaders,
    tx,
  });

  const {
    systemHealth,
    loading: systemHealthLoading,
    feedback: systemHealthFeedback,
    refresh: refreshSystemHealth,
    lastUpdated: systemHealthLastUpdated,
  } = useAdminSystemHealth({
    activeTab,
    buildAuthHeaders,
  });

  const {
    activeEntity,
    setActiveEntity,
    itemsByEntity,
    loading: universityLoading,
    mutating: universityMutating,
    feedback: universityFeedback,
    lastUpdated: universityLastUpdated,
    refresh: refreshUniversity,
    createItem: createUniversityItem,
    updateItem: updateUniversityItem,
    deleteItem: deleteUniversityItem,
  } = useAdminUniversity({
    activeTab,
    buildAuthHeaders,
  });

  const {
    tenants,
    loading: tenantsLoading,
    mutating: tenantsMutating,
    feedback: tenantsFeedback,
    lastUpdated: tenantsLastUpdated,
    refresh: refreshTenants,
    createTenant,
    updateTenant,
    deleteTenant,
  } = useAdminTenants({
    activeTab,
    buildAuthHeaders,
  });

  const adminSections: AdminSection[] = [
    { id: "overview", label: l.overview, icon: "◧" },
    { id: "languages", label: l.languages, icon: "⟲" },
    { id: "local-users", label: l.localUsers, icon: "◫" },
    { id: "rbac", label: tx("rbac"), icon: "◎" },
    { id: "integrations", label: l.integrations, icon: "◇" },
    { id: "backups", label: tx("backups"), icon: "▣" },
    { id: "jobs", label: "Jobs", icon: "◔" },
    { id: "audit", label: l.audit, icon: "◌" },
    { id: "feature-flags", label: tx("featureFlags"), icon: "✦" },
    { id: "example-notes", label: tx("exampleNotesTab", "Example Notes"), icon: "▤" },
    { id: "system", label: "System", icon: "◍" },
    { id: "university", label: "University", icon: "◬" },
    { id: "tenants", label: "Tenants", icon: "⬡" },
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
            buildAuthHeaders={buildAuthHeaders}
            tx={tx}
          />
        ) : null}
        {activeTab === "system" ? (
          <AdminSystemTab
            systemHealth={systemHealth}
            loading={systemHealthLoading}
            feedback={systemHealthFeedback}
            lastUpdated={systemHealthLastUpdated}
            onRefresh={refreshSystemHealth}
          />
        ) : null}

        {activeTab === "jobs" ? (
          <AdminJobsTab
            tx={tx}
            jobsLoading={jobsLoading}
            jobsMutating={jobsMutating}
            jobsFeedback={jobsFeedback}
            jobsStatusFilter={jobsStatusFilter}
            filteredJobs={filteredJobs}
            onStatusFilterChange={setJobsStatusFilter}
            onLoadJobs={loadJobs}
            onCreateJob={createJob}
            onRetryJob={retryJob}
            onCancelJob={cancelJob}
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

        {activeTab === "university" ? (
          <AdminUniversityTab
            activeEntity={activeEntity}
            onEntityChange={setActiveEntity}
            itemsByEntity={itemsByEntity}
            loading={universityLoading}
            mutating={universityMutating}
            feedback={universityFeedback}
            lastUpdated={universityLastUpdated}
            onRefresh={refreshUniversity}
            onCreateItem={createUniversityItem}
            onUpdateItem={updateUniversityItem}
            onDeleteItem={deleteUniversityItem}
          />
        ) : null}

        {activeTab === "tenants" ? (
          <AdminTenantsTab
            tenants={tenants}
            loading={tenantsLoading}
            mutating={tenantsMutating}
            feedback={tenantsFeedback}
            lastUpdated={tenantsLastUpdated}
            onRefresh={refreshTenants}
            onCreateTenant={createTenant}
            onUpdateTenant={updateTenant}
            onDeleteTenant={deleteTenant}
          />
        ) : null}

        {status ? <p className="statusLine">{status}</p> : null}
      </section>
    </main>
    </AdminShell>
  );
}
