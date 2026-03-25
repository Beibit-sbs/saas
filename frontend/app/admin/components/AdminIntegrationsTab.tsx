import type { AdminCopy, AiProviderForm, AiProviderStatus, InlineFeedback, LdapConfigForm, LdapStatus, TxFn } from "../types";

type AdminIntegrationsTabProps = {
  l: AdminCopy;
  tx: TxFn;
  ldapStatus: LdapStatus | null;
  ldapConfigForm: LdapConfigForm;
  ldapTestLogin: string;
  ldapTestPassword: string;
  ldapTestResult: string | null;
  integrationsFeedback: InlineFeedback | null;
  ldapFeedback: InlineFeedback | null;
  aiProviderFeedback: Record<string, InlineFeedback | null>;
  integrationsLoading: boolean;
  ldapSaveBusy: boolean;
  ldapTestServiceBusy: boolean;
  ldapTestUserBusy: boolean;
  aiSaveBusyByProvider: Record<string, boolean>;
  aiValidateBusyByProvider: Record<string, boolean>;
  aiProviders: AiProviderStatus[];
  aiConfigForm: Record<string, AiProviderForm>;
  onReloadIntegrations: (force?: boolean) => void | Promise<void>;
  onLdapConfigChange: (value: LdapConfigForm) => void;
  onLdapTestLoginChange: (value: string) => void;
  onLdapTestPasswordChange: (value: string) => void;
  onSaveLdapConfig: () => void | Promise<void>;
  onTestLdapConnection: (withUserBind: boolean) => void | Promise<void>;
  onAiConfigFormChange: (provider: string, value: AiProviderForm) => void;
  onSaveProviderConfig: (provider: string) => void | Promise<void>;
  onValidateProvider: (provider: string) => void | Promise<void>;
};

export function AdminIntegrationsTab({
  l,
  tx,
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
  onReloadIntegrations,
  onLdapConfigChange,
  onLdapTestLoginChange,
  onLdapTestPasswordChange,
  onSaveLdapConfig,
  onTestLdapConnection,
  onAiConfigFormChange,
  onSaveProviderConfig,
  onValidateProvider,
}: AdminIntegrationsTabProps) {
  return (
    <div className="grid2">
      <article className="panelCard">
        <h2>{l.directoryIdentity}</h2>
        <p className="subText">{l.directoryHelp}</p>
        <div className="badgeRow">
          <span className="badge">LDAP/AD</span>
          <span className="badge">{l.enabledFlag}: {ldapStatus?.enabled ? l.yes : l.no}</span>
          <span className="badge">{ldapStatus?.configured ? l.configured : l.notConfigured}</span>
          {integrationsLoading ? <span className="badge badgeInfo">{tx("loading")}</span> : null}
        </div>
        <div className="rowButtons mt-2">
          <button type="button" className="ghost" onClick={() => void onReloadIntegrations(true)} disabled={integrationsLoading}>
            {integrationsLoading ? tx("loading") : tx("refreshList")}
          </button>
        </div>
        {integrationsFeedback ? (
          <p className={`inlineFeedback inlineFeedback${integrationsFeedback.tone === "error" ? "Error" : integrationsFeedback.tone === "success" ? "Success" : "Info"}`}>
            {integrationsFeedback.message}
          </p>
        ) : null}
        {ldapStatus ? (
          <div className="integrationDetails">
            <h3>{l.ldapConfigTitle}</h3>
            <label className="toggleRow">
              <input type="checkbox" checked={ldapConfigForm.enabled} onChange={(e) => onLdapConfigChange({ ...ldapConfigForm, enabled: e.target.checked })} />
              <span>{l.ldapEnabled}</span>
            </label>
            <div className="formGrid compactFormGrid">
              <input value={ldapConfigForm.server_uri} onChange={(e) => onLdapConfigChange({ ...ldapConfigForm, server_uri: e.target.value })} placeholder={l.ldapServerUri} />
              <input value={ldapConfigForm.bind_dn} onChange={(e) => onLdapConfigChange({ ...ldapConfigForm, bind_dn: e.target.value })} placeholder={l.ldapBindDn} />
              <input value={ldapConfigForm.bind_password} onChange={(e) => onLdapConfigChange({ ...ldapConfigForm, bind_password: e.target.value })} placeholder={l.ldapBindPassword} type="password" />
              <input value={ldapConfigForm.base_dn} onChange={(e) => onLdapConfigChange({ ...ldapConfigForm, base_dn: e.target.value })} placeholder={l.ldapBaseDn} />
              <input value={ldapConfigForm.user_filter} onChange={(e) => onLdapConfigChange({ ...ldapConfigForm, user_filter: e.target.value })} placeholder={l.ldapUserFilter} />
              <input value={ldapConfigForm.display_name_attribute} onChange={(e) => onLdapConfigChange({ ...ldapConfigForm, display_name_attribute: e.target.value })} placeholder={l.ldapDisplayAttr} />
              <input value={ldapConfigForm.login_attribute} onChange={(e) => onLdapConfigChange({ ...ldapConfigForm, login_attribute: e.target.value })} placeholder={l.ldapLoginAttr} />
              <input value={ldapConfigForm.group_attribute} onChange={(e) => onLdapConfigChange({ ...ldapConfigForm, group_attribute: e.target.value })} placeholder={l.ldapGroupAttr} />
              <input value={ldapConfigForm.group_role_map_json} onChange={(e) => onLdapConfigChange({ ...ldapConfigForm, group_role_map_json: e.target.value })} placeholder={l.ldapRoleMapJson} />
              <input value={ldapConfigForm.default_role} onChange={(e) => onLdapConfigChange({ ...ldapConfigForm, default_role: e.target.value })} placeholder={l.ldapDefaultRole} />
              <input value={ldapConfigForm.timeout_seconds} onChange={(e) => onLdapConfigChange({ ...ldapConfigForm, timeout_seconds: e.target.value })} placeholder={l.ldapTimeout} />
            </div>
            <p className="subText">{tx("keepSecretHint")}</p>
            {ldapFeedback ? (
              <p className={`inlineFeedback inlineFeedback${ldapFeedback.tone === "error" ? "Error" : ldapFeedback.tone === "success" ? "Success" : "Info"}`}>
                {ldapFeedback.message}
              </p>
            ) : null}
            <div className="formGrid compactFormGrid">
              <input value={ldapTestLogin} onChange={(e) => onLdapTestLoginChange(e.target.value)} placeholder={l.ldapLoginPlaceholder} />
              <input value={ldapTestPassword} onChange={(e) => onLdapTestPasswordChange(e.target.value)} placeholder={l.ldapPasswordPlaceholder} type="password" />
            </div>
            <div className="rowButtons">
              <button type="button" onClick={() => void onSaveLdapConfig()} className="primary" disabled={ldapSaveBusy || ldapTestServiceBusy || ldapTestUserBusy || integrationsLoading}>
                {ldapSaveBusy ? tx("saving") : l.saveSettings}
              </button>
              <button type="button" onClick={() => void onTestLdapConnection(false)} className="ghost" disabled={ldapSaveBusy || ldapTestServiceBusy || ldapTestUserBusy || integrationsLoading}>
                {ldapTestServiceBusy ? tx("testing") : l.testConnection}
              </button>
              <button type="button" onClick={() => void onTestLdapConnection(true)} className="primary" disabled={ldapSaveBusy || ldapTestServiceBusy || ldapTestUserBusy || integrationsLoading}>
                {ldapTestUserBusy ? tx("testing") : l.testUserBind}
              </button>
            </div>
            {ldapTestResult ? <p className="subText">{ldapTestResult}</p> : null}
          </div>
        ) : null}
      </article>
      <article className="panelCard">
        <h2>{l.aiProviders}</h2>
        <p className="subText">{l.aiHelp}</p>
        {aiProviders.length === 0 ? (
          <p className="subText">{l.noProviders}</p>
        ) : (
          <div className="providerStack">
            {aiProviders.map((provider) => {
              const providerBusy = Boolean(aiSaveBusyByProvider[provider.provider] || aiValidateBusyByProvider[provider.provider] || integrationsLoading);

              return (
                <div key={provider.provider} className="providerCard">
                  <div>
                    <p><b>{provider.provider}</b></p>
                    <p className="subText">{l.validationEndpoint}: {provider.validation_url || "-"}</p>
                  </div>
                  <div className="formGrid compactFormGrid">
                    <input
                      value={aiConfigForm[provider.provider]?.apiKey || ""}
                      onChange={(e) => onAiConfigFormChange(provider.provider, { apiKey: e.target.value, validationUrl: aiConfigForm[provider.provider]?.validationUrl || provider.validation_url || "" })}
                      placeholder={l.providerApiKey}
                      type="password"
                      disabled={providerBusy}
                    />
                    <input
                      value={aiConfigForm[provider.provider]?.validationUrl || provider.validation_url || ""}
                      onChange={(e) => onAiConfigFormChange(provider.provider, { apiKey: aiConfigForm[provider.provider]?.apiKey || "", validationUrl: e.target.value })}
                      placeholder={l.validationEndpoint}
                      disabled={providerBusy}
                    />
                  </div>
                  <p className="subText">{tx("keepSecretHint")}</p>
                  <div className="providerActions">
                    <span className="badge">{provider.configured ? l.configured : l.notConfigured}</span>
                    {providerBusy ? <span className="badge badgeInfo">{tx("loading")}</span> : null}
                    <button type="button" onClick={() => void onSaveProviderConfig(provider.provider)} className="primary" disabled={providerBusy}>
                      {aiSaveBusyByProvider[provider.provider] ? tx("saving") : l.saveSettings}
                    </button>
                    <button type="button" onClick={() => void onValidateProvider(provider.provider)} className="ghost" disabled={providerBusy}>
                      {aiValidateBusyByProvider[provider.provider] ? tx("validating") : l.validateProvider}
                    </button>
                  </div>
                  {aiProviderFeedback[provider.provider] ? (
                    <p className={`inlineFeedback inlineFeedback${aiProviderFeedback[provider.provider]?.tone === "error" ? "Error" : aiProviderFeedback[provider.provider]?.tone === "success" ? "Success" : "Info"}`}>
                      {aiProviderFeedback[provider.provider]?.message}
                    </p>
                  ) : null}
                </div>
              );
            })}
          </div>
        )}
      </article>
    </div>
  );
}