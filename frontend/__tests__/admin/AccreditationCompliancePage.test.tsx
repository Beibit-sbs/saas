import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import AccreditationCompliancePage from "@/app/(admin)/console/accreditation-compliance/page";

const createMutateAsync = vi.fn();
const updateMutateAsync = vi.fn();

vi.mock("@/modules/accreditation/hooks", () => ({
  useAccreditation: () => ({
    data: {
      items: [
        {
          id: 1,
          standard_code: "ACC-2026-01",
          standard_type: "institutional",
          title: "Institutional Mission Alignment",
          owner_department: "Registrar",
          review_cycle_year: 2026,
          due_date: null,
          evidence_summary: "Initial self-study package",
          risk_level: "medium",
          status: "draft",
          reviewer_notes: null,
          remediation_plan: null,
        },
      ],
    },
    isLoading: false,
  }),
  useCreateAccreditation: () => ({ mutateAsync: createMutateAsync, isPending: false }),
  useUpdateAccreditationStatus: () => ({ mutateAsync: updateMutateAsync, isPending: false }),
}));

describe("AccreditationCompliancePage", () => {
  it("renders accreditation title", () => {
    render(<AccreditationCompliancePage />);
    expect(screen.getByText("Accreditation Compliance")).toBeInTheDocument();
  });

  it("renders accreditation table row", () => {
    render(<AccreditationCompliancePage />);
    expect(screen.getByText("ACC-2026-01")).toBeInTheDocument();
    expect(screen.getByText("Institutional Mission Alignment")).toBeInTheDocument();
  });

  it("shows create dialog trigger", () => {
    render(<AccreditationCompliancePage />);
    expect(screen.getByRole("button", { name: "Create Standard Record" })).toBeInTheDocument();
  });

  it("opens create dialog", () => {
    render(<AccreditationCompliancePage />);
    fireEvent.click(screen.getByRole("button", { name: "Create Standard Record" }));
    expect(screen.getByText("New Accreditation Record")).toBeInTheDocument();
  });

  it("displays draft status badge", () => {
    render(<AccreditationCompliancePage />);
    expect(screen.getByText("Draft")).toBeInTheDocument();
  });

  it("renders status filter input", () => {
    render(<AccreditationCompliancePage />);
    expect(screen.getByPlaceholderText("Filter by status")).toBeInTheDocument();
  });
});
