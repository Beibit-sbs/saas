import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import DelinquencyCollectionsPage from "../../app/(admin)/console/delinquency-collections/page";

const useRecordsMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/platform/kpi/wave1-kpi-bar", () => ({
  Wave1KpiBar: () => <div data-testid="wave1-kpi-bar-mock" />,
}));

vi.mock("../../modules/delinquency-collections/hooks", () => ({
  useDelinquencyRecords: (...args: unknown[]) => useRecordsMock(...args),
  useCreateDelinquencyRecord: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateDelinquencyStatus: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateDelinquencyEscalation: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode; permission: string }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
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
  usePathname: () => "/console/delinquency-collections",
  useSearchParams: () => new URLSearchParams(),
}));

const SAMPLE = {
  id: 1,
  tenant_id: "1",
  student_id: "STU-001",
  invoice_code: "INV-2026-009",
  amount_due: 2500,
  days_overdue: 45,
  escalation_stage: "stage_1",
  status: "open",
};

describe("DelinquencyCollectionsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useRecordsMock.mockReturnValue({
      data: { items: [SAMPLE] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders page heading", () => {
    render(<DelinquencyCollectionsPage />);
    expect(screen.getByText(/Delinquency & Collections/i)).toBeInTheDocument();
  });

  it("renders record row", () => {
    render(<DelinquencyCollectionsPage />);
    expect(screen.getByText("STU-001")).toBeInTheDocument();
    expect(screen.getByText("INV-2026-009")).toBeInTheDocument();
    expect(screen.getByText("45")).toBeInTheDocument();
  });

  it("renders create form", () => {
    render(<DelinquencyCollectionsPage />);
    expect(screen.getByLabelText(/Student ID/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Invoice Code/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Amount Due/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Days Overdue/i)).toBeInTheDocument();
  });

  it("shows access denied", () => {
    allowAccess = false;
    render(<DelinquencyCollectionsPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
