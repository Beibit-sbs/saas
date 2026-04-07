import { RolePortalShell } from "@/app/components/role-portal-shell";

export default function FacultyPortalPage() {
  return (
    <RolePortalShell
      roleKey="faculty"
      roleLabel="Faculty Zone"
      title="Faculty Portal"
      subtitle="Workspace for instructors to run roster operations, grading cycles, and teaching schedule decisions."
      accentFrom="#7c2d12"
      accentTo="#0f766e"
      cards={[
        {
          title: "Class Roster",
          description: "Inspect student roster state, profile details, and section-level enrollment composition.",
          href: "/console/students",
          cta: "Open roster",
        },
        {
          title: "Grading Cycle",
          description: "Submit grade updates and verify recent changes before final lock in period close.",
          href: "/console/grades",
          cta: "Manage grades",
        },
        {
          title: "Teaching Schedule",
          description: "Review schedule windows, teaching assignments, and timing constraints per section.",
          href: "/console/scheduling",
          cta: "Open scheduling",
        },
        {
          title: "Academic Operations",
          description: "Track operational alerts and activity events that impact faculty workflows.",
          href: "/console/ops",
          cta: "View ops",
        },
      ]}
    />
  );
}
