export type AlumniStatus = "active" | "engaged" | "donor" | "inactive";

export type AlumniEngagementType = "mentoring" | "event" | "donation" | "referral";

export interface AlumniRecord {
  id: number;
  tenant_id?: string | null;
  student_id: number;
  graduation_year: number;
  status: AlumniStatus;
  engagement_type: AlumniEngagementType;
  employer?: string | null;
  contact_email?: string | null;
  notes?: string | null;
}

export interface AlumniRecordListResponse {
  items: AlumniRecord[];
}

export interface AlumniRecordItemResponse {
  item: AlumniRecord;
}

export interface AlumniRecordCreatePayload {
  student_id: number;
  graduation_year: number;
  engagement_type: AlumniEngagementType;
  employer?: string | null;
  contact_email?: string | null;
  notes?: string | null;
}

export interface AlumniStatusUpdatePayload {
  status: AlumniStatus;
  notes?: string | null;
}
