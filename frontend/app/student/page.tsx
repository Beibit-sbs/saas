import { RolePortalShell } from "@/app/components/role-portal-shell";

export default function StudentPortalPage() {
  return (
    <RolePortalShell
      roleKey="student"
      roleLabel="Student Zone"
      title="Student Portal"
      subtitle="Self-service area for registration, grades, and personal academic progress across the current term."
      accentFrom="#0f766e"
      accentTo="#1d4ed8"
      cards={[
        {
          title: "Enrollment Requests",
          description: "Add or drop subjects, then track approval and waitlist state for the active term.",
          href: "/console/enrollments",
          cta: "Manage enrollment",
        },
        {
          title: "Grades and Progress",
          description: "Review current gradebook outcomes and monitor GPA trend before transcript export.",
          href: "/console/grades",
          cta: "Open grades",
        },
        {
          title: "Academic Transcript",
          description: "Open transcript details and verify historical records before advisor submission.",
          href: "/console/transcripts",
          cta: "View transcript",
        },
        {
          title: "Profile and Preferences",
          description: "Update personal profile details and communication language for account operations.",
          href: "/profile",
          cta: "Open profile",
        },
      ]}
    />
  );
}
