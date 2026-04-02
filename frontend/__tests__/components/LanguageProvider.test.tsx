import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AuthProvider } from "../../app/components/AuthProvider";
import { LanguageProvider, useLanguage } from "../../app/components/LanguageProvider";
import { LOCALE_COOKIE_KEY } from "../../shared/i18n/locale";

function LanguageConsumer() {
  const { language, supportedLanguages, t } = useLanguage();

  return (
    <div>
      <div data-testid="active-language">{language}</div>
      <div data-testid="language-count">{supportedLanguages.length}</div>
      <div data-testid="translation-ui-language">{t("ui.language")}</div>
      <div data-testid="translation-ui-apply">{t("ui.apply")}</div>
    </div>
  );
}

function SwitchLanguageConsumer() {
  const { language, setLanguage } = useLanguage();
  return (
    <div>
      <div data-testid="active-language-switch">{language}</div>
      <button type="button" onClick={() => setLanguage("en")}>
        Switch to en
      </button>
    </div>
  );
}

describe("LanguageProvider", () => {
  let runtimeLanguagesPayload: {
    languages: Array<{ code: string; name: string; native_name: string; enabled: boolean; system: boolean }>;
    default_language: string;
  };

  beforeEach(() => {
    localStorage.clear();
    document.cookie = `${LOCALE_COOKIE_KEY}=; Max-Age=0; Path=/`;
    document.documentElement.lang = "";
    vi.clearAllMocks();

    runtimeLanguagesPayload = {
      languages: [
        { code: "kk", name: "Kazakh", native_name: "Қазақша", enabled: true, system: true },
        { code: "ru", name: "Russian", native_name: "Русский", enabled: true, system: true },
        { code: "en", name: "English", native_name: "English", enabled: true, system: true },
      ],
      default_language: "ru",
    };

    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/api/auth/me/profile")) {
          return Promise.resolve(new Response(JSON.stringify({ detail: "unauthorized" }), { status: 401 }));
        }
        if (url.endsWith("/api/i18n/languages")) {
          return Promise.resolve(
            new Response(
              JSON.stringify(runtimeLanguagesPayload),
              { status: 200 },
            ),
          );
        }
        return Promise.resolve(new Response(JSON.stringify({}), { status: 200 }));
      }),
    );
  });

  it("should render children", () => {
    render(
      <AuthProvider>
        <LanguageProvider>
          <div data-testid="test-child">Test Content</div>
        </LanguageProvider>
      </AuthProvider>
    );

    expect(screen.getByTestId("test-child")).toBeInTheDocument();
  });

  it("should provide default supported languages", () => {
    render(
      <AuthProvider>
        <LanguageProvider>
          <LanguageConsumer />
        </LanguageProvider>
      </AuthProvider>
    );

    expect(screen.getByTestId("language-count")).toHaveTextContent("3");
  });

  it("should initialize language from localStorage if available", () => {
    localStorage.setItem("app.language", "en");

    render(
      <AuthProvider>
        <LanguageProvider>
          <LanguageConsumer />
        </LanguageProvider>
      </AuthProvider>
    );

    expect(screen.getByTestId("active-language")).toHaveTextContent("en");
  });

  it("uses admin default language when no saved locale exists", async () => {
    runtimeLanguagesPayload.default_language = "en";
    localStorage.clear();

    render(
      <AuthProvider>
        <LanguageProvider>
          <LanguageConsumer />
        </LanguageProvider>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("active-language")).toHaveTextContent("en");
    });
  });

  it("should persist selected language to localStorage and cookie", () => {
    render(
      <AuthProvider>
        <LanguageProvider>
          <SwitchLanguageConsumer />
        </LanguageProvider>
      </AuthProvider>
    );

    fireEvent.click(screen.getByText("Switch to en"));

    expect(screen.getByTestId("active-language-switch")).toHaveTextContent("en");
    expect(localStorage.getItem("app.language")).toBe("en");
    expect(document.documentElement.lang).toBe("en");
    expect(document.cookie).toContain("app.locale=en");
  });

  it("falls back to runtime default when saved locale becomes inactive", async () => {
    runtimeLanguagesPayload = {
      languages: [
        { code: "ru", name: "Russian", native_name: "Русский", enabled: true, system: true },
        { code: "en", name: "English", native_name: "English", enabled: true, system: true },
      ],
      default_language: "en",
    };
    localStorage.setItem("app.language", "kk");

    render(
      <AuthProvider>
        <LanguageProvider>
          <LanguageConsumer />
        </LanguageProvider>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("active-language")).toHaveTextContent("en");
    });
  });

  it("keeps ru/kk/en working via code dictionaries", async () => {
    localStorage.setItem("app.language", "kk");

    render(
      <AuthProvider>
        <LanguageProvider>
          <LanguageConsumer />
        </LanguageProvider>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("translation-ui-apply")).toHaveTextContent("Қолдану");
    });
  });

  it("does not crash when active language dictionary is missing", async () => {
    runtimeLanguagesPayload = {
      languages: [
        { code: "zh", name: "Chinese", native_name: "中文", enabled: true, system: false },
        { code: "ru", name: "Russian", native_name: "Русский", enabled: true, system: true },
        { code: "en", name: "English", native_name: "English", enabled: true, system: true },
      ],
      default_language: "zh",
    };
    localStorage.setItem("app.language", "zh");

    render(
      <AuthProvider>
        <LanguageProvider>
          <LanguageConsumer />
        </LanguageProvider>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("active-language")).toBeInTheDocument();
    });

    expect(screen.getByTestId("translation-ui-language")).toHaveTextContent("Язык");
  });
});
