import { describe, it, expect, beforeEach, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { AuthProvider } from "../../app/components/AuthProvider";
import { LanguageProvider, useLanguage } from "../../app/components/LanguageProvider";
import LanguageSwitcher from "../../app/components/LanguageSwitcher";

function LangProbe() {
  const { language } = useLanguage();
  return <div data-testid="probe-language">{language}</div>;
}

describe("LanguageSwitcher", () => {
  let runtimeLanguagesPayload: {
    languages: Array<{ code: string; name: string; native_name: string; enabled: boolean; system: boolean }>;
    default_language: string;
  };

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();

    runtimeLanguagesPayload = {
      languages: [
        { code: "ru", name: "Russian", native_name: "Русский", enabled: true, system: true },
        { code: "kk", name: "Kazakh", native_name: "Қазақша", enabled: true, system: true },
        { code: "en", name: "English", native_name: "English", enabled: true, system: true },
      ],
      default_language: "ru",
    };

    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
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

  it("switches locale after apply", () => {
    render(
      <AuthProvider>
        <LanguageProvider>
          <LanguageSwitcher variant="inline" />
          <LangProbe />
        </LanguageProvider>
      </AuthProvider>,
    );

    const select = screen.getByRole("combobox") as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "en" } });
    fireEvent.click(screen.getByRole("button", { name: /(apply|применить)/i }));

    expect(screen.getByTestId("probe-language")).toHaveTextContent("en");
  });

  it("hides disabled language from switcher options", async () => {
    runtimeLanguagesPayload = {
      languages: [
        { code: "ru", name: "Russian", native_name: "Русский", enabled: true, system: true },
        { code: "kk", name: "Kazakh", native_name: "Қазақша", enabled: false, system: true },
        { code: "en", name: "English", native_name: "English", enabled: true, system: true },
      ],
      default_language: "ru",
    };

    render(
      <AuthProvider>
        <LanguageProvider>
          <LanguageSwitcher variant="inline" />
        </LanguageProvider>
      </AuthProvider>,
    );

    await waitFor(() => {
      const options = Array.from(screen.getAllByRole("option")).map((item) => item.textContent || "");
      expect(options).toContain("Русский");
      expect(options).toContain("English");
      expect(options).not.toContain("Қазақша");
    });
  });
});
