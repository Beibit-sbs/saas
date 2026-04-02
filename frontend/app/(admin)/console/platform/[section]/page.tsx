import { notFound } from "next/navigation";
import { PlatformSectionView } from "../platform-section-view";
import { PLATFORM_SECTION_TO_TAB, isPlatformSectionSlug } from "../platform-sections";

type PlatformSectionPageProps = {
  params: {
    section: string;
  };
};

export default function PlatformSectionPage({ params }: PlatformSectionPageProps) {
  if (!isPlatformSectionSlug(params.section)) {
    notFound();
  }

  return <PlatformSectionView tab={PLATFORM_SECTION_TO_TAB[params.section]} />;
}
