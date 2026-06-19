import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import TranscriptPage from "../../app/(admin)/console/students/[id]/transcript/page";

const useTranscriptMock = vi.fn();
const useCreateTranscriptSnapshotMock = vi.fn();
let allowAccess = true;

vi.mock("next/link", () => ({
  default: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock("../../modules/transcripts/hooks", () => ({
  useTranscript: (...args: unknown[]) => useTranscriptMock(...args),
  useCreateTranscriptSnapshot: (...args: unknown[]) => useCreateTranscriptSnapshotMock(...args),
}));

vi.mock("../../modules/students/hooks", () => ({
  useStudent: () => ({
    data: {
      id: "1001",
      student_number: "STU-001",
      first_name: "Jane",
      last_name: "Doe",
      email: "jane@example.com",
      status: "active",
      tenant_id: "1",
      program: "CS",
      enrollment_year: 2026,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
  }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  PermissionGate: ({ children }: { children: ReactNode }) => <>{children}</>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: () => allowAccess,
    hasAnyPermission: () => allowAccess,
    roles: allowAccess ? ["admin"] : [],
  }),
}));

vi.mock("../../shared/hooks/use-mutation-feedback", () => ({
  useMutationFeedback: () => ({
    getHandlers: () => ({
      onSuccess: vi.fn(),
      onError: vi.fn(),
    }),
  }),
}));

const TRANSCRIPT = {
  student_profile_id: 1001,
  gpa: 3.9,
  total_credits: 30,
  items: [
    {
      enrollment_id: 4001,
      term_id: 1,
      term_code: "2026-SP",
      term_name: "2026 Spring",
      course_id: 701,
      course_code: "CS101",
      course_title: "Intro to CS",
      credits: 3,
      grade_code: "A",
      grade_points: 4.0,
    },
  ],
};

describe("TranscriptPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useTranscriptMock.mockReturnValue({
      data: TRANSCRIPT,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useCreateTranscriptSnapshotMock.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
  });

  it("renders transcript summary and entries", () => {
    render(<TranscriptPage params={{ id: "s1" }} />);

    expect(screen.getByText("STU-001 / Jane Doe")).toBeInTheDocument();
    expect(screen.getByText("Intro to CS")).toBeInTheDocument();
    expect(screen.getByText("Create snapshot")).toBeInTheDocument();
  });

  it("creates snapshot and renders latest snapshot card", () => {
    const mutate = vi.fn((_, handlers) => {
      handlers?.onSuccess?.({
        id: 9301,
        tenant_id: 1,
        student_profile_id: 1001,
        snapshot_json: { student_profile_id: 1001 },
        generated_by: "owner@example.com",
        generated_at: "2026-04-08T04:00:00Z",
      });
    });

    useCreateTranscriptSnapshotMock.mockReturnValue({ mutate, isPending: false });

    render(<TranscriptPage params={{ id: "s1" }} />);

    fireEvent.click(screen.getByRole("button", { name: /create snapshot/i }));

    expect(mutate).toHaveBeenCalled();
    expect(screen.getByText(/latest snapshot/i)).toBeInTheDocument();
    expect(screen.getByText("#9301")).toBeInTheDocument();
    expect(screen.getByText("owner@example.com")).toBeInTheDocument();
  });

  it("renders error state when transcript is unavailable", () => {
    useTranscriptMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("not found"),
      refetch: vi.fn(),
    });

    render(<TranscriptPage params={{ id: "s1" }} />);

    expect(screen.getByText(/transcript not found/i)).toBeInTheDocument();
  });

  it("shows access denied when read permission is missing", () => {
    allowAccess = false;
    render(<TranscriptPage params={{ id: "s1" }} />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
