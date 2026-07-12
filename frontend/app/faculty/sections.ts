import type { PortalCard } from "@/app/components/role-portal-shell";

export type FacultySectionKey = "roster" | "grades" | "schedule" | "operations";

export type FacultySection = {
  key: FacultySectionKey;
  navLabel: string;
  title: string;
  subtitle: string;
  cta: string;
  bullets: string[];
};

export const FACULTY_SECTIONS: Record<FacultySectionKey, FacultySection> = {
  roster: {
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
  grades: {
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
  schedule: {
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
  operations: {
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
};

export const FACULTY_NAV_ITEMS = [
  { href: "/faculty", label: "Home" },
  { href: "/faculty/roster", label: FACULTY_SECTIONS.roster.navLabel },
  { href: "/faculty/grades", label: FACULTY_SECTIONS.grades.navLabel },
  { href: "/faculty/schedule", label: FACULTY_SECTIONS.schedule.navLabel },
  { href: "/faculty/operations", label: FACULTY_SECTIONS.operations.navLabel },
] as const;

export const FACULTY_HOME_CARDS: PortalCard[] = [
  {
    title: FACULTY_SECTIONS.roster.title,
    description: FACULTY_SECTIONS.roster.subtitle,
    href: "/faculty/roster",
    cta: FACULTY_SECTIONS.roster.cta,
  },
  {
    title: FACULTY_SECTIONS.grades.title,
    description: FACULTY_SECTIONS.grades.subtitle,
    href: "/faculty/grades",
    cta: FACULTY_SECTIONS.grades.cta,
  },
  {
    title: FACULTY_SECTIONS.schedule.title,
    description: FACULTY_SECTIONS.schedule.subtitle,
    href: "/faculty/schedule",
    cta: FACULTY_SECTIONS.schedule.cta,
  },
  {
    title: FACULTY_SECTIONS.operations.title,
    description: FACULTY_SECTIONS.operations.subtitle,
    href: "/faculty/operations",
    cta: FACULTY_SECTIONS.operations.cta,
  },
];