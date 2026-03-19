import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from "react";

import { buildCsrfHeaders } from "../../components/csrf";
import type { AdminCopy, AiProviderForm, AiProviderStatus, InlineFeedback, LdapConfigForm, LdapStatus, TxFn } from "../types";

type UseAdminIntegrationsParams = {
  activeTab: string;
  buildAuthHeaders: () => Record<string, string>;
  l: AdminCopy;
  tx: TxFn;
};

type UseAdminIntegrationsResult = {
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
  setLdapConfigForm: (value: LdapConfigForm) => void;
  setLdapTestLogin: (value: string) => void;
  setLdapTestPassword: (value: string) => void;
  setAiConfigForm: Dispatch<SetStateAction<Record<string, AiProviderForm>>>;
  loadIntegrationStatus: (showFeedback?: boolean) => Promise<void>;
  saveLdapConfig: () => Promise<void>;
  testLdapConnection: (withUserBind: boolean) => Promise<void>;
  saveProviderConfig: (provider: string) => Promise<void>;
  validateProvider: (provider: string) => Promise<void>;
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

export function useAdminIntegrations({
  activeTab,
  buildAuthHeaders,
  l,
  tx,
}: UseAdminIntegrationsParams): UseAdminIntegrationsResult {
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

  const testLdapConnection = useCallback(async (withUserBind: boolean) => {
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
  }, [buildAuthHeaders, l.errorPrefix, l.serviceBindOk, l.validationOk, ldapTestLogin, ldapTestPassword, loadIntegrationStatus, tx]);

  const validateProvider = useCallback(async (provider: string) => {
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
  }, [buildAuthHeaders, l.errorPrefix, l.validationOk, loadIntegrationStatus]);

  const saveLdapConfig = useCallback(async () => {
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
  }, [buildAuthHeaders, l.errorPrefix, l.ldapSaved, ldapConfigForm, loadIntegrationStatus]);

  const saveProviderConfig = useCallback(async (provider: string) => {
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
  }, [aiConfigForm, buildAuthHeaders, l.errorPrefix, l.providerSaved, loadIntegrationStatus]);

  useEffect(() => {
    if (activeTab !== "integrations") {
      return;
    }
    void loadIntegrationStatus();
  }, [activeTab, loadIntegrationStatus]);

  return {
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
  };
}
