import { DocumentAuditPage } from '@/modules/document-workflow/components/pages';

export default function Page({ params }: { params: { id: string } }) {
  return <DocumentAuditPage id={params.id} />;
}