import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import BillingIndexPage from "../../app/(admin)/console/billing/page";
import BillingPlansPage from "../../app/(admin)/console/billing/plans/page";
import BillingQuotasPage from "../../app/(admin)/console/billing/quotas/page";
import BillingUsagePage from "../../app/(admin)/console/billing/usage/page";

const redirectMock = vi.fn();

vi.mock("next/navigation", () => ({
  redirect: (url: string) => redirectMock(url),
}));

vi.mock("../../app/(admin)/console/platform/platform-section-view", () => ({
  PlatformSectionView: ({ section }: { section: string }) => <div>section:{section}</div>,
}));

describe("Billing routes", () => {
  it("redirects /console/billing to plans", () => {
    BillingIndexPage();
    expect(redirectMock).toHaveBeenCalledWith("/console/billing/plans");
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
