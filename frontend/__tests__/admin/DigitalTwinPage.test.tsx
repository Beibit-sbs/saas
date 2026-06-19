import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import DigitalTwinPage from "@/app/(admin)/console/digital-twin/page";

describe("DigitalTwinPage (A-056.2 shell)", () => {
  it("renders observed dimensions, reused sources, and safety boundaries read-only", () => {
    render(<DigitalTwinPage />);

    expect(screen.getByTestId("digital-twin-page")).toBeInTheDocument();
    expect(screen.getByTestId("digital-twin-observed-dimensions")).toBeInTheDocument();
    expect(screen.getByTestId("digital-twin-safety-boundaries")).toBeInTheDocument();
    expect(screen.getByTestId("digital-twin-capacity-whatif")).toBeInTheDocument();
    expect(screen.getByText("POST /api/admin/digital-twin/simulate/capacity")).toBeInTheDocument();
    expect(screen.getByText("incomplete_data reported, never guessed")).toBeInTheDocument();
    expect(
      screen.getByText(
        "use_live_sources reads current_students from enrollments and classroom_capacity from campus_rooms (best-effort, falls back honestly)",
      ),
    ).toBeInTheDocument();
    expect(screen.getByTestId("digital-twin-early-warning")).toBeInTheDocument();
    expect(screen.getByText("POST /api/admin/digital-twin/early-warning/capacity")).toBeInTheDocument();
    expect(screen.getByText("recommends action, executes nothing")).toBeInTheDocument();
    expect(screen.getByTestId("digital-twin-scenarios")).toBeInTheDocument();
    expect(screen.getByText("POST /api/admin/digital-twin/scenarios/capacity")).toBeInTheDocument();
    expect(screen.getByText("intake_plus_30pct")).toBeInTheDocument();

    // observed dimension + reused source (no duplication)
    expect(screen.getByText("student_population")).toBeInTheDocument();
    expect(screen.getByText("student_risk_signal_registry")).toBeInTheDocument();
    expect(screen.getByText("scheduling")).toBeInTheDocument();

    // safety boundaries block autonomy; honest no-fake-metrics
    expect(screen.getByText("no_autonomous_budget_commitment=true")).toBeInTheDocument();
    expect(screen.getByText("no_hidden_scoring=true")).toBeInTheDocument();
    expect(screen.getAllByText("fake_metrics=false").length).toBeGreaterThan(0);
    expect(screen.getByText("autonomous_academic_decision")).toBeInTheDocument();

    // operating principle
    expect(screen.getByTestId("digital-twin-operating-principle")).toHaveTextContent(
      "Brain sees. Digital twin simulates.",
    );
  });
});
