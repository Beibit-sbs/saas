import { DocumentDetailPage } from '@/modules/document-workflow/components/pages';

export default function Page({ params }: { params: { id: string } }) {
  return <DocumentDetailPage id={params.id} />;
}