/**
 * A-015.6 Wave 3 KPI frontend tests.
 * Covers: BudgetPlanningPage, ProcurementWorkflowPage, AssetInventoryPage, and
 * the dashboard Wave3 section each render Wave1KpiBar with the correct metric keys.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

// ─── shared mock helpers ────────────────────────────────────────────────────

vi.mock("../../modules/platform/kpi/wave1-kpi-bar", () => ({
  Wave1KpiBar: ({ metricKeys, labels }: { metricKeys: string[]; labels: Record<string, string> }) => (
    <div data-testid="wave3-kpi-bar-mock" data-keys={metricKeys.join(",")} />
  ),
}));

vi.mock("../../shared/auth/context", () => ({
  useAdminAuth: () => ({ user: { tenantId: 1, roles: ["admin"], permissions: [] } }),
}));

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: () => true,
    hasAnyPermission: () => true,
    roles: ["admin"],
  }),
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({ t: (k: string) => k }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("../../shared/auth/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("../../shared/hooks/use-mutation-feedback", () => ({
  useMutationFeedback: () => ({ getHandlers: () => ({ onSuccess: vi.fn(), onError: vi.fn() }) }),
}));

// ─── BudgetPlanningPage ─────────────────────────────────────────────────────

vi.mock("../../modules/budget-planning/hooks", () => ({
  useBudgetDashboardSummary: () => ({
    data: {
      total_budget: 0,
      total_allocated: 0,
      total_spent: 0,
      total_overrun: 0,
      variance_pct: 0,
    },
    isLoading: false,
    isError: false,
  }),
  useBudgetsList: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
    refetch: vi.fn(),
  }),
}));

import BudgetPlanningPage from "../../app/(admin)/console/budget-planning/page";

describe("BudgetPlanningPage Wave3 KPI wiring", () => {
  it("renders Wave1KpiBar with budget overrun metric keys", () => {
    render(<BudgetPlanningPage />);
    const bar = screen.getByTestId("wave3-kpi-bar-mock");
    expect(bar).toBeInTheDocument();
    const keys = bar.getAttribute("data-keys") ?? "";
    expect(keys).toContain("budget_overrun_risk_count");
    expect(keys).toContain("budget_overrun_amount_at_risk");
    expect(keys).toContain("budget_review_actions_count");
  });
});

// ─── ProcurementWorkflowPage ─────────────────────────────────────────────────

vi.mock("../../modules/procurement-workflow/hooks", () => ({
  useProcurementDashboardSummary: () => ({
    data: {
      total_requests: 0,
      total_pending_approvals: 0,
      total_ordered_value: 0,
      total_approved: 0,
      total_po_issued: 0,
    },
    isLoading: false,
    isError: false,
  }),
  useProcurementList: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
  }),
}));

import ProcurementWorkflowPage from "../../app/(admin)/console/procurement-workflow/page";

describe("ProcurementWorkflowPage Wave3 KPI wiring", () => {
  it("renders Wave1KpiBar with procurement metric keys", () => {
    render(<ProcurementWorkflowPage />);
    const bar = screen.getByTestId("wave3-kpi-bar-mock");
    expect(bar).toBeInTheDocument();
    const keys = bar.getAttribute("data-keys") ?? "";
    expect(keys).toContain("procurement_requests_pending_approval");
    expect(keys).toContain("procurement_approval_automation_count");
    expect(keys).toContain("procurement_po_issued_count");
  });
});

// ─── AssetInventoryPage ──────────────────────────────────────────────────────

vi.mock("../../modules/asset-inventory/hooks", () => ({
  useAssetItems: () => ({ data: { items: [], total: 0 }, isLoading: false, isError: false }),
  useCreateAssetItem: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateAssetItemStatus: () => ({ mutate: vi.fn(), isPending: false }),
  useDepreciationRecords: () => ({ data: { items: [], total: 0 }, isLoading: false }),
  useCreateDepreciationRecord: () => ({ mutate: vi.fn(), isPending: false }),
}));

import AssetInventoryPage from "../../app/(admin)/console/asset-inventory/page";

describe("AssetInventoryPage Wave3 KPI wiring", () => {
  it("renders Wave1KpiBar with PO/delivery/asset and supply metric keys", () => {
    render(<AssetInventoryPage />);
    const bar = screen.getByTestId("wave3-kpi-bar-mock");
    expect(bar).toBeInTheDocument();
    const keys = bar.getAttribute("data-keys") ?? "";
    expect(keys).toContain("po_delivery_completion_rate");
    expect(keys).toContain("delivered_po_asset_conversion_rate");
    expect(keys).toContain("asset_conversion_gap_count");
    expect(keys).toContain("inventory_low_stock_items_count");
    expect(keys).toContain("critical_supply_risk_count");
    expect(keys).toContain("reorder_recommendations_count");
    expect(keys).toContain("supply_risk_actions_count");
  });
});
