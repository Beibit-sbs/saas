import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
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
  });

  it("should render children", () => {
    render(
      <LanguageProvider>
        <div data-testid="test-child">Test Content</div>
      </LanguageProvider>
    );

    expect(screen.getByTestId("test-child")).toBeInTheDocument();
  });

  it("should provide default supported languages", () => {
    render(
      <LanguageProvider>
        <LanguageConsumer />
      </LanguageProvider>
    );

    expect(screen.getByTestId("language-count")).toHaveTextContent("3");
  });

  it("should initialize language from localStorage if available", () => {
    localStorage.setItem("app.language", "en");

    render(
      <LanguageProvider>
        <LanguageConsumer />
      </LanguageProvider>
    );

    expect(screen.getByTestId("active-language")).toHaveTextContent("en");
  });

  it("should default to ru language if localStorage is empty", () => {
    localStorage.clear();

    render(
      <LanguageProvider>
        <LanguageConsumer />
      </LanguageProvider>
    );

    expect(screen.getByTestId("active-language")).toHaveTextContent("ru");
  });
});
