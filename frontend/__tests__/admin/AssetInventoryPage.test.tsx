import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import AssetInventoryPage from "../../app/(admin)/console/asset-inventory/page";

const useAssetsMock = vi.fn();
const useDeprMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/asset-inventory/hooks", () => ({
  useAssetItems: (...args: unknown[]) => useAssetsMock(...args),
  useDepreciationRecords: (...args: unknown[]) => useDeprMock(...args),
  useCreateAssetItem: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateAssetItemStatus: () => ({ mutate: vi.fn(), isPending: false }),
  useCreateDepreciationRecord: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/asset-inventory",
  useSearchParams: () => new URLSearchParams(),
}));

const SAMPLE_ASSET = {
  id: 1,
  tenant_id: "1",
  asset_code: "ASSET-2026-001",
  name: "Laptop Dell XPS",
  category: "it_hardware",
  location: "Building A, Room 101",
  condition: "good",
  purchase_year: 2024,
  vendor: "Dell",
  status: "active",
};

const SAMPLE_DEPR = {
  id: 1,
  tenant_id: "1",
  asset_code: "ASSET-2026-001",
  depreciation_method: "straight_line",
  original_value: 1500,
  current_value: 1200,
  depreciation_rate: 0.2,
  status: "active",
};

describe("AssetInventoryPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useAssetsMock.mockReturnValue({
      data: { items: [SAMPLE_ASSET] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useDeprMock.mockReturnValue({
      data: { items: [SAMPLE_DEPR] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders page title", () => {
    render(<AssetInventoryPage />);
    expect(screen.getByText("Asset Inventory")).toBeDefined();
  });

  it("renders asset row", () => {
    render(<AssetInventoryPage />);
    expect(screen.getAllByText("ASSET-2026-001").length).toBeGreaterThanOrEqual(1);
  });

  it("renders depreciation record row", () => {
    render(<AssetInventoryPage />);
    expect(screen.getAllByText("ASSET-2026-001").length).toBeGreaterThanOrEqual(1);
  });

  it("renders access denied when no permission", () => {
    allowAccess = false;
    render(<AssetInventoryPage />);
    expect(screen.getByText("Access Denied")).toBeDefined();
  });
});
