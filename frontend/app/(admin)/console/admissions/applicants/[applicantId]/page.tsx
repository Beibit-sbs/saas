import { AdmissionsCrmPage } from "@/modules/admissions-crm/pages";

export default function Page({ params }: { params: { applicantId: string } }) {
  const applicantId = Number(params.applicantId);
  return <AdmissionsCrmPage routeKey="applicant-detail" applicantId={Number.isFinite(applicantId) ? applicantId : undefined} />;
}
