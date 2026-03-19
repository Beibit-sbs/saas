"use client";
import { useCallback, useState } from "react";
import { adminTranslations, type AdminTranslationKey } from "../../i18n/admin";
import { useLanguage } from "../components/LanguageProvider";
import { AdminAuditTab } from "./components/AdminAuditTab";
import { AdminBackupsTab } from "./components/AdminBackupsTab";
import { AdminExampleNotesTab } from "./components/AdminExampleNotesTab";
import { AdminFeatureFlagsTab } from "./components/AdminFeatureFlagsTab";
import { AdminIntegrationsTab } from "./components/AdminIntegrationsTab";
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
import { useAdminLanguages } from "./hooks/useAdminLanguages";
import { useAdminLocalUsers } from "./hooks/useAdminLocalUsers";
import { useAdminOverview } from "./hooks/useAdminOverview";
import { useAdminRbac } from "./hooks/useAdminRbac";
import { useAdminSystemHealth } from "./hooks/useAdminSystemHealth";
import { useAdminTenants } from "./hooks/useAdminTenants";
import { useAdminUniversity } from "./hooks/useAdminUniversity";
import type { AdminTab, UiLang } from "./types";

const toUiLang = (value: string): UiLang => {
  if (value === "en" || value === "kk") {
    return value;
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
