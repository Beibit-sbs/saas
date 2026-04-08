import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

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
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => key,
  }),
}));

describe("AdmissionsPage", () => {
  it("renders AccessDenied when admissions.read permission is missing", () => {
    hasPermissionMock.mockReturnValue(false);

    render(<AdmissionsPage />);

    expect(hasPermissionMock).toHaveBeenCalled();
    expect(screen.getByText("Access Denied")).toBeInTheDocument();
  });
});
