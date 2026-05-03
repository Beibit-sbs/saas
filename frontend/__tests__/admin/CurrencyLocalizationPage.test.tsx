import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import CurrencyLocalizationPage from "../../app/(admin)/console/currency-localization/page";

let allowAccess = true;

const useTenantLocaleMock = vi.fn();
const setTenantLocaleMutate = vi.fn();
const upsertExchangeRateMutate = vi.fn();
const convertAmountMutate = vi.fn();
const formatMoneyMutate = vi.fn();

vi.mock("../../modules/currency-localization/hooks", () => ({
  useTenantLocale: (...args: unknown[]) => useTenantLocaleMock(...args),
  useSetTenantLocale: () => ({ mutate: setTenantLocaleMutate, isPending: false }),
  useUpsertExchangeRate: () => ({ mutate: upsertExchangeRateMutate, isPending: false, data: null }),
  useConvertAmount: () => ({
    mutate: convertAmountMutate,
    isPending: false,
    data: {
      tenant_id: 1,
      from_currency: "USD",
      to_currency: "KZT",
      amount: 10,
      converted_amount: 5000,
      formatted_converted_amount: "KZT 5000.00",
    },
  }),
  useFormatMoneyPreview: () => ({
    mutate: formatMoneyMutate,
    isPending: false,
    data: {
      amount: 10,
      currency_code: "USD",
      formatted: "$10.00",
    },
  }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  PermissionGate: ({ children }: { children: React.ReactNode }) =>
    allowAccess ? <>{children}</> : null,
  RequirePermission: ({ children }: { children: React.ReactNode; permission: string }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../shared/hooks/use-mutation-feedback", () => ({
  useMutationFeedback: () => ({
    getHandlers: () => ({ onSuccess: vi.fn(), onError: vi.fn() }),
  }),
}));

describe("CurrencyLocalizationPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useTenantLocaleMock.mockReturnValue({
      data: {
        profile_id: 7,
        tenant_id: 1,
        currency_code: "KZT",
        language_code: "kk",
        timezone: "Asia/Almaty",
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders the currency localization page with loaded locale", () => {
    render(<CurrencyLocalizationPage />);

    expect(screen.getByTestId("currency-localization-page")).toBeInTheDocument();
    expect(screen.getByLabelText("Preferred currency")).toHaveValue("KZT");
    expect(screen.getByLabelText("Preferred language")).toHaveValue("kk");
    expect(screen.getByText(/Active profile: KZT \/ kk \/ Asia\/Almaty/i)).toBeInTheDocument();
  });

  it("shows empty locale message when tenant is not configured", () => {
    useTenantLocaleMock.mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<CurrencyLocalizationPage />);
    expect(screen.getByText(/No tenant locale profile configured yet/i)).toBeInTheDocument();
  });

  it("submits locale and conversion actions", () => {
    render(<CurrencyLocalizationPage />);

    fireEvent.change(screen.getByLabelText("Preferred currency"), { target: { value: "USD" } });
    fireEvent.change(screen.getByLabelText("Preferred language"), { target: { value: "en" } });
    fireEvent.click(screen.getByRole("button", { name: "Save tenant locale" }));
    fireEvent.click(screen.getByRole("button", { name: "Convert amount" }));

    expect(setTenantLocaleMutate).toHaveBeenCalledWith(
      {
        tenant_id: 1,
        currency_code: "USD",
        language_code: "en",
        timezone: "Asia/Almaty",
      },
      expect.any(Object),
    );
    expect(convertAmountMutate).toHaveBeenCalledWith(
      {
        tenant_id: 1,
        amount: 10,
        from_currency: "USD",
        to_currency: "KZT",
      },
      expect.any(Object),
    );
  });

  it("submits exchange rate and formatting actions", () => {
    render(<CurrencyLocalizationPage />);

    fireEvent.change(screen.getByLabelText("Rate"), { target: { value: "510" } });
    fireEvent.change(screen.getByLabelText("Preview currency"), { target: { value: "EUR" } });
    fireEvent.click(screen.getByRole("button", { name: "Save exchange rate" }));
    fireEvent.click(screen.getByRole("button", { name: "Format amount" }));

    expect(upsertExchangeRateMutate).toHaveBeenCalledWith(
      {
        tenant_id: 1,
        base_currency: "USD",
        quote_currency: "KZT",
        rate: 510,
      },
      expect.any(Object),
    );
    expect(formatMoneyMutate).toHaveBeenCalledWith(
      {
        amount: 10,
        currency_code: "EUR",
      },
      expect.any(Object),
    );
  });

  it("shows access denied when permission is missing", () => {
    allowAccess = false;
    render(<CurrencyLocalizationPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});