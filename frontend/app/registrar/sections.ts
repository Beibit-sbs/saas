import type { PortalCard } from "@/app/components/role-portal-shell";

export type RegistrarSectionKey = "admissions" | "governance" | "audit" | "controls";

export type RegistrarSection = {
  key: RegistrarSectionKey;
  navLabel: string;
  title: string;
  subtitle: string;
  cta: string;
  bullets: string[];
};

export const REGISTRAR_SECTIONS: Record<RegistrarSectionKey, RegistrarSection> = {
  admissions: {
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
  governance: {
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
  audit: {
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
  controls: {
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
};

export const REGISTRAR_NAV_ITEMS = [
  { href: "/registrar", label: "Home" },
  { href: "/registrar/admissions", label: REGISTRAR_SECTIONS.admissions.navLabel },
  { href: "/registrar/governance", label: REGISTRAR_SECTIONS.governance.navLabel },
  { href: "/registrar/audit", label: REGISTRAR_SECTIONS.audit.navLabel },
  { href: "/registrar/controls", label: REGISTRAR_SECTIONS.controls.navLabel },
] as const;

export const REGISTRAR_HOME_CARDS: PortalCard[] = [
  {
    title: REGISTRAR_SECTIONS.admissions.title,
    description: REGISTRAR_SECTIONS.admissions.subtitle,
    href: "/registrar/admissions",
    cta: REGISTRAR_SECTIONS.admissions.cta,
  },
  {
    title: REGISTRAR_SECTIONS.governance.title,
    description: REGISTRAR_SECTIONS.governance.subtitle,
    href: "/registrar/governance",
    cta: REGISTRAR_SECTIONS.governance.cta,
  },
  {
    title: REGISTRAR_SECTIONS.audit.title,
    description: REGISTRAR_SECTIONS.audit.subtitle,
    href: "/registrar/audit",
    cta: REGISTRAR_SECTIONS.audit.cta,
  },
  {
    title: REGISTRAR_SECTIONS.controls.title,
    description: REGISTRAR_SECTIONS.controls.subtitle,
    href: "/registrar/controls",
    cta: REGISTRAR_SECTIONS.controls.cta,
  },
];