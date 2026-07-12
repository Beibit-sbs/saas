import { notFound } from "next/navigation";
import { RolePortalSectionView } from "@/app/components/role-portal-section-view";
import { getRolePortalSection } from "@/app/components/role-portal-registry";

type FacultySectionPageProps = {
  params: {
    section: string;
  };
};

export default function FacultySectionPage({ params }: FacultySectionPageProps) {
  if (!getRolePortalSection("faculty", params.section)) {
    notFound();
  }
  return <RolePortalSectionView roleKey="faculty" sectionKey={params.section} />;
}