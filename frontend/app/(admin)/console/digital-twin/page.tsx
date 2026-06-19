"use client";

// Digital Twin / Predictive Operations — read-only frontend shell (A-056.2).
// Declares what the twin observes and the safety boundaries it runs under.
// No fabricated metrics; mirrors the backend shell contract (A-056.1).

const OBSERVED_DIMENSIONS = [
  "student_population",
  "staff_population",
  "rooms_and_buildings",
  "schedules",
  "budgets",
  "inventory",
  "service_workload",
  "security_events",
];

const SOURCE_SIGNAL_REGISTRIES = [
  "student_risk_signal_registry",
  "finance_anomaly_signal_registry",
  "academic_quality_signal_registry",
  "procurement_risk_signal_registry",
  "curriculum_gap_signal_registry",
];

const SOURCE_CAPACITY_MODULES = [
  "enrollments",
  "scheduling",
  "room_booking",
  "asset_inventory",
  "dormitory_management",
  "dining",
];

const FORBIDDEN_ACTIONS = [
  "autonomous_budget_commitment",
  "autonomous_academic_decision",
  "autonomous_disciplinary_decision",
  "hidden_scoring",
  "supplier_order_without_human_approval",
  "any_execution_without_human_approval",
];

const SAFETY_FLAGS = [
  "no_autonomous_budget_commitment=true",
  "no_autonomous_academic_decision=true",
  "no_autonomous_disciplinary_decision=true",
  "no_hidden_scoring=true",
  "no_supplier_order_without_human_approval=true",
  "all_recommendations_explain_evidence=true",
  "all_accepted_actions_audited=true",
  "fake_metrics=false",
  "provider_live_enabled=false",
];

export default function DigitalTwinPage() {
  return (
    <div className="space-y-6 p-4" data-testid="digital-twin-page">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Digital Twin / Predictive Operations</h1>
        <p className="text-sm text-muted-foreground">
          Read-only observation + simulation shell. Runtime mode:
          METADATA_OBSERVATION_SIMULATION_HUMAN_REVIEW_ONLY. No fabricated metrics; incomplete_data=true.
        </p>
        <p className="text-sm font-medium" data-testid="digital-twin-operating-principle">
          Brain sees. Digital twin simulates. Workflow proposes. Human approves. Audit records.
        </p>
      </header>

      <section className="rounded-xl border bg-card p-4" data-testid="digital-twin-observed-dimensions">
        <h2 className="text-base font-semibold">Observed dimensions</h2>
        <p className="mt-1 text-xs text-muted-foreground">GET /api/admin/digital-twin/state</p>
        <ul className="mt-3 grid gap-1 text-sm text-muted-foreground md:grid-cols-2">
          {OBSERVED_DIMENSIONS.map((dim) => (
            <li key={dim}>{dim}</li>
          ))}
        </ul>
      </section>

      <section className="rounded-xl border bg-card p-4" data-testid="digital-twin-sources">
        <h2 className="text-base font-semibold">Reused sources (no duplication)</h2>
        <div className="mt-3 grid gap-4 md:grid-cols-2">
          <div>
            <h3 className="text-sm font-medium">Signal registries</h3>
            <ul className="mt-2 grid gap-1 text-xs text-muted-foreground">
              {SOURCE_SIGNAL_REGISTRIES.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-medium">Capacity / resource modules</h3>
            <ul className="mt-2 grid gap-1 text-xs text-muted-foreground">
              {SOURCE_CAPACITY_MODULES.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="rounded-xl border bg-card p-4" data-testid="digital-twin-safety-boundaries">
        <h2 className="text-base font-semibold">Safety boundaries</h2>
        <p className="mt-1 text-xs text-muted-foreground">GET /api/admin/digital-twin/safety-boundaries</p>
        <div className="mt-3 grid gap-4 md:grid-cols-2">
          <div>
            <h3 className="text-sm font-medium">Forbidden actions</h3>
            <ul className="mt-2 grid gap-1 text-xs text-muted-foreground">
              {FORBIDDEN_ACTIONS.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-medium">Safety flags</h3>
            <ul className="mt-2 grid gap-1 text-xs text-muted-foreground">
              {SAFETY_FLAGS.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          </div>
        </div>
        <p className="mt-3 text-xs text-muted-foreground">
          No autonomous budget, academic, or disciplinary action. No hidden scoring. No supplier order
          without human approval. All recommendations explain evidence and produce an audit trail.
        </p>
      </section>

      <section className="rounded-xl border bg-card p-4" data-testid="digital-twin-capacity-whatif">
        <h2 className="text-base font-semibold">Capacity what-if (deterministic)</h2>
        <p className="mt-1 text-xs text-muted-foreground">POST /api/admin/digital-twin/simulate/capacity</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Deterministic projection on provided baselines — no value is fabricated. Each input is tagged
          to its source module (current_students→enrollments, classroom_capacity→scheduling,
          dormitory_capacity→dormitory_management). Missing inputs are reported as incomplete_data, not
          guessed. Output is a human-review readout (projected_students, classroom_utilization,
          dormitory_pressure, risks) — it proposes nothing and executes nothing.
        </p>
        <ul className="mt-3 grid gap-1 text-xs text-muted-foreground md:grid-cols-2">
          <li>human_review_required=true</li>
          <li>fake_metrics=false</li>
          <li>incomplete_data reported, never guessed</li>
          <li>no autonomous action</li>
          <li>use_live_sources reads current_students from enrollments and classroom_capacity from campus_rooms (best-effort, falls back honestly)</li>
        </ul>
      </section>

      <section className="rounded-xl border bg-card p-4" data-testid="digital-twin-early-warning">
        <h2 className="text-base font-semibold">Early warning (read-only, human-gated)</h2>
        <p className="mt-1 text-xs text-muted-foreground">POST /api/admin/digital-twin/early-warning/capacity</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Turns the capacity projection into severity-classified warnings (high/medium) with a
          recommended human action — classroom capacity risk → escalate_to_scheduling_and_facilities,
          dormitory capacity risk → escalate_to_housing_office. The twin proposes; a human decides.
        </p>
        <ul className="mt-3 grid gap-1 text-xs text-muted-foreground md:grid-cols-2">
          <li>requires_human_approval=true</li>
          <li>no_autonomous_action=true</li>
          <li>signal registries declared as candidate sources (not fabricated counts)</li>
          <li>recommends action, executes nothing</li>
        </ul>
      </section>

      <section className="rounded-xl border bg-card p-4" data-testid="digital-twin-scenarios">
        <h2 className="text-base font-semibold">What-if scenario registry (executive review)</h2>
        <p className="mt-1 text-xs text-muted-foreground">POST /api/admin/digital-twin/scenarios/capacity</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Runs named intake-growth scenarios side by side for executive comparison — default
          baseline / +10% / +20% / +30% — each with its capacity projection and early warnings.
          Read-only; the twin lays out the options, humans choose.
        </p>
        <ul className="mt-3 grid gap-1 text-xs text-muted-foreground md:grid-cols-2">
          <li>baseline</li>
          <li>intake_plus_10pct</li>
          <li>intake_plus_20pct</li>
          <li>intake_plus_30pct</li>
        </ul>
      </section>

      <section className="rounded-xl border bg-card p-4" data-testid="digital-twin-scenario-decision">
        <h2 className="text-base font-semibold">Human decision → audit (closes the loop)</h2>
        <p className="mt-1 text-xs text-muted-foreground">POST /api/admin/digital-twin/scenarios/decision</p>
        <p className="mt-2 text-sm text-muted-foreground">
          A reviewer records accepted / rejected / deferred on a scenario with a rationale. The decision
          is written to the real audit trail (action digital_twin.scenario_decision_recorded) and nothing
          is executed — the principle in full: Brain sees, twin simulates, workflow proposes, human
          approves, audit records.
        </p>
        <ul className="mt-3 grid gap-1 text-xs text-muted-foreground md:grid-cols-2">
          <li>decision ∈ accepted | rejected | deferred</li>
          <li>no_autonomous_execution=true</li>
          <li>recorded to app_audit_events with correlation_id</li>
          <li>rationale required; human_review_required=true</li>
        </ul>
      </section>

      <section className="rounded-xl border bg-card p-4" data-testid="digital-twin-resource-whatif">
        <h2 className="text-base font-semibold">Resource-consumption what-if (supplies / utilities)</h2>
        <p className="mt-1 text-xs text-muted-foreground">POST /api/admin/digital-twin/simulate/resource · /early-warning/resource</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Deterministic days-of-stock projection per resource (current_stock / daily_consumption), with a
          reorder/stockout early warning and a recommended human action (escalate_to_procurement_reorder).
          Inputs tagged to source modules (current_stock→asset_inventory, daily_consumption→operations);
          missing consumption → incomplete_data, never guessed. Read-only; the twin proposes, a human reorders.
        </p>
        <ul className="mt-3 grid gap-1 text-xs text-muted-foreground md:grid-cols-2">
          <li>stockout_before_lead_time → high</li>
          <li>reorder_point_reached → medium</li>
          <li>requires_human_approval=true · no_autonomous_action=true</li>
          <li>no supplier order without human approval</li>
        </ul>
      </section>

      <section className="rounded-xl border bg-card p-4" data-testid="digital-twin-decision-log">
        <h2 className="text-base font-semibold">Executive decision log (read-back)</h2>
        <p className="mt-1 text-xs text-muted-foreground">GET /api/admin/digital-twin/scenarios/decisions</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Reads back the recorded scenario decisions from the audit trail (filtered to
          digital_twin.scenario_decision_recorded) — reviewer, scenario, decision, rationale,
          correlation_id, timestamp. Tenant-scoped, read-only; the audit trail is the system of record.
        </p>
      </section>
    </div>
  );
}
