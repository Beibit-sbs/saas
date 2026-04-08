import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import BackupsPage from "../../app/(admin)/console/backups/page";

let allowAccess = true;

const useBackupSettingsMock = vi.fn();
const useBackupHistoryMock = vi.fn();
const useRestoreCandidatesMock = vi.fn();

vi.mock("../../modules/backups/hooks", () => ({
  useBackupSettings: (...args: unknown[]) => useBackupSettingsMock(...args),
  useBackupHistory: (...args: unknown[]) => useBackupHistoryMock(...args),
  useRestoreCandidates: (...args: unknown[]) => useRestoreCandidatesMock(...args),
  useUpdateBackupSettings: () => ({ mutate: vi.fn(), isPending: false }),
  useRunBackupNow: () => ({ mutate: vi.fn(), isPending: false }),
  useRunRestore: () => ({ mutate: vi.fn(), isPending: false }),
  useApplyRetention: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  PermissionGate: ({ children }: { children: React.ReactNode }) =>
    allowAccess ? <>{children}</> : null,
  RequirePermission: ({ children }: { children: React.ReactNode; permission: string }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
  AccessDenied: ({ message }: { message?: string }) => (
    <div>{message ?? "Access Denied"}</div>
  ),
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
    getHandlers: () => ({ onSuccess: vi.fn(), onError: vi.fn() }),
  }),
}));

vi.mock("../../app/components/LanguageProvider", async () => {
  const { en: commonEn } = await import("../../i18n/common/en");
  const { en: adminEn } = await import("../../i18n/admin/en");
  const dict = { ...commonEn, ...adminEn } as Record<string, string>;

  return {
    useLanguage: () => ({
      t: (key: string) => dict[key] ?? key,
    }),
  };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
  usePathname: () => "/console/backups",
  useSearchParams: () => new URLSearchParams(),
}));

describe("BackupsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useBackupSettingsMock.mockReturnValue({
      data: {
        active_profile: "local",
        profiles: [{ id: "local", label: "Local", path: "/tmp/app-backups/local" }],
        allowed_roots: ["/tmp/app-backups"],
        retention_days: 14,
        retention_min_files: 3,
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useBackupHistoryMock.mockReturnValue({
      data: {
        jobs: [
          {
            job_id: "1",
            job_type: "backup",
            status: "completed",
            profile_id: "local",
            started_at: "2026-01-01T00:00:00Z",
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useRestoreCandidatesMock.mockReturnValue({
      data: {
        profile_id: "local",
        profile_label: "Local",
        profile_path: "/tmp/app-backups/local",
        candidates: [
          {
            file_name: "backup_1.dump",
            file_path: "/tmp/app-backups/local/backup_1.dump",
            size_bytes: 100,
            modified_at: "2026-01-01T00:00:00Z",
          },
        ],
      },
      isLoading: false,
      error: null,
    });
  });

  it("renders backups page with history", () => {
    render(<BackupsPage />);
    expect(screen.getByTestId("backups-page")).toBeInTheDocument();
    expect(screen.getByText("Backup history")).toBeInTheDocument();
    expect(screen.getByText("backup")).toBeInTheDocument();
  });

  it("renders restore candidates table", () => {
    render(<BackupsPage />);
    expect(screen.getAllByText("backup_1.dump").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("shows empty state when history is empty", () => {
    useBackupHistoryMock.mockReturnValue({
      data: { jobs: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useRestoreCandidatesMock.mockReturnValue({
      data: {
        profile_id: "local",
        profile_label: "Local",
        profile_path: "/tmp/app-backups/local",
        candidates: [],
      },
      isLoading: false,
      error: null,
    });

    render(<BackupsPage />);
    expect(screen.getByText(/No backup jobs yet\./i)).toBeInTheDocument();
  });
  it("shows access denied when read permission is missing", () => {
    allowAccess = false;
    render(<BackupsPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });

});
