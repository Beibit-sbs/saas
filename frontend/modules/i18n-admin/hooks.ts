import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type {
  AdminLanguagesResponse,
  LanguageCatalogResponse,
  AddLanguagePayload,
  ToggleLanguagePayload,
  SetDefaultLanguagePayload,
} from "./types";

const ADMIN_BASE = "/api/admin/i18n";
const PUBLIC_BASE = "/api/i18n";

export const ADMIN_LANGUAGES_KEY = "admin-i18n-languages";
export const LANGUAGE_CATALOG_KEY = "public-language-catalog";

export function useAdminLanguages() {
  return useQuery({
    queryKey: [ADMIN_LANGUAGES_KEY],
    queryFn: () => apiGet<AdminLanguagesResponse>(`${ADMIN_BASE}/languages`),
  });
}

export function useLanguageCatalog() {
  return useQuery({
    queryKey: [LANGUAGE_CATALOG_KEY],
    queryFn: () => apiGet<LanguageCatalogResponse>(`${PUBLIC_BASE}/catalog`),
  });
}

export function useAddLanguage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AddLanguagePayload) =>
      apiPost<{ language: { code: string } }>(`${ADMIN_BASE}/languages`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ADMIN_LANGUAGES_KEY] }),
  });
}

export function useSetDefaultLanguage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: SetDefaultLanguagePayload) =>
      apiPatch<{ default_language: string }>(`${ADMIN_BASE}/default-language`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ADMIN_LANGUAGES_KEY] }),
  });
}

export function useToggleLanguage(code: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ToggleLanguagePayload) =>
      apiPatch<{ language: { code: string; enabled: boolean } }>(`${ADMIN_BASE}/languages/${code}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ADMIN_LANGUAGES_KEY] }),
  });
}

export function useDeleteLanguage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (code: string) => apiDelete<{ status: string; code: string }>(`${ADMIN_BASE}/languages/${code}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ADMIN_LANGUAGES_KEY] }),
  });
}
