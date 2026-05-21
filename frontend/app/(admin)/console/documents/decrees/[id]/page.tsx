import { DecreeDetailPage } from '@/modules/document-workflow/components/pages';

export default function Page({ params }: { params: { id: string } }) {
  return <DecreeDetailPage id={params.id} />;
}