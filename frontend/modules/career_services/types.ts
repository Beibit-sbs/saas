export type CareerOpportunityType = "internship" | "job" | "mentorship" | "work_study";

export type CareerOpportunityStatus = "open" | "in_review" | "closed" | "archived";

export interface CareerOpportunity {
  id: number;
  tenant_id?: string | null;
  student_id: number;
  title: string;
  company: string;
  opportunity_type: CareerOpportunityType;
  status: CareerOpportunityStatus;
  owner_id?: string | null;
  start_date?: string | null;
  notes?: string | null;
}

export interface CareerOpportunityListResponse {
  items: CareerOpportunity[];
}

export interface CareerOpportunityItemResponse {
  item: CareerOpportunity;
}

export interface CareerOpportunityCreatePayload {
  student_id: number;
  title: string;
  company: string;
  opportunity_type: CareerOpportunityType;
  owner_id?: string | null;
  start_date?: string | null;
  notes?: string | null;
}

export interface CareerOpportunityStatusUpdatePayload {
  status: CareerOpportunityStatus;
  notes?: string | null;
}
