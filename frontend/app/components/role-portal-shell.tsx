"use client";

import Link from "next/link";
import { Manrope, IBM_Plex_Serif } from "next/font/google";
import { useEffect, useMemo, useState } from "react";

const manrope = Manrope({ subsets: ["latin", "cyrillic"], weight: ["500", "700", "800"] });
const plexSerif = IBM_Plex_Serif({ subsets: ["latin", "cyrillic"], weight: ["500", "600"] });

export type PortalCard = {
  title: string;
  description: string;
  href: string;
  cta: string;
};

type RolePortalShellProps = {
  roleKey: "student" | "faculty" | "registrar";
  roleLabel: string;
  title: string;
  subtitle: string;
  accentFrom: string;
  accentTo: string;
  cards: PortalCard[];
};

type DashboardSnapshot = {
  generated_at: string | null;
  snapshot_date: string | null;
  kpis: Array<{
    key: string;
    value: number;
    title: string;
    source_status?: string | null;
  }>;
};

type RoleKpi = {
  label: string;
  value: string;
  hint: string;
};

type CopilotAskResponse = {
  insights: Array<{ title: string; value: string }>;
  warnings: string[];
  recommendations: Array<{ recommendation_type: string; title: string; reason: string }>;
};

type StudentRiskSummary = {
  atRiskCount: number;
  severeAtRiskCount: number;
  severity: "low" | "medium" | "high";
  warnings: string[];
  recommendationTitles: string[];
};

function buildRoleKpis(roleKey: RolePortalShellProps["roleKey"], snapshot: DashboardSnapshot): RoleKpi[] {
  const metricMap = new Map(snapshot.kpis.map((item) => [item.key, item]));
  const readValue = (key: string): number => Number(metricMap.get(key)?.value ?? 0);
  const readSource = (key: string): string => String(metricMap.get(key)?.source_status ?? "n/a");

  if (roleKey === "student") {
    return [
      {
        label: "Total Students",
        value: readValue("total_students").toLocaleString(),
        hint: `Source: ${readSource("total_students")}`,
      },
      {
        label: "Total Enrollments",
        value: readValue("total_enrollments").toLocaleString(),
        hint: `Source: ${readSource("total_enrollments")}`,
      },
      {
        label: "Total Grades Submitted",
        value: readValue("total_grades_submitted").toLocaleString(),
        hint: `Source: ${readSource("total_grades_submitted")}`,
      },
    ];
  }

  if (roleKey === "faculty") {
    return [
      {
        label: "Faculty Workload Proxy",
        value: readValue("total_grades_submitted").toLocaleString(),
        hint: "Grades submitted volume",
      },
      {
        label: "Enrollment Throughput",
        value: readValue("total_enrollments").toLocaleString(),
        hint: "Enrollment creation volume",
      },
      {
        label: "Students in Scope",
        value: readValue("total_students").toLocaleString(),
        hint: "Student population baseline",
      },
    ];
  }

  return [
    {
      label: "Analytics Events Ingested",
      value: readValue("analytics_events_ingested_total").toLocaleString(),
      hint: `Source: ${readSource("analytics_events_ingested_total")}`,
    },
    {
      label: "Analytics KPI Reads",
      value: readValue("analytics_kpi_reads_total").toLocaleString(),
      hint: `Source: ${readSource("analytics_kpi_reads_total")}`,
    },
    {
      label: "Failed Jobs",
      value: readValue("total_failed_jobs").toLocaleString(),
      hint: `Source: ${readSource("total_failed_jobs")}`,
    },
  ];
}

export function RolePortalShell(props: RolePortalShellProps) {
  const { roleKey, roleLabel, title, subtitle, accentFrom, accentTo, cards } = props;
  const [dashboardSnapshot, setDashboardSnapshot] = useState<DashboardSnapshot | null>(null);
  const [kpiError, setKpiError] = useState<string | null>(null);
  const [studentRisk, setStudentRisk] = useState<StudentRiskSummary | null>(null);

  useEffect(() => {
    let active = true;

    void (async () => {
      try {
        const res = await fetch("/api/bff/analytics/kpis", {
          method: "GET",
          cache: "no-store",
          credentials: "include",
        });

        if (!res.ok) {
          throw new Error(`Dashboard fetch failed: ${res.status}`);
        }

        const payload = (await res.json()) as DashboardSnapshot;
        if (active) {
          setDashboardSnapshot(payload);
          setKpiError(null);
        }
      } catch (error) {
        if (active) {
          setDashboardSnapshot(null);
          setKpiError(String(error));
        }
      }
    })();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    if (roleKey !== "student") {
      setStudentRisk(null);
      return () => {
        active = false;
      };
    }

    void (async () => {
      try {
        const sessionRes = await fetch("/api/auth/me", {
          method: "GET",
          cache: "no-store",
          credentials: "include",
        });
        if (!sessionRes.ok) {
          return;
        }

        const sessionPayload = (await sessionRes.json()) as {
          authenticated?: boolean;
          user?: { tenantId?: number };
        };
        const tenantId = Number(sessionPayload?.user?.tenantId ?? 0);
        if (!sessionPayload.authenticated || tenantId <= 0) {
          return;
        }

        const riskRes = await fetch("/api/bff/admin/platform/ai/copilot/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          cache: "no-store",
          credentials: "include",
          body: JSON.stringify({
            tenant_id: tenantId,
            question: "Show students at academic risk and expulsion risk",
            context: {},
          }),
        });
        if (!riskRes.ok) {
          return;
        }

        const riskPayload = (await riskRes.json()) as CopilotAskResponse;
        const atRiskCount = Number(riskPayload.insights.find((item) => item.title === "At-Risk Students")?.value ?? 0);
        const severeAtRiskCount = Number(
          riskPayload.insights.find((item) => item.title === "High Expulsion Risk Students")?.value ?? 0,
        );

        const severity: StudentRiskSummary["severity"] =
          severeAtRiskCount > 0 ? "high" : atRiskCount > 0 ? "medium" : "low";

        if (active) {
          setStudentRisk({
            atRiskCount,
            severeAtRiskCount,
            severity,
            warnings: Array.isArray(riskPayload.warnings) ? riskPayload.warnings : [],
            recommendationTitles: (riskPayload.recommendations || []).map((item) => item.title),
          });
        }
      } catch {
        if (active) {
          setStudentRisk(null);
        }
      }
    })();

    return () => {
      active = false;
    };
  }, [roleKey]);

  const kpis = useMemo(() => {
    if (!dashboardSnapshot) {
      return [] as RoleKpi[];
    }
    return buildRoleKpis(roleKey, dashboardSnapshot);
  }, [roleKey, dashboardSnapshot]);

  return (
    <main
      className={manrope.className}
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at 15% -10%, rgba(255,255,255,0.9), rgba(255,255,255,0) 35%), linear-gradient(145deg, #f4f7fb 0%, #ecf3f5 45%, #eef6ea 100%)",
        padding: "2rem 1rem 2.5rem",
      }}
    >
      <section
        style={{
          maxWidth: 1080,
          margin: "0 auto",
          borderRadius: 24,
          border: "1px solid rgba(15,23,42,0.08)",
          background: "rgba(255,255,255,0.78)",
          backdropFilter: "blur(4px)",
          boxShadow: "0 20px 45px rgba(15,23,42,0.08)",
          overflow: "hidden",
        }}
      >
        <header
          style={{
            padding: "1.6rem 1.6rem 1.3rem",
            background: `linear-gradient(110deg, ${accentFrom}, ${accentTo})`,
            color: "#f8fafc",
          }}
        >
          <p style={{ margin: 0, letterSpacing: "0.1em", textTransform: "uppercase", fontWeight: 800, fontSize: "0.74rem" }}>
            {roleLabel}
          </p>
          <h1 className={plexSerif.className} style={{ margin: "0.4rem 0 0", fontSize: "clamp(1.6rem, 3.4vw, 2.35rem)", lineHeight: 1.12 }}>
            {title}
          </h1>
          <p style={{ margin: "0.75rem 0 0", maxWidth: 780, color: "rgba(248,250,252,0.9)", fontSize: "1.02rem" }}>{subtitle}</p>
        </header>

        <section style={{ padding: "1.2rem 1.3rem 1.5rem" }}>
          <div style={{ marginBottom: "1rem" }}>
            <p style={{ margin: 0, color: "#334155", fontSize: "0.84rem", letterSpacing: "0.02em", textTransform: "uppercase", fontWeight: 800 }}>
              Live KPI Analytics
            </p>
            {dashboardSnapshot && (
              <p style={{ margin: "0.35rem 0 0", color: "#64748b", fontSize: "0.85rem" }}>
                Updated: {dashboardSnapshot.generated_at ? new Date(dashboardSnapshot.generated_at).toLocaleString() : "n/a"}
              </p>
            )}
          </div>

          {kpis.length > 0 && (
            <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", marginBottom: "1rem" }}>
              {kpis.map((kpi) => (
                <article
                  key={kpi.label}
                  style={{
                    borderRadius: 12,
                    border: "1px solid rgba(15,23,42,0.09)",
                    background: "#f8fafc",
                    padding: "0.8rem",
                  }}
                >
                  <p style={{ margin: 0, color: "#64748b", fontSize: "0.77rem", textTransform: "uppercase", letterSpacing: "0.03em", fontWeight: 700 }}>
                    {kpi.label}
                  </p>
                  <p style={{ margin: "0.3rem 0 0", color: "#0f172a", fontSize: "1.05rem", fontWeight: 800 }}>
                    {kpi.value}
                  </p>
                  <p style={{ margin: "0.25rem 0 0", color: "#475569", fontSize: "0.8rem" }}>{kpi.hint}</p>
                </article>
              ))}
            </div>
          )}

          {!dashboardSnapshot && !kpiError && (
            <p style={{ margin: "0 0 1rem", color: "#64748b", fontSize: "0.9rem" }}>
              Loading KPI analytics...
            </p>
          )}

          {kpiError && (
            <p style={{ margin: "0 0 1rem", color: "#991b1b", fontSize: "0.9rem" }}>
              KPI analytics is currently unavailable.
            </p>
          )}

          {roleKey === "student" && studentRisk && (
            <article
              style={{
                marginBottom: "1rem",
                borderRadius: 12,
                border:
                  studentRisk.severity === "high"
                    ? "1px solid rgba(153,27,27,0.35)"
                    : studentRisk.severity === "medium"
                      ? "1px solid rgba(180,83,9,0.35)"
                      : "1px solid rgba(21,128,61,0.35)",
                background:
                  studentRisk.severity === "high"
                    ? "#fef2f2"
                    : studentRisk.severity === "medium"
                      ? "#fffbeb"
                      : "#f0fdf4",
                padding: "0.9rem",
              }}
            >
              <p style={{ margin: 0, fontSize: "0.78rem", fontWeight: 800, letterSpacing: "0.04em", textTransform: "uppercase", color: "#334155" }}>
                Academic Risk Watch
              </p>
              <p style={{ margin: "0.35rem 0 0", fontWeight: 700, color: "#0f172a" }}>
                At-risk students: {studentRisk.atRiskCount.toLocaleString()} | High expulsion risk: {studentRisk.severeAtRiskCount.toLocaleString()}
              </p>
              <p style={{ margin: "0.2rem 0 0", color: "#475569", fontSize: "0.85rem" }}>
                Severity: {studentRisk.severity}
                {studentRisk.warnings.length > 0 ? ` | Warnings: ${studentRisk.warnings.join(", ")}` : ""}
              </p>
              {studentRisk.recommendationTitles.length > 0 && (
                <p style={{ margin: "0.2rem 0 0", color: "#334155", fontSize: "0.85rem" }}>
                  Recommended actions: {studentRisk.recommendationTitles.slice(0, 2).join("; ")}
                </p>
              )}
            </article>
          )}

          <div style={{ display: "grid", gap: "0.9rem", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
            {cards.map((card) => (
              <article
                key={card.href}
                style={{
                  borderRadius: 14,
                  border: "1px solid rgba(15,23,42,0.09)",
                  background: "#fff",
                  padding: "1rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.8rem",
                  boxShadow: "0 8px 22px rgba(15,23,42,0.05)",
                }}
              >
                <h2 style={{ margin: 0, fontSize: "1.02rem", color: "#0f172a" }}>{card.title}</h2>
                <p style={{ margin: 0, color: "#334155", lineHeight: 1.45 }}>{card.description}</p>
                <Link
                  href={card.href}
                  style={{
                    marginTop: "auto",
                    alignSelf: "flex-start",
                    textDecoration: "none",
                    color: "#0f172a",
                    fontWeight: 700,
                    borderBottom: "2px solid rgba(15,23,42,0.35)",
                  }}
                >
                  {card.cta}
                </Link>
              </article>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
