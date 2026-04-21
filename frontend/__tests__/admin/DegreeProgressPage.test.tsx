import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import DegreeProgressPage from "../../app/(admin)/console/degree-progress/page";

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: () => false,
    hasAnyPermission: () => false,
    roles: [],
  }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../modules/degree-progress/hooks", () => ({
  useDegreeProgress: () => ({
    data: null,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useGraduationEligibility: () => ({
    data: null,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useDegreeProgressConsistency: () => ({
    data: null,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

describe("DegreeProgressPage", () => {
  it("renders AccessDenied when degree progress read permission is missing", () => {
    render(<DegreeProgressPage />);

    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
