import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import AdmissionsPage from "../../app/(admin)/console/admissions/page";

const hasPermissionMock = vi.fn();

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: hasPermissionMock,
    hasAnyPermission: hasPermissionMock,
    roles: [],
  }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
  RequirePermission: ({ message, children }: { message?: string; children: ReactNode }) => (
    <div>{message ?? children}</div>
  ),
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => key,
  }),
}));

describe("AdmissionsPage", () => {
  it("renders AccessDenied when admissions.read permission is missing", () => {
    render(<AdmissionsPage />);

    expect(
      screen.getByText("This Admissions CRM route is fail-closed until the required permission is granted."),
    ).toBeInTheDocument();
  });
});
