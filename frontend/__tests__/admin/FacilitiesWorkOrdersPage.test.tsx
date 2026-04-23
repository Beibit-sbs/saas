import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import FacilitiesWorkOrdersPage from "../../app/(admin)/console/facilities-work-orders/page";

const useOrdersMock = vi.fn();
const useRequestsMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/facilities-work-orders/hooks", () => ({
  useWorkOrders: (...args: unknown[]) => useOrdersMock(...args),
  useMaintenanceRequests: (...args: unknown[]) => useRequestsMock(...args),
  useCreateWorkOrder: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateWorkOrderStatus: () => ({ mutate: vi.fn(), isPending: false }),
  useCreateMaintenanceRequest: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateMaintenanceRequestStatus: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/facilities-work-orders",
  useSearchParams: () => new URLSearchParams(),
}));

const SAMPLE_ORDER = {
  id: 1,
  tenant_id: "1",
  order_code: "WO-2026-001",
  facility_code: "FAC-001",
  title: "Repair HVAC unit",
  work_type: "repair",
  priority: "medium",
  assigned_to: "tech@example.com",
  status: "open",
};

const SAMPLE_REQUEST = {
  id: 1,
  tenant_id: "1",
  request_code: "MR-2026-001",
  facility_code: "FAC-002",
  issue_type: "hvac",
  severity: "medium",
  notes: "Heating not working",
  status: "pending",
};

describe("FacilitiesWorkOrdersPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useOrdersMock.mockReturnValue({
      data: { items: [SAMPLE_ORDER] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useRequestsMock.mockReturnValue({
      data: { items: [SAMPLE_REQUEST] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders page title", () => {
    render(<FacilitiesWorkOrdersPage />);
    expect(screen.getByText("Facilities & Work Orders")).toBeDefined();
  });

  it("renders work order row", () => {
    render(<FacilitiesWorkOrdersPage />);
    expect(screen.getByText("WO-2026-001")).toBeDefined();
  });

  it("renders maintenance request row", () => {
    render(<FacilitiesWorkOrdersPage />);
    expect(screen.getByText("MR-2026-001")).toBeDefined();
  });

  it("renders access denied when no permission", () => {
    allowAccess = false;
    render(<FacilitiesWorkOrdersPage />);
    expect(screen.getByText("Access Denied")).toBeDefined();
  });
});
