import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import TranscriptsPage from "../../app/(admin)/console/transcripts/page";

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

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("TranscriptsPageList", () => {
  it("renders AccessDenied when transcripts read permission is missing", () => {
    render(<TranscriptsPage />);

    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
