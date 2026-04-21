export type ThesisStatus =
  | "draft"
  | "submitted"
  | "under_review"
  | "approved"
  | "rejected"
  | "defended";

export interface ThesisRecord {
  id: number;
  tenant_id?: string | null;
  thesis_code: string;
  student_id: number;
  title: string;
  advisor_faculty_id?: string | null;
  status: ThesisStatus;
  defense_date?: string | null;
  repository_url?: string | null;
}

export interface ThesisListResponse {
  items: ThesisRecord[];
}

export interface ThesisItemResponse {
  item: ThesisRecord;
}

export interface ThesisCreatePayload {
  thesis_code: string;
  student_id: number;
  title: string;
  advisor_faculty_id?: string;
  repository_url?: string;
}

export interface ThesisStatusUpdatePayload {
  status: ThesisStatus;
  defense_date?: string;
}
