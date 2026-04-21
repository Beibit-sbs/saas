export type AidType = "scholarship" | "grant" | "tuition_discount" | "stipend";

export type AidStatus = "pending" | "approved" | "disbursed" | "rejected";

export interface FinancialAidRecord {
  id: number;
  tenant_id?: string | null;
  student_id: number;
  aid_type: AidType;
  amount: number;
  currency: string;
  status: AidStatus;
  term: string;
  reviewer_id?: string | null;
  notes?: string | null;
}

export interface FinancialAidRecordListResponse {
  items: FinancialAidRecord[];
}

export interface FinancialAidRecordItemResponse {
  item: FinancialAidRecord;
}

export interface FinancialAidRecordCreatePayload {
  student_id: number;
  aid_type: AidType;
  amount: number;
  currency: string;
  term: string;
  reviewer_id?: string | null;
  notes?: string | null;
}

export interface FinancialAidStatusUpdatePayload {
  status: AidStatus;
  notes?: string | null;
}
