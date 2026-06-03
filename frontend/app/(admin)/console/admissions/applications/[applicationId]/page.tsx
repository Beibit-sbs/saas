import { AdmissionsCrmPage } from "@/modules/admissions-crm/pages";

export default function Page({ params }: { params: { applicationId: string } }) {
  const applicationId = Number(params.applicationId);
  return <AdmissionsCrmPage routeKey="application-detail" applicationId={Number.isFinite(applicationId) ? applicationId : undefined} />;
}
