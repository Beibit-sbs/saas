import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AdminJobsTab } from "../../app/admin/components/AdminJobsTab";

const tx = (key: string, fallback?: string) => fallback || key;

describe("AdminJobsTab", () => {
  it("renders jobs list and controls", () => {
    render(
      <AdminJobsTab
        tx={tx as any}
        jobsLoading={false}
        jobsMutating={false}
        jobsFeedback={null}
        jobsStatusFilter=""
        filteredJobs={[
          {
            id: 11,
            tenant_id: 1,
            job_type: "backup.run",
            status: "failed",
            payload_json: {},
            result_json: null,
            error_message: "boom",
            retry_count: 1,
            max_retries: 3,
            created_at: "2026-03-21T00:00:00Z",
            started_at: null,
            finished_at: null,
            created_by: "owner@example.com",
          },
        ]}
        onStatusFilterChange={vi.fn()}
        onLoadJobs={vi.fn(async () => undefined)}
        onCreateJob={vi.fn(async () => undefined)}
        onRetryJob={vi.fn(async () => undefined)}
        onCancelJob={vi.fn(async () => undefined)}
      />, 
    );

    expect(screen.getByText("Jobs")).toBeInTheDocument();
    expect(screen.getByText("backup.run")).toBeInTheDocument();
    expect(screen.getByText("boom")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("invokes callbacks for primary interactions", async () => {
    const user = userEvent.setup();
    const onCreateJob = vi.fn(async () => undefined);
    const onLoadJobs = vi.fn(async () => undefined);
    const onRetryJob = vi.fn(async () => undefined);
    const onCancelJob = vi.fn(async () => undefined);

    render(
      <AdminJobsTab
        tx={tx as any}
        jobsLoading={false}
        jobsMutating={false}
        jobsFeedback={null}
        jobsStatusFilter=""
        filteredJobs={[
          {
            id: 22,
            tenant_id: 1,
            job_type: "report.generate",
            status: "failed",
            payload_json: {},
            result_json: null,
            error_message: "oops",
            retry_count: 0,
            max_retries: 3,
            created_at: "2026-03-21T00:00:00Z",
            started_at: null,
            finished_at: null,
            created_by: "owner@example.com",
          },
        ]}
        onStatusFilterChange={vi.fn()}
        onLoadJobs={onLoadJobs}
        onCreateJob={onCreateJob}
        onRetryJob={onRetryJob}
        onCancelJob={onCancelJob}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Queue backup.run" }));
    await user.click(screen.getByRole("button", { name: "Refresh jobs" }));
    await user.click(screen.getByRole("button", { name: "Retry" }));

    expect(onCreateJob).toHaveBeenCalledWith("backup.run", {});
    expect(onLoadJobs).toHaveBeenCalled();
    expect(onRetryJob).toHaveBeenCalledWith(22);
    expect(onCancelJob).not.toHaveBeenCalled();
  });
});
