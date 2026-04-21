export type AdvisingSessionType = "academic" | "career" | "personal" | "mentoring";

export type AdvisingSessionStatus = "scheduled" | "completed" | "cancelled" | "no_show";

export interface AdvisingSession {
  id: number;
  tenant_id?: string | null;
  student_id: number;
  advisor_id: string;
  session_type: AdvisingSessionType;
  status: AdvisingSessionStatus;
  scheduled_at?: string | null;
  notes?: string | null;
  outcome?: string | null;
}

export interface AdvisingSessionListResponse {
  items: AdvisingSession[];
}

export interface AdvisingSessionItemResponse {
  item: AdvisingSession;
}

export interface AdvisingSessionCreatePayload {
  student_id: number;
  advisor_id: string;
  session_type: AdvisingSessionType;
  scheduled_at?: string | null;
  notes?: string | null;
}

export interface AdvisingSessionStatusUpdatePayload {
  status: AdvisingSessionStatus;
  outcome?: string | null;
}
