import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import AccessControlPage from "../../app/(admin)/console/access-control/page";

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

vi.mock("lucide-react", () => ({ KeyRound: () => null }));

describe("AccessControlPage", () => {
  it("renders without crashing", () => {
    render(<AccessControlPage />);
    expect(screen.getByTestId("access-control-page")).toBeTruthy();
  });

  it("renders page header", () => {
    render(<AccessControlPage />);
    expect(screen.getByText("Access Control")).toBeTruthy();
  });

  it("renders lifecycle and events sections", () => {
    render(<AccessControlPage />);
    expect(screen.getByTestId("access-control-lifecycle-section")).toBeTruthy();
    expect(screen.getByTestId("access-control-events-section")).toBeTruthy();
  });

  it("shows all card lifecycle states", () => {
    render(<AccessControlPage />);
    for (const state of ["ACTIVE", "SUSPENDED", "REVOKED"]) {
      expect(screen.getByTestId(`card-state-${state}`)).toBeTruthy();
    }
  });

  it("shows all access-control contract events", () => {
    render(<AccessControlPage />);
    for (const ev of [
      "access.granted",
      "access.denied",
      "card.issued",
      "card.suspended",
      "card.revoked",
      "card.reactivated",
      "security.anomaly",
    ]) {
      expect(screen.getByTestId(`contract-event-${ev}`)).toBeTruthy();
    }
  });

  it("does not include destructive or hardware-control wording", () => {
    const { container } = render(<AccessControlPage />);
    const text = (container.textContent ?? "").toLowerCase();
    for (const forbidden of ["open door", "physical door", "hardware acs", "lockout", "ban", "blacklist", "punish"]) {
      expect(text).not.toContain(forbidden);
    }
  });
});
