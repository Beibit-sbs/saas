import { notFound } from "next/navigation";
import { PlatformSectionView } from "../platform-section-view";
import { isPlatformSectionSlug } from "../platform-sections";

type PlatformSectionPageProps = {
  params: {
    section: string;
  };
};

export default function PlatformSectionPage({ params }: PlatformSectionPageProps) {
  if (!isPlatformSectionSlug(params.section)) {
    notFound();
  }

  return <PlatformSectionView section={params.section} />;
}
