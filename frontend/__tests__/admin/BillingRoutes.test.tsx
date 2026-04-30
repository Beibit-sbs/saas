import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import BillingIndexPage from "../../app/(admin)/console/billing/page";
import BillingPlansPage from "../../app/(admin)/console/billing/plans/page";
import BillingQuotasPage from "../../app/(admin)/console/billing/quotas/page";
import BillingUsagePage from "../../app/(admin)/console/billing/usage/page";

vi.mock("next/navigation", () => ({
  redirect: vi.fn(),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/console/billing",
}));

vi.mock("../../app/(admin)/console/platform/platform-section-view", () => ({
  PlatformSectionView: ({ section }: { section: string }) => <div>section:{section}</div>,
}));

// BillingIndexPage is a "use client" component — mock auth/permission hooks.
vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({ hasPermission: () => true }),
}));

vi.mock("../../shared/auth/context", () => ({
  useAdminAuth: () => ({
    user: { id: "1", login: "admin", roles: ["admin"], tenant_id: 1 },
    token: "test-token",
  }),
  AuthContext: { Provider: ({ children }: { children: React.ReactNode }) => children },
}));

describe("Billing routes", () => {
  it("renders /console/billing index page with billing content", () => {
    render(<BillingIndexPage />);
    // The billing index page renders its own dashboard UI (not a redirect).
    // Verify the page renders without crashing and contains billing-related text.
    expect(screen.getByText("Billing")).toBeInTheDocument();
  });

  it("maps /console/billing/plans to billing-plans section", () => {
    render(<BillingPlansPage />);
    expect(screen.getByText("section:billing-plans")).toBeInTheDocument();
  });

  it("maps /console/billing/quotas to usage-quotas section", () => {
    render(<BillingQuotasPage />);
    expect(screen.getByText("section:usage-quotas")).toBeInTheDocument();
  });

  it("maps /console/billing/usage to usage-quotas section", () => {
    render(<BillingUsagePage />);
    expect(screen.getByText("section:usage-quotas")).toBeInTheDocument();
  });
});
