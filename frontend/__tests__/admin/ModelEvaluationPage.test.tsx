import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import ModelEvaluationPage from "../../app/(admin)/console/model-evaluation/page";

let allowAccess = true;

vi.mock("../../modules/model-evaluation/hooks", () => ({
  useCreateEvalRun: () => ({ mutate: vi.fn(), isPending: false }),
  useListEvalRuns: () => ({
    data: [
      {
        run_id: "run-1",
        eval_set_name: "gpt4-baseline",
        model_name: "gpt-4o",
        status: "completed",
        metrics: [],
        notes: null,
        created_by: "admin",
        created_at: "2026-01-01T00:00:00Z",
        completed_at: null,
      },
    ],
  }),
  useLeaderboard: () => ({
    data: [
      {
        rank: 1,
        model_name: "gpt-4o",
        eval_set_name: "gpt4-baseline",
        primary_metric: "accuracy",
        primary_score: 0.92,
        run_id: "run-1",
        completed_at: null,
      },
    ],
  }),
  useSubmitEvalResults: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode; permission: string }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: () => allowAccess,
    hasAnyPermission: () => allowAccess,
    roles: allowAccess ? ["admin"] : [],
  }),
}));

describe("ModelEvaluationPage", () => {
  beforeEach(() => {
    allowAccess = true;
  });

  it("renders page title", () => {
    render(<ModelEvaluationPage />);
    expect(screen.getByText(/Model Evaluation/i)).toBeInTheDocument();
  });

  it("renders eval run rows", () => {
    render(<ModelEvaluationPage />);
    expect(screen.getAllByText("gpt4-baseline").length).toBeGreaterThan(0);
    expect(screen.getAllByText("gpt-4o").length).toBeGreaterThan(0);
  });

  it("renders leaderboard", () => {
    render(<ModelEvaluationPage />);
    expect(screen.getByText("Leaderboard")).toBeInTheDocument();
    expect(screen.getByText("#1")).toBeInTheDocument();
  });

  it("shows access denied without permission", () => {
    allowAccess = false;
    render(<ModelEvaluationPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
