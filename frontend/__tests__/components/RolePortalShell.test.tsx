/**
 * Tests for the RolePortalShell component — verifies that each role
 * (student / faculty / registrar) renders KPI cards, navigation cards,
 * and the AI risk widget when relevant data is available.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

// ── Mock next/font/google before importing the component ──────────────────
vi.mock("next/font/google", () => ({
  Manrope: () => ({ className: "manrope-mock" }),
  IBM_Plex_Serif: () => ({ className: "ibm-plex-mock" }),
}));

// ── Mock next/link ────────────────────────────────────────────────────────
vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

import { RolePortalShell } from "../../app/components/role-portal-shell";

const KPI_SNAPSHOT = {
  generated_at: "2026-04-12T08:00:00Z",
  snapshot_date: "2026-04-12",
  kpis: [
    { key: "total_students", value: 1200, title: "Total Students", source_status: "live" },
    { key: "total_enrollments", value: 3400, title: "Total Enrollments", source_status: "live" },
    { key: "total_grades_submitted", value: 890, title: "Total Grades Submitted", source_status: "live" },
    { key: "analytics_events_ingested_total", value: 50000, title: "Events Ingested", source_status: "live" },
    { key: "analytics_kpi_reads_total", value: 1500, title: "KPI Reads", source_status: "live" },
  ],
};

const STUDENT_CARDS = [
  { title: "Enrollment Requests", description: "Manage enrollment.", href: "/console/enrollments", cta: "Manage enrollment" },
  { title: "Grades and Progress", description: "Review grades.", href: "/console/grades", cta: "Open grades" },
];

const FACULTY_CARDS = [
  { title: "Class Roster", description: "Inspect roster.", href: "/console/students", cta: "Open roster" },
  { title: "Grading Cycle", description: "Submit grades.", href: "/console/grades", cta: "Manage grades" },
];

const REGISTRAR_CARDS = [
  { title: "Admissions Pipeline", description: "Track applicants.", href: "/console/admissions", cta: "Open admissions" },
  { title: "Institution Governance", description: "Review tenants.", href: "/console/tenants", cta: "Open governance" },
];

function buildFetch(kpiData: object, riskData?: object) {
  return vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/api/bff/analytics/kpis")) {
      return Promise.resolve(new Response(JSON.stringify(kpiData), { status: 200 }));
    }
    if (url.includes("/api/auth/me")) {
      return Promise.resolve(
        new Response(
          JSON.stringify({ authenticated: true, user: { tenantId: 1 } }),
          { status: 200 },
        ),
      );
    }
    if (url.includes("/api/bff/admin/platform/ai/copilot/ask")) {
      return Promise.resolve(
        new Response(JSON.stringify(riskData ?? { insights: [], warnings: [], recommendations: [] }), { status: 200 }),
      );
    }
    return Promise.resolve(new Response(JSON.stringify({}), { status: 200 }));
  });
}

describe("RolePortalShell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── Student portal ──────────────────────────────────────────────────────
  it("renders student portal header and KPI cards", async () => {
    vi.stubGlobal("fetch", buildFetch(KPI_SNAPSHOT));

    render(
      <RolePortalShell
        roleKey="student"
        roleLabel="Student Zone"
        title="Student Portal"
        subtitle="Self-service area."
        accentFrom="#0f766e"
        accentTo="#1d4ed8"
        cards={STUDENT_CARDS}
      />,
    );

    expect(screen.getByText("Student Portal")).toBeInTheDocument();
    expect(screen.getByText("Student Zone")).toBeInTheDocument();

    // KPI cards should appear after fetch resolves
    await waitFor(() => {
      expect(screen.getByText("1,200")).toBeInTheDocument(); // total_students
    });
    expect(screen.getByText("3,400")).toBeInTheDocument(); // total_enrollments
    expect(screen.getByText("890")).toBeInTheDocument(); // total_grades_submitted
  });

  it("renders student navigation cards with correct links", async () => {
    vi.stubGlobal("fetch", buildFetch(KPI_SNAPSHOT));

    render(
      <RolePortalShell
        roleKey="student"
        roleLabel="Student Zone"
        title="Student Portal"
        subtitle="Self-service area."
        accentFrom="#0f766e"
        accentTo="#1d4ed8"
        cards={STUDENT_CARDS}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Enrollment Requests")).toBeInTheDocument();
    });

    const enrollLink = screen.getByRole("link", { name: "Manage enrollment" });
    expect(enrollLink).toHaveAttribute("href", "/console/enrollments");

    const gradesLink = screen.getByRole("link", { name: "Open grades" });
    expect(gradesLink).toHaveAttribute("href", "/console/grades");
  });

  it("shows AI Academic Risk Watch when copilot returns at-risk data", async () => {
    const riskData = {
      insights: [
        { title: "At-Risk Students", value: "42" },
        { title: "High Expulsion Risk Students", value: "7" },
      ],
      warnings: ["High dropout velocity"],
      recommendations: [
        { recommendation_type: "alert", title: "Schedule advisor meeting", reason: "GPA below threshold" },
      ],
    };

    vi.stubGlobal("fetch", buildFetch(KPI_SNAPSHOT, riskData));

    render(
      <RolePortalShell
        roleKey="student"
        roleLabel="Student Zone"
        title="Student Portal"
        subtitle="Self-service area."
        accentFrom="#0f766e"
        accentTo="#1d4ed8"
        cards={STUDENT_CARDS}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Academic Risk Watch")).toBeInTheDocument();
    });

    expect(screen.getByText(/At-risk students: 42/)).toBeInTheDocument();
    expect(screen.getByText(/High expulsion risk: 7/)).toBeInTheDocument();
    expect(screen.getByText(/Severity: high/)).toBeInTheDocument();
  });

  // ── Faculty portal ──────────────────────────────────────────────────────
  it("renders faculty portal header and KPI cards", async () => {
    vi.stubGlobal("fetch", buildFetch(KPI_SNAPSHOT));

    render(
      <RolePortalShell
        roleKey="faculty"
        roleLabel="Faculty Zone"
        title="Faculty Portal"
        subtitle="Instructor workspace."
        accentFrom="#7c2d12"
        accentTo="#0f766e"
        cards={FACULTY_CARDS}
      />,
    );

    expect(screen.getByText("Faculty Portal")).toBeInTheDocument();
    expect(screen.getByText("Faculty Zone")).toBeInTheDocument();

    await waitFor(() => {
      // faculty workload proxy = total_grades_submitted = 890
      expect(screen.getByText("890")).toBeInTheDocument();
    });

    const rosterLink = await screen.findByRole("link", { name: "Open roster" });
    expect(rosterLink).toHaveAttribute("href", "/console/students");
  });

  // ── Registrar portal ────────────────────────────────────────────────────
  it("renders registrar portal header and navigation cards", async () => {
    vi.stubGlobal("fetch", buildFetch(KPI_SNAPSHOT));

    render(
      <RolePortalShell
        roleKey="registrar"
        roleLabel="Registrar Zone"
        title="Registrar and Dean Office"
        subtitle="Governance surface."
        accentFrom="#4c1d95"
        accentTo="#7c2d12"
        cards={REGISTRAR_CARDS}
      />,
    );

    expect(screen.getByText("Registrar and Dean Office")).toBeInTheDocument();
    expect(screen.getByText("Registrar Zone")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Admissions Pipeline")).toBeInTheDocument();
    });

    const admissionsLink = screen.getByRole("link", { name: "Open admissions" });
    expect(admissionsLink).toHaveAttribute("href", "/console/admissions");
  });

  // ── KPI unavailable ─────────────────────────────────────────────────────
  it("shows fallback text when KPI fetch fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response(JSON.stringify({}), { status: 500 }))),
    );

    render(
      <RolePortalShell
        roleKey="faculty"
        roleLabel="Faculty Zone"
        title="Faculty Portal"
        subtitle="Instructor workspace."
        accentFrom="#7c2d12"
        accentTo="#0f766e"
        cards={FACULTY_CARDS}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText(/KPI analytics is currently unavailable/)).toBeInTheDocument();
    });
  });
});
