import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import HrPayrollPage from "../../app/(admin)/console/hr-payroll/page";

const useEmployeesMock = vi.fn();
const useCyclesMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/hr-payroll/hooks", () => ({
  useHrEmployees: (...args: unknown[]) => useEmployeesMock(...args),
  usePayrollCycles: (...args: unknown[]) => useCyclesMock(...args),
  useCreateHrEmployee: () => ({ mutate: vi.fn(), isPending: false }),
  useCreatePayrollCycle: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateHrEmployeeStatus: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdatePayrollCycleStatus: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/hr-payroll",
  useSearchParams: () => new URLSearchParams(),
}));

const EMPLOYEE = {
  id: 1,
  tenant_id: "1",
  employee_code: "EMP-001",
  full_name: "John Smith",
  department_id: "DEPT-HR",
  role_title: "HR Partner",
  status: "active",
};

const CYCLE = {
  id: 1,
  tenant_id: "1",
  cycle_code: "PAY-2026-05",
  period_label: "May 2026",
  total_gross: 100000,
  total_net: 75000,
  employee_count: 42,
  status: "processing",
};

describe("HrPayrollPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;

    useEmployeesMock.mockReturnValue({
      data: { items: [EMPLOYEE] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    useCyclesMock.mockReturnValue({
      data: { items: [CYCLE] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders page heading", () => {
    render(<HrPayrollPage />);
    expect(screen.getByText(/HR & Payroll/i)).toBeInTheDocument();
  });

  it("renders employee and cycle rows", () => {
    render(<HrPayrollPage />);
    expect(screen.getByText("EMP-001")).toBeInTheDocument();
    expect(screen.getByText("John Smith")).toBeInTheDocument();
    expect(screen.getByText("PAY-2026-05")).toBeInTheDocument();
    expect(screen.getByText("May 2026")).toBeInTheDocument();
  });

  it("renders employee and cycle forms", () => {
    render(<HrPayrollPage />);
    expect(screen.getByLabelText(/Employee Code/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Full Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Cycle Code/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Employee Count/i)).toBeInTheDocument();
  });

  it("shows access denied", () => {
    allowAccess = false;
    render(<HrPayrollPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
