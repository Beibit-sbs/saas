import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import EventsManagementPage from "../../app/(admin)/console/events-management/page";

let allowAccess = true;

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
}));

vi.mock("../../shared/ui/page-header", () => ({
  PageHeader: ({ title, description }: { title: string; description?: string }) => (
    <div>
      <h1>{title}</h1>
      {description ? <p>{description}</p> : null}
    </div>
  ),
}));

vi.mock("../../shared/ui/badge", () => ({
  Badge: ({ children, ...props }: { children: React.ReactNode }) => <span {...props}>{children}</span>,
}));

describe("EventsManagementPage", () => {
  beforeEach(() => {
    allowAccess = true;
    vi.clearAllMocks();
  });

  it("renders lifecycle and contracted event sections", () => {
    render(<EventsManagementPage />);

    expect(screen.getByTestId("events-management-page")).toBeInTheDocument();
    expect(screen.getByText("Events Management")).toBeInTheDocument();
    expect(screen.getByTestId("events-management-lifecycle-section")).toBeInTheDocument();
    expect(screen.getByTestId("events-management-events-section")).toBeInTheDocument();

    expect(screen.getByTestId("event-state-DRAFT")).toBeInTheDocument();
    expect(screen.getByTestId("event-state-COMPLETED")).toBeInTheDocument();
    expect(screen.getByTestId("contract-event-event.published")).toBeInTheDocument();
    expect(screen.getByTestId("contract-event-event.cancelled")).toBeInTheDocument();
  });

  it("renders access denied when permission gate blocks", () => {
    allowAccess = false;
    render(<EventsManagementPage />);

    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
