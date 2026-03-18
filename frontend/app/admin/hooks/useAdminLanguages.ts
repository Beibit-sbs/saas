import { useCallback, useEffect, useMemo, useState } from "react";

import { buildCsrfHeaders } from "../../components/csrf";
import type { AdminCopy, CatalogLanguage, SupportedLanguage } from "../types";

type UseAdminLanguagesParams = {
  buildAuthHeaders: () => Record<string, string>;
  l: AdminCopy;
  onLanguagesReloaded?: (items: SupportedLanguage[]) => void;
  onStatusChange: (value: string | null) => void;
};

type UseAdminLanguagesResult = {
  supportedLanguages: SupportedLanguage[];
  catalogQuery: string;
  availableCatalogLanguages: CatalogLanguage[];
  selectedCatalogCode: string;
  selectedCatalogLanguage: CatalogLanguage | null;
  setCatalogQuery: (value: string) => void;
  setSelectedCatalogCode: (code: string) => void;
  addLanguage: () => Promise<void>;
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
        onStatusChange(`${l.errorPrefix}: ${err.detail || res.status}`);
        return;
      }

      const json = (await res.json()) as { items?: SupportedLanguage[] };
      const items = json.items || [];
      setSupportedLanguages(items);
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
        onStatusChange(`${l.errorPrefix}: ${err.detail || res.status}`);
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
        onStatusChange(`${l.errorPrefix}: ${err.detail || res.status}`);
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

  const deleteLanguage = useCallback(async (codeToDelete: string) => {
    onStatusChange(null);
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
        onStatusChange(`${l.errorPrefix}: ${err.detail || res.status}`);
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
    catalogQuery,
    availableCatalogLanguages,
    selectedCatalogCode,
    selectedCatalogLanguage,
    setCatalogQuery,
    setSelectedCatalogCode,
    addLanguage,
    setLanguageEnabled,
    deleteLanguage,
  };
}
