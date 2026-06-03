import { AdmissionsCrmPage } from "@/modules/admissions-crm/pages";

export default function Page({ params }: { params: { leadId: string } }) {
  const leadId = Number(params.leadId);
  return <AdmissionsCrmPage routeKey="lead-detail" leadId={Number.isFinite(leadId) ? leadId : undefined} />;
}
