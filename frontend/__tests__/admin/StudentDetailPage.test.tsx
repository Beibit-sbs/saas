import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import StudentDetailPage from "../../app/(admin)/console/students/[id]/page";

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: () => false,
    hasAnyPermission: () => false,
    roles: [],
  }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
  PermissionGate: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("../../modules/students/hooks", () => ({
  useStudent: () => ({
    data: null,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

vi.mock("../../modules/enrollments/hooks", () => ({
  useEnrollments: () => ({
    data: { items: [] },
    isLoading: false,
  }),
}));

vi.mock("next/link", () => ({
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => key,
  }),
}));

describe("StudentDetailPage", () => {
  it("renders AccessDenied when students read permission is missing", () => {
    render(<StudentDetailPage params={{ id: "student-1" }} />);

    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
