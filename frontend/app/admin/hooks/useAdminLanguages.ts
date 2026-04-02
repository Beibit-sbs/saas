import { useCallback, useEffect, useMemo, useState } from "react";

import { buildCsrfHeaders } from "../../components/csrf";
import type { AdminCopy, CatalogLanguage, SupportedLanguage } from "../types";

const ADMIN_I18N_BFF_BASE = "/api/bff/admin/i18n";

function extractErrorDetail(errorBody: unknown, fallbackStatus: number): string {
  if (errorBody && typeof errorBody === "object") {
    const body = errorBody as { detail?: unknown; error?: { detail?: unknown } };
    if (typeof body.detail === "string" && body.detail.trim().length > 0) {
      return body.detail;
    }
    if (typeof body.error?.detail === "string" && body.error.detail.trim().length > 0) {
      return body.error.detail;
    }
  }
  return String(fallbackStatus);
}

type UseAdminLanguagesParams = {
  buildAuthHeaders: () => Record<string, string>;
  l: AdminCopy;
  onLanguagesReloaded?: (items: SupportedLanguage[]) => void;
  onStatusChange: (value: string | null) => void;
};

type UseAdminLanguagesResult = {
  supportedLanguages: SupportedLanguage[];
  defaultLanguage: string;
  catalogQuery: string;
  availableCatalogLanguages: CatalogLanguage[];
  selectedCatalogCode: string;
  selectedCatalogLanguage: CatalogLanguage | null;
  setCatalogQuery: (value: string) => void;
  setSelectedCatalogCode: (code: string) => void;
  addLanguage: () => Promise<void>;
  setDefaultLanguage: (code: string) => Promise<void>;
  setLanguageEnabled: (codeToUpdate: string, enabled: boolean) => Promise<void>;
  deleteLanguage: (codeToDelete: string) => Promise<void>;
};

export function useAdminLanguages({
  buildAuthHeaders,
  l,
  onLanguagesReloaded,
  onStatusChange,
}: UseAdminLanguagesParams): UseAdminLanguagesResult {
  const [supportedLanguages, setSupportedLanguages] = useState<SupportedLanguage[]>([]);
  const [languageCatalog, setLanguageCatalog] = useState<CatalogLanguage[]>([]);
  const [selectedCatalogCode, setSelectedCatalogCode] = useState("");
  const [catalogQuery, setCatalogQuery] = useState("");
  const [defaultLanguage, setDefaultLanguageState] = useState("ru");

  const availableCatalogLanguages = useMemo(() => languageCatalog.filter((item) => {
    const exists = supportedLanguages.some((lang) => lang.code === item.code);
    if (exists) {
      return false;
    }

    if (!catalogQuery.trim()) {
      return true;
    }

    const haystack = `${item.code} ${item.name} ${item.native_name}`.toLowerCase();
    return haystack.includes(catalogQuery.trim().toLowerCase());
  }), [catalogQuery, languageCatalog, supportedLanguages]);

  const selectedCatalogLanguage = useMemo(
    () => languageCatalog.find((item) => item.code === selectedCatalogCode) || null,
    [languageCatalog, selectedCatalogCode],
  );

  const loadLanguageCatalog = useCallback(async () => {
    try {
      const res = await fetch("/api/i18n/catalog", { cache: "no-store", credentials: "include" });
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

  const reloadLanguages = useCallback(async () => {
    try {
      const res = await fetch(`${ADMIN_I18N_BFF_BASE}/languages`, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        onStatusChange(`${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`);
        return;
      }

      const json = (await res.json()) as {
        items?: SupportedLanguage[];
        languages?: SupportedLanguage[];
        default_language?: string;
      };
      const items = json.items || json.languages || [];
      setSupportedLanguages(items);
      if (json.default_language) {
        setDefaultLanguageState(String(json.default_language));
      }
      onLanguagesReloaded?.(items);
    } catch (error) {
      onStatusChange(String(error));
    }
  }, [buildAuthHeaders, l.errorPrefix, onLanguagesReloaded, onStatusChange]);

  const addLanguage = useCallback(async () => {
    onStatusChange(null);

    if (!selectedCatalogLanguage) {
      onStatusChange(l.languageRequired);
      return;
    }

    try {
      const csrfHeaders = await buildCsrfHeaders("/api");
      const res = await fetch(`${ADMIN_I18N_BFF_BASE}/languages`, {
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
        onStatusChange(`${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`);
        return;
      }

      setSelectedCatalogCode("");
      setCatalogQuery("");
      await reloadLanguages();
      onStatusChange(l.languageAdded);
    } catch (error) {
      onStatusChange(String(error));
    }
  }, [buildAuthHeaders, l.errorPrefix, l.languageAdded, l.languageRequired, onStatusChange, reloadLanguages, selectedCatalogLanguage]);

  const setLanguageEnabled = useCallback(async (codeToUpdate: string, enabled: boolean) => {
    onStatusChange(null);
    try {
      const csrfHeaders = await buildCsrfHeaders("/api");
      const res = await fetch(`${ADMIN_I18N_BFF_BASE}/languages/${codeToUpdate}`, {
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
        onStatusChange(`${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`);
        return;
      }

      await reloadLanguages();
      onStatusChange(
        enabled
          ? l.languageEnabledMsg.replace("{code}", codeToUpdate)
          : l.languageDisabledMsg.replace("{code}", codeToUpdate),
      );
    } catch (error) {
      onStatusChange(String(error));
    }
  }, [buildAuthHeaders, l.errorPrefix, l.languageDisabledMsg, l.languageEnabledMsg, onStatusChange, reloadLanguages]);

  const setDefaultLanguage = useCallback(async (code: string) => {
    onStatusChange(null);

    if (!code) {
      onStatusChange(l.defaultLanguageRequired);
      return;
    }

    try {
      const csrfHeaders = await buildCsrfHeaders("/api");
      const res = await fetch(`${ADMIN_I18N_BFF_BASE}/default-language`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({ code }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        onStatusChange(`${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`);
        return;
      }

      await reloadLanguages();
      onStatusChange(l.defaultLanguageUpdatedMsg.replace("{code}", code));
    } catch (error) {
      onStatusChange(String(error));
    }
  }, [buildAuthHeaders, l.defaultLanguageRequired, l.defaultLanguageUpdatedMsg, l.errorPrefix, onStatusChange, reloadLanguages]);

  const deleteLanguage = useCallback(async (codeToDelete: string) => {
    onStatusChange(null);
    try {
      const csrfHeaders = await buildCsrfHeaders("/api");
      const res = await fetch(`${ADMIN_I18N_BFF_BASE}/languages/${codeToDelete}`, {
        method: "DELETE",
        headers: {
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        onStatusChange(`${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`);
        return;
      }

      await reloadLanguages();
      onStatusChange(l.languageDeletedMsg.replace("{code}", codeToDelete));
    } catch (error) {
      onStatusChange(String(error));
    }
  }, [buildAuthHeaders, l.errorPrefix, l.languageDeletedMsg, onStatusChange, reloadLanguages]);

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

  return {
    supportedLanguages,
    defaultLanguage,
    catalogQuery,
    availableCatalogLanguages,
    selectedCatalogCode,
    selectedCatalogLanguage,
    setCatalogQuery,
    setSelectedCatalogCode,
    addLanguage,
    setDefaultLanguage,
    setLanguageEnabled,
    deleteLanguage,
  };
}
