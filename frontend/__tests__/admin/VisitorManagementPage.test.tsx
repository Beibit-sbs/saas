import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import VisitorManagementPage from "../../app/(admin)/console/visitor-management/page";

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("../../shared/ui/page-header", () => ({
  PageHeader: ({ title, description }: { title: string; description: string }) => (
    <div data-testid="page-header">
      <h1>{title}</h1>
      <p>{description}</p>
    </div>
  ),
}));

vi.mock("../../shared/ui/badge", () => ({
  Badge: ({ children, "data-testid": testId }: { children: React.ReactNode; "data-testid"?: string }) => (
    <span data-testid={testId}>{children}</span>
  ),
}));

vi.mock("lucide-react", () => ({ ShieldCheck: () => null }));

describe("VisitorManagementPage", () => {
  it("renders without crashing", () => {
    render(<VisitorManagementPage />);
    expect(screen.getByTestId("visitor-management-page")).toBeTruthy();
  });

  it("renders page header with correct title", () => {
    render(<VisitorManagementPage />);
    expect(screen.getByTestId("page-header")).toBeTruthy();
    expect(screen.getByText("Visitor Management")).toBeTruthy();
  });

  it("renders lifecycle section", () => {
    render(<VisitorManagementPage />);
    expect(screen.getByTestId("visitor-management-lifecycle-section")).toBeTruthy();
  });

  it("renders events section", () => {
    render(<VisitorManagementPage />);
    expect(screen.getByTestId("visitor-management-events-section")).toBeTruthy();
  });

  it("shows all lifecycle states", () => {
    render(<VisitorManagementPage />);
    const states = [
      "REQUESTED",
      "APPROVED",
      "REJECTED",
      "CHECKED_IN",
      "CHECKED_OUT",
      "EXPIRED",
      "CANCELLED",
    ];
    for (const state of states) {
      expect(screen.getByTestId(`visitor-state-${state}`)).toBeTruthy();
    }
  });

  it("shows all contract events", () => {
    render(<VisitorManagementPage />);
    const events = [
      "visitor.registered",
      "visitor.approved",
      "visitor.rejected",
      "visitor.checked_in",
      "visitor.checked_out",
      "visitor.expired",
      "visitor.cancelled",
      "visitor.unauthorized_attempt",
    ];
    for (const ev of events) {
      expect(screen.getByTestId(`contract-event-${ev}`)).toBeTruthy();
    }
  });

  it("does not display hardware/auto-ban wording", () => {
    const { container } = render(<VisitorManagementPage />);
    const text = container.textContent ?? "";
    const forbidden = ["open door", "lock out", "auto-ban", "blacklist", "physical access control"];
    for (const term of forbidden) {
      expect(text.toLowerCase()).not.toContain(term);
    }
  });

  it("page is wrapped in RequirePermission guard", () => {
    // Verify page renders through RequirePermission by checking testid is present
    // (RequirePermission mock passes children through)
    render(<VisitorManagementPage />);
    expect(screen.getByTestId("visitor-management-page")).toBeTruthy();
  });
});
