import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AuthProvider } from "../../app/components/AuthProvider";
import { LanguageProvider, useLanguage } from "../../app/components/LanguageProvider";

function LanguageConsumer() {
  const { language, supportedLanguages } = useLanguage();

  return (
    <div>
      <div data-testid="active-language">{language}</div>
      <div data-testid="language-count">{supportedLanguages.length}</div>
    </div>
  );
}

describe("LanguageProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
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
              JSON.stringify({
                languages: [
                  { code: "kk", name: "Kazakh", native_name: "Қазақша", enabled: true, system: true },
                  { code: "ru", name: "Russian", native_name: "Русский", enabled: true, system: true },
                  { code: "en", name: "English", native_name: "English", enabled: true, system: true },
                ],
              }),
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

  it("should default to ru language if localStorage is empty", () => {
    localStorage.clear();

    render(
      <AuthProvider>
        <LanguageProvider>
          <LanguageConsumer />
        </LanguageProvider>
      </AuthProvider>
    );

    expect(screen.getByTestId("active-language")).toHaveTextContent("ru");
  });
});
