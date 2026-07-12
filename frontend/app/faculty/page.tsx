import { RolePortalShell } from "@/app/components/role-portal-shell";
import { FACULTY_HOME_CARDS } from "./sections";

export default function FacultyPortalPage() {
  return (
    <RolePortalShell
      roleKey="faculty"
      roleLabel="Faculty Zone"
      title="Faculty Portal"
      subtitle="Workspace for instructors to run roster review, grading cycles, and teaching schedule decisions."
      accentFrom="#7c2d12"
      accentTo="#0f766e"
      cards={FACULTY_HOME_CARDS}
    />
  );
}
