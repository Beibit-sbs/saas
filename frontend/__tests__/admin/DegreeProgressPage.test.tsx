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
  useProgramRequirements: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useCreateProgramRequirement: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../modules/students/hooks", () => ({
  useStudents: () => ({ data: { items: [], total: 0 }, isLoading: false, error: null, refetch: vi.fn() }),
  useStudent: () => ({ data: null, isLoading: false, error: null, refetch: vi.fn() }),
  useActiveStudentProgram: () => ({ data: null, isLoading: false, error: null, refetch: vi.fn() }),
  useBindStudentProgram: () => ({ mutate: vi.fn(), isPending: false }),
  useChangeStudentStatus: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../modules/programs/hooks", () => ({
  usePrograms: () => ({ data: { programs: [] }, isLoading: false, error: null, refetch: vi.fn() }),
}));

vi.mock("../../modules/courses/hooks", () => ({
  useCourses: () => ({ data: { courses: [] }, isLoading: false, error: null, refetch: vi.fn() }),
}));

vi.mock("../../modules/student-lifecycle/hooks", () => ({
  useCreateDegreeProgressSnapshot: () => ({ mutate: vi.fn(), isPending: false }),
  useReviewGraduationReadiness: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../modules/student-lifecycle/types", () => ({
  DegreeProgressStatus: {
    GRADUATION_READY_METADATA: "GRADUATION_READY_METADATA",
    NOT_READY_METADATA: "NOT_READY_METADATA",
  },
}));

describe("DegreeProgressPage", () => {
  it("renders AccessDenied when degree progress read permission is missing", () => {
    render(<DegreeProgressPage />);

    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
