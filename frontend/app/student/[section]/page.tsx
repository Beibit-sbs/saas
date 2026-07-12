import { notFound } from "next/navigation";
import { RolePortalSectionView } from "@/app/components/role-portal-section-view";
import { getRolePortalSection } from "@/app/components/role-portal-registry";

type StudentSectionPageProps = {
  params: {
    section: string;
  };
};

export default function StudentSectionPage({ params }: StudentSectionPageProps) {
  if (!getRolePortalSection("student", params.section)) {
    notFound();
  }
  return <RolePortalSectionView roleKey="student" sectionKey={params.section} />;
}