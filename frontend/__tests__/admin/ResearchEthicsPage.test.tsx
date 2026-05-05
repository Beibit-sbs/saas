import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import ResearchEthicsPage from "../../app/(admin)/console/research-ethics/page";
import { ApiRequestError } from "../../shared/api/client";

const useResearchEthicsReviewsMock = vi.fn();
const useResearchEthicsBrainContextMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/platform/kpi/wave1-kpi-bar", () => ({
  Wave1KpiBar: ({ metricKeys }: { metricKeys: string[] }) => (
    <div data-testid="wave1-kpi-bar-mock" data-keys={metricKeys.join(",")} />
  ),
}));

vi.mock("../../modules/research-ethics/hooks", () => ({
  useResearchEthicsReviews: (...args: unknown[]) => useResearchEthicsReviewsMock(...args),
  useResearchEthicsBrainContext: (...args: unknown[]) => useResearchEthicsBrainContextMock(...args),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../shared/ui/page-header", () => ({
  PageHeader: ({ title, description }: { title: string; description?: string }) => (
    <div>
      <h1>{title}</h1>
      {description ? <p>{description}</p> : null}
    </div>
  ),
}));

vi.mock("../../shared/ui/page-states", () => ({
  LoadingState: ({ title, message }: { title?: string; message?: string }) => (
    <div>{title}::{message}</div>
  ),
  ErrorState: ({ title, message }: { title?: string; message?: string }) => (
    <div>{title}::{message}</div>
  ),
}));

vi.mock("../../shared/ui/empty-state", () => ({
  EmptyState: ({ title, description }: { title?: string; description?: string }) => (
    <div>{title}::{description}</div>
  ),
}));

vi.mock("../../shared/ui/badge", () => ({
  Badge: ({ children, variant, ...props }: { children: React.ReactNode; variant?: string }) => (
    <div data-variant={variant} {...props}>{children}</div>
  ),
}));

describe("ResearchEthicsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;

    useResearchEthicsReviewsMock.mockReturnValue({
      data: {
        records: [
          {
            id: 101,
            tenant_id: 1,
            review_code: "IRB-101",
            project_title: "Human Subjects Study",
            principal_investigator_id: "FAC-101",
            review_type: "irb",
            status: "under_review",
            risk_level: "high",
            submission_date: "2026-05-01T00:00:00Z",
            decision_date: null,
            committee_name: "Central IRB",
            notes: null,
            integration_source: null,
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    useResearchEthicsBrainContextMock.mockReturnValue({
      data: {
        module: "research_ethics",
        tenant_id: 1,
        total_reviews: 4,
        pending_reviews: 1,
        approved_reviews: 2,
        rejected_reviews: 0,
        high_risk_reviews: 1,
        compliance_status: "under_review",
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders title, KPI bar, and base layout", () => {
    render(<ResearchEthicsPage />);
    expect(screen.getByTestId("research-ethics-page")).toBeInTheDocument();
    expect(screen.getByText("Research Ethics")).toBeInTheDocument();
    const bar = screen.getByTestId("wave1-kpi-bar-mock");
    expect(bar).toBeInTheDocument();
    expect(bar.getAttribute("data-keys")).toContain("research_ethics_review_cases_count");
    expect(bar.getAttribute("data-keys")).toContain("research_ethics_requires_approval_count");
  });

  it("renders loading state safely", () => {
    useResearchEthicsReviewsMock.mockReturnValueOnce({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });
    useResearchEthicsBrainContextMock.mockReturnValueOnce({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });

    render(<ResearchEthicsPage />);
    expect(screen.getByText(/Loading research ethics/)).toBeInTheDocument();
  });

  it("renders empty state safely", () => {
    useResearchEthicsReviewsMock.mockReturnValueOnce({
      data: { records: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<ResearchEthicsPage />);
    expect(screen.getByText(/No research ethics reviews found/)).toBeInTheDocument();
  });

  it("renders review items with status and risk badges", () => {
    render(<ResearchEthicsPage />);
    expect(screen.getByText("IRB-101")).toBeInTheDocument();
    expect(screen.getByText("Human Subjects Study")).toBeInTheDocument();
    expect(screen.getByTestId("status-badge-101")).toHaveAttribute("data-variant", "warning");
    expect(screen.getByTestId("risk-badge-101")).toHaveAttribute("data-variant", "destructive");
  });

  it("does not crash when optional fields are missing", () => {
    useResearchEthicsReviewsMock.mockReturnValueOnce({
      data: {
        records: [
          {
            id: 202,
            tenant_id: 1,
            review_code: "IRB-202",
            project_title: "Metadata Study",
            principal_investigator_id: "FAC-202",
            review_type: "biosafety",
            status: "pending",
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<ResearchEthicsPage />);
    expect(screen.getByText("IRB-202")).toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });

  it("renders access denied for 403/401 backend errors", () => {
    useResearchEthicsReviewsMock.mockReturnValueOnce({
      data: undefined,
      isLoading: false,
      error: new ApiRequestError({ status: 403, detail: "forbidden" }),
      refetch: vi.fn(),
    });

    render(<ResearchEthicsPage />);
    expect(screen.getByText(/requires research.read access/i)).toBeInTheDocument();
  });

  it("renders generic error state for non-auth failures", () => {
    useResearchEthicsReviewsMock.mockReturnValueOnce({
      data: undefined,
      isLoading: false,
      error: new Error("backend unavailable"),
      refetch: vi.fn(),
    });

    render(<ResearchEthicsPage />);
    expect(screen.getByText(/Failed to load research ethics::backend unavailable/)).toBeInTheDocument();
  });

  it("does not expose automatic approve, reject, or sanction controls", () => {
    render(<ResearchEthicsPage />);
    expect(screen.queryByRole("button", { name: /approve/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /reject/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /sanction/i })).not.toBeInTheDocument();
  });

  it("renders access denied when frontend permission gate blocks access", () => {
    allowAccess = false;
    render(<ResearchEthicsPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
