import type { PortalCard } from "@/app/components/role-portal-shell";

export type RolePortalKey = "student" | "faculty" | "registrar";

export type RolePortalField = {
  key: string;
  label: string;
};

export type RolePortalResource = {
  title: string;
  endpoint: string;
  kind: "list" | "object";
  emptyMessage: string;
  previewFields: RolePortalField[];
};

export type RolePortalSectionConfig = {
  key: string;
  navLabel: string;
  title: string;
  subtitle: string;
  cta: string;
  bullets: string[];
  resources?: RolePortalResource[];
};

export type RolePortalConfig = {
  roleKey: RolePortalKey;
  roleLabel: string;
  zoneTitle: string;
  title: string;
  subtitle: string;
  accentFrom: string;
  accentTo: string;
  sections: RolePortalSectionConfig[];
};

export const ROLE_PORTAL_CONFIGS: Record<RolePortalKey, RolePortalConfig> = {
  student: {
    roleKey: "student",
    roleLabel: "Student Zone",
    zoneTitle: "Student Zone",
    title: "Student Portal",
    subtitle: "Self-service area for registration, grades, and personal academic progress across the current term.",
    accentFrom: "#0f766e",
    accentTo: "#1d4ed8",
    sections: [
      {
        key: "enrollments",
        navLabel: "Enrollments",
        title: "Enrollment Requests",
        subtitle: "Student self-service workspace for add/drop activity, waitlist follow-up, and enrollment review.",
        cta: "Manage enrollment",
        bullets: [
          "Review current registration actions and enrollment-related follow-up items from the student zone.",
          "Use a route-safe page that does not depend on broader console navigation.",
          "Keep enrollment guidance, next steps, and academic coordination close to the student portal.",
        ],
        resources: [
          {
            title: "Live enrollment preview",
            endpoint: "/api/bff/admin/enrollments?page=1&page_size=5",
            kind: "list",
            emptyMessage: "No enrollment records are currently visible to this account.",
            previewFields: [
              { key: "student_profile_id", label: "Student" },
              { key: "course_id", label: "Course" },
              { key: "section_id", label: "Section" },
              { key: "enrollment_status", label: "Status" },
            ],
          },
        ],
      },
      {
        key: "grades",
        navLabel: "Grades",
        title: "Grades and Progress",
        subtitle: "Student-facing grading view for academic standing, progress checks, and result review.",
        cta: "Open grades",
        bullets: [
          "Review grade outcomes and progress notes from a student-safe route.",
          "Keep grade-related navigation inside the portal instead of depending on admin console surfaces.",
          "Use this page as the student entry point for grade review and follow-up actions.",
        ],
        resources: [
          {
            title: "Live grade preview",
            endpoint: "/api/bff/admin/grades?page=1&page_size=5",
            kind: "list",
            emptyMessage: "No grade records are currently visible to this account.",
            previewFields: [
              { key: "student_name", label: "Student" },
              { key: "course_name", label: "Course" },
              { key: "grade_code", label: "Grade" },
              { key: "grade_points", label: "Points" },
            ],
          },
        ],
      },
      {
        key: "transcripts",
        navLabel: "Transcripts",
        title: "Academic Transcript",
        subtitle: "Student transcript review page for historical academic records, verification, and export preparation.",
        cta: "View transcript",
        bullets: [
          "Review transcript-related information from a dedicated student route.",
          "Prepare academic record verification before advisor or registrar follow-up.",
          "Keep transcript navigation inside the role portal rather than generic console sections.",
        ],
      },
      {
        key: "profile",
        navLabel: "Profile",
        title: "Profile and Preferences",
        subtitle: "Student account space for personal details, language preferences, and self-service profile maintenance.",
        cta: "Open profile",
        bullets: [
          "Review the profile and preference tasks available to the student account.",
          "Use this page as the portal-owned entry point before moving to shared profile management.",
          "Keep identity and communication preference tasks connected to the student journey.",
        ],
        resources: [
          {
            title: "Saved preferences",
            endpoint: "/api/auth/me/preferences",
            kind: "object",
            emptyMessage: "No explicit user preferences are stored yet.",
            previewFields: [{ key: "language", label: "Language" }],
          },
        ],
      },
    ],
  },
  faculty: {
    roleKey: "faculty",
    roleLabel: "Faculty Zone",
    zoneTitle: "Faculty Zone",
    title: "Faculty Portal",
    subtitle: "Workspace for instructors to run roster review, grading cycles, and teaching schedule decisions.",
    accentFrom: "#7c2d12",
    accentTo: "#0f766e",
    sections: [
      {
        key: "roster",
        navLabel: "Roster",
        title: "Class Roster",
        subtitle: "Faculty-facing view of students, section composition, and roster review checkpoints.",
        cta: "Open roster review",
        bullets: [
          "Review student membership by class and section without entering restricted admin console routes.",
          "Use this route as the faculty-safe landing page for roster-oriented workflow steps.",
          "Keep classroom visibility, attendance context, and review tasks in a dedicated faculty zone.",
        ],
      },
      {
        key: "grades",
        navLabel: "Grades",
        title: "Grading Cycle",
        subtitle: "Instructor workspace for grading review, grade submission readiness, and verification steps.",
        cta: "Review grading cycle",
        bullets: [
          "Track grading deadlines and finalization checkpoints for the current teaching period.",
          "Use faculty-safe grading guidance without falling into admin-only console views.",
          "Coordinate grade verification and instructional review actions from one place.",
        ],
      },
      {
        key: "schedule",
        navLabel: "Schedule",
        title: "Teaching Schedule",
        subtitle: "Faculty schedule surface for section timing, teaching load awareness, and classroom coordination.",
        cta: "Open teaching schedule",
        bullets: [
          "Review section timing, instructional windows, and coordination dependencies.",
          "Keep faculty schedule workflows inside the faculty portal instead of console-only pages.",
          "Use this page as the route-safe entry point for teaching timetable review.",
        ],
      },
      {
        key: "operations",
        navLabel: "Operations",
        title: "Academic Operations",
        subtitle: "Operational summary for faculty-impacting academic events, alerts, and follow-up actions.",
        cta: "Open operations summary",
        bullets: [
          "Surface the operational items that matter to instructors without exposing broad admin console capabilities.",
          "Review teaching-impacting alerts, dependencies, and coordination notes.",
          "Use this route-safe summary as the faculty portal replacement for console operations tabs.",
        ],
      },
    ],
  },
  registrar: {
    roleKey: "registrar",
    roleLabel: "Registrar Zone",
    zoneTitle: "Registrar Zone",
    title: "Registrar and Dean Office",
    subtitle: "Academic governance surface for admissions control, policy review, and evidence-driven registrar operations.",
    accentFrom: "#4c1d95",
    accentTo: "#7c2d12",
    sections: [
      {
        key: "admissions",
        navLabel: "Admissions",
        title: "Admissions Coordination",
        subtitle: "Registrar-facing intake oversight for applicant flow, decision timing, and document completeness.",
        cta: "Review admissions operations",
        bullets: [
          "Track applicant funnel state and stage transitions that require registrar approval.",
          "Monitor document completeness and unresolved institutional intake blockers.",
          "Coordinate decision windows with enrollment readiness and downstream record creation.",
        ],
      },
      {
        key: "governance",
        navLabel: "Governance",
        title: "Institution Governance",
        subtitle: "Operational governance surface for institutional policy, tenant readiness, and compliance checkpoints.",
        cta: "Open governance review",
        bullets: [
          "Review institution-level policy checkpoints that affect registrar operations.",
          "Verify readiness signals before operational changes are rolled into academic workflows.",
          "Keep governance evidence close to the registrar workflow instead of sending users into console-only routes.",
        ],
      },
      {
        key: "audit",
        navLabel: "Audit",
        title: "Audit and Evidence",
        subtitle: "Evidence-focused workspace for operational review, traceability, and registrar-side control checks.",
        cta: "Inspect evidence trail",
        bullets: [
          "Review the audit trail used for registrar approvals and academic record interventions.",
          "Validate change history before escalating exceptions to administration or compliance teams.",
          "Keep a clean separation between registrar evidence review and platform-only console access.",
        ],
      },
      {
        key: "controls",
        navLabel: "Controls",
        title: "Platform Controls",
        subtitle: "Read-only operational control surface summarizing safeguards that affect registrar workflows.",
        cta: "View operating controls",
        bullets: [
          "Understand which platform controls currently gate registrar-facing workflows and releases.",
          "Review guardrails, runtime checks, and escalation paths without requiring platform console privileges.",
          "Use this space as the registrar-safe landing page for controls previously linked to restricted console routes.",
        ],
      },
    ],
  },
};

export function getRolePortalConfig(roleKey: RolePortalKey): RolePortalConfig {
  return ROLE_PORTAL_CONFIGS[roleKey];
}

export function getRolePortalSection(roleKey: RolePortalKey, sectionKey: string): RolePortalSectionConfig | null {
  return ROLE_PORTAL_CONFIGS[roleKey].sections.find((section) => section.key === sectionKey) ?? null;
}

export function getRolePortalNavItems(roleKey: RolePortalKey): Array<{ href: string; label: string }> {
  const config = ROLE_PORTAL_CONFIGS[roleKey];
  return [
    { href: `/${roleKey}`, label: "Home" },
    ...config.sections.map((section) => ({ href: `/${roleKey}/${section.key}`, label: section.navLabel })),
  ];
}

export function getRolePortalHomeCards(roleKey: RolePortalKey): PortalCard[] {
  return ROLE_PORTAL_CONFIGS[roleKey].sections.map((section) => ({
    title: section.title,
    description: section.subtitle,
    href: `/${roleKey}/${section.key}`,
    cta: section.cta,
  }));
}