import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import SecurityOperationsPage from "../../app/(admin)/console/security-operations/page";

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

vi.mock("lucide-react", () => ({ AlertTriangle: () => null }));

describe("SecurityOperationsPage", () => {
  it("renders without crashing", () => {
    render(<SecurityOperationsPage />);
    expect(screen.getByTestId("security-operations-page")).toBeTruthy();
  });

  it("renders page header and sections", () => {
    render(<SecurityOperationsPage />);
    expect(screen.getByText("Security Operations")).toBeTruthy();
    expect(screen.getByTestId("security-operations-lifecycle-section")).toBeTruthy();
    expect(screen.getByTestId("security-operations-events-section")).toBeTruthy();
  });

  it("shows expected incident lifecycle states", () => {
    render(<SecurityOperationsPage />);
    for (const state of ["OPEN", "ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "ESCALATED", "DISMISSED"]) {
      expect(screen.getByTestId(`incident-state-${state}`)).toBeTruthy();
    }
  });

  it("shows expected contract events", () => {
    render(<SecurityOperationsPage />);
    for (const ev of [
      "security.incident.opened",
      "security.incident.acknowledged",
      "security.incident.escalated",
      "security.incident.resolved",
      "security.incident.dismissed",
      "campus.security_incident.detected",
    ]) {
      expect(screen.getByTestId(`contract-event-${ev}`)).toBeTruthy();
    }
  });

  it("does not include hardware control or auto-punitive wording", () => {
    const { container } = render(<SecurityOperationsPage />);
    const text = (container.textContent ?? "").toLowerCase();
    for (const forbidden of ["open door", "hardware", "physical access control", "lockout", "blacklist", "auto-ban", "punish"]) {
      expect(text).not.toContain(forbidden);
    }
  });
});
