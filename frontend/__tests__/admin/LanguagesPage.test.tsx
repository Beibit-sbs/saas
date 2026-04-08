import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import LanguagesPage from "../../app/(admin)/console/languages/page";

let allowAccess = true;

const useAdminLanguagesMock = vi.fn();
const useLanguageCatalogMock = vi.fn();

vi.mock("../../modules/i18n-admin/hooks", () => ({
  useAdminLanguages: (...args: unknown[]) => useAdminLanguagesMock(...args),
  useLanguageCatalog: (...args: unknown[]) => useLanguageCatalogMock(...args),
  useAddLanguage: () => ({ mutate: vi.fn(), isPending: false }),
  useSetDefaultLanguage: () => ({ mutate: vi.fn(), isPending: false }),
  useToggleLanguage: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteLanguage: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  PermissionGate: ({ children }: { children: React.ReactNode }) =>
    allowAccess ? <>{children}</> : null,
  RequirePermission: ({ children }: { children: React.ReactNode; permission: string }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
  AccessDenied: ({ message }: { message?: string }) => (
    <div>{message ?? "Access Denied"}</div>
  ),
}));

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: () => allowAccess,
    hasAnyPermission: () => allowAccess,
    roles: allowAccess ? ["admin"] : [],
  }),
}));

vi.mock("../../shared/hooks/use-mutation-feedback", () => ({
  useMutationFeedback: () => ({
    getHandlers: () => ({ onSuccess: vi.fn(), onError: vi.fn() }),
  }),
}));

vi.mock("../../app/components/LanguageProvider", async () => {
  const { en: commonEn } = await import("../../i18n/common/en");
  const { en: adminEn } = await import("../../i18n/admin/en");
  const dict = { ...commonEn, ...adminEn } as Record<string, string>;

  return {
    useLanguage: () => ({
      t: (key: string) => dict[key] ?? key,
    }),
  };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
  usePathname: () => "/console/languages",
  useSearchParams: () => new URLSearchParams(),
}));

describe("LanguagesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useAdminLanguagesMock.mockReturnValue({
      data: {
        languages: [
          { code: "en", name: "English", native_name: "English", enabled: true },
          { code: "ru", name: "Russian", native_name: "Русский", enabled: true },
        ],
        default_language: "en",
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useLanguageCatalogMock.mockReturnValue({
      data: {
        languages: [
          { code: "en", name: "English", native_name: "English" },
          { code: "ru", name: "Russian", native_name: "Русский" },
          { code: "kk", name: "Kazakh", native_name: "Қазақша" },
        ],
      },
      isLoading: false,
      error: null,
    });
  });

  it("renders languages page and rows", () => {
    render(<LanguagesPage />);
    expect(screen.getByTestId("languages-page")).toBeInTheDocument();
    expect(screen.getAllByText("English").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Russian").length).toBeGreaterThanOrEqual(1);
  });

  it("shows language catalog and default selectors", () => {
    render(<LanguagesPage />);
    expect(screen.getByText("Language catalog")).toBeInTheDocument();
    expect(screen.getAllByText("Set default language").length).toBeGreaterThanOrEqual(1);
  });

  it("shows empty state when no languages are configured", () => {
    useAdminLanguagesMock.mockReturnValue({
      data: { languages: [], default_language: "" },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useLanguageCatalogMock.mockReturnValue({
      data: { languages: [] },
      isLoading: false,
      error: null,
    });

    render(<LanguagesPage />);
    expect(screen.getByText(/No languages found for this query\./i)).toBeInTheDocument();
  });

  it("shows access denied when read permission is missing", () => {
    allowAccess = false;
    render(<LanguagesPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
