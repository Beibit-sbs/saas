export type ResearchGrantStatus = "planned" | "active" | "submitted" | "delayed" | "closed";

export interface ResearchGrant {
  id: number;
  tenant_id?: string | null;
  grant_code: string;
  title: string;
  pi_faculty_id: string;
  deadline: string;
  funding_amount: number;
  status: ResearchGrantStatus;
}

export interface ResearchGrantListResponse {
  items: ResearchGrant[];
}

export interface ResearchGrantItemResponse {
  item: ResearchGrant;
}

export interface ResearchGrantCreatePayload {
  grant_code: string;
  title: string;
  pi_faculty_id: string;
  deadline: string;
  funding_amount: number;
  status?: ResearchGrantStatus;
}

export interface ResearchGrantStatusUpdatePayload {
  status: ResearchGrantStatus;
}
