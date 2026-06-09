import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import IntegrationsPage from "../../app/(admin)/console/integrations/page";
import IntegrationProviderReadinessPage from "../../app/(admin)/console/integrations/provider-readiness/page";

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: ReactNode }) => <>{children}</>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

describe("Integrations provider readiness pages", () => {
  it("renders integrations root with provider readiness inventory sections", () => {
    render(<IntegrationsPage />);

    expect(screen.getByTestId("integrations-root-page")).toBeInTheDocument();
    expect(screen.getByTestId("integrations-provider-readiness-card")).toBeInTheDocument();
    expect(screen.getByTestId("integrations-boundary-labels")).toBeInTheDocument();
    expect(screen.getByTestId("integrations-workflow-sections")).toBeInTheDocument();
    expect(screen.getByTestId("integrations-dashboard-cards")).toBeInTheDocument();
    expect(screen.getByTestId("integrations-navigation-visibility")).toBeInTheDocument();
    expect(screen.getByTestId("integrations-empty-state")).toBeInTheDocument();
  });

  it("renders dedicated provider readiness shell with boundaries and readiness indicators", () => {
    render(<IntegrationProviderReadinessPage />);

    expect(screen.getByTestId("ipr-page-shell")).toBeInTheDocument();
    expect(screen.getByText("Integration / Provider Readiness")).toBeInTheDocument();
    expect(screen.getByTestId("ipr-boundary-labels")).toBeInTheDocument();
    expect(screen.getByTestId("ipr-workflow-sections")).toBeInTheDocument();
    expect(screen.getByTestId("ipr-dashboard-cards")).toBeInTheDocument();
    expect(screen.getByTestId("ipr-readiness-indicators")).toBeInTheDocument();
    expect(screen.getByTestId("ipr-empty-state")).toBeInTheDocument();
  });
});
