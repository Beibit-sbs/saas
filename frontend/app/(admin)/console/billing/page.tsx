import { redirect } from "next/navigation";

export default function BillingIndexPage() {
  redirect("/console/billing/plans");
}
