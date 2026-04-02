import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { AdminOverviewTab } from "../../app/admin/components/AdminOverviewTab";
import type { AdminCopy } from "../../app/admin/types";
import { adminTranslations } from "../../i18n/admin";

const l: AdminCopy = adminTranslations.en;

describe("AdminOverviewTab states", () => {
  it("renders a dedicated loading state before the first snapshot arrives", () => {
    render(
      <AdminOverviewTab
        l={l}
        tx={(key) => l[key]}
        dashboardStamp="-"
        dashboardLoading={true}
        overviewFeedback={null}
        dashboardSnapshot={null}
        decisionInsights={[]}
        enabledLanguageCodes=""
        onRefresh={vi.fn()}
      />,
    );

    expect(screen.getByTestId("overview-state-loading")).toBeInTheDocument();
    expect(screen.getByText(/loading live control signals/i)).toBeInTheDocument();
  });

  it("renders a recoverable empty/error state when the primary snapshot is unavailable", () => {
    const onRefresh = vi.fn();

    render(
      <AdminOverviewTab
        l={l}
        tx={(key) => l[key]}
        dashboardStamp="-"
        dashboardLoading={false}
        overviewFeedback={{ tone: "error", message: "Error: 503" }}
        dashboardSnapshot={null}
        decisionInsights={[]}
        enabledLanguageCodes=""
        onRefresh={onRefresh}
      />,
    );

    expect(screen.getByTestId("overview-state-empty")).toBeInTheDocument();
    expect(screen.getByText(/overview is temporarily unavailable/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /refresh snapshot/i })).toBeInTheDocument();
  });
});