export interface AdminLanguage {
  code: string;
  name: string;
  native_name?: string | null;
  enabled: boolean;
}

export interface AdminLanguagesResponse {
  languages: AdminLanguage[];
  default_language: string;
}

export interface LanguageCatalogItem {
  code: string;
  name: string;
  native_name?: string | null;
}

export interface LanguageCatalogResponse {
  languages: LanguageCatalogItem[];
}

export interface AddLanguagePayload {
  code: string;
  name: string;
  native_name?: string;
}

export interface ToggleLanguagePayload {
  enabled: boolean;
}

export interface SetDefaultLanguagePayload {
  code: string;
}
