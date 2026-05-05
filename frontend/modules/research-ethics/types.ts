export interface ResearchEthicsReviewRecord {
  id: number;
  tenant_id: number;
  review_code: string;
  project_title: string;
  principal_investigator_id: string;
  review_type: string;
  status: string;
  submission_date?: string | null;
  decision_date?: string | null;
  risk_level?: string | null;
  notes?: string | null;
  integration_source?: string | null;
  committee_name?: string | null;
}

export interface ResearchEthicsReviewListResponse {
  records: ResearchEthicsReviewRecord[];
}

export interface ResearchEthicsBrainContext {
  module: string;
  tenant_id: number;
  total_reviews: number;
  pending_reviews: number;
  approved_reviews: number;
  rejected_reviews: number;
  high_risk_reviews: number;
  compliance_status: string;
}
