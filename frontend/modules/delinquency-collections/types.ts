export type DelinquencyStatus =
  | "open"
  | "in_review"
  | "escalated"
  | "resolved"
  | "written_off";

export type EscalationStage = "stage_1" | "stage_2" | "stage_3" | "legal";

export interface DelinquencyRecord {
  id: number;
  tenant_id?: string | null;
  student_id: string;
  invoice_code: string;
  amount_due: number;
  days_overdue: number;
  escalation_stage: EscalationStage;
  status: DelinquencyStatus;
}

export interface DelinquencyListResponse {
  items: DelinquencyRecord[];
}

export interface DelinquencyItemResponse {
  item: DelinquencyRecord;
}

export interface DelinquencyCreatePayload {
  student_id: string;
  invoice_code: string;
  amount_due: number;
  days_overdue: number;
  escalation_stage?: EscalationStage;
  status?: DelinquencyStatus;
}

export interface DelinquencyStatusUpdatePayload {
  status: DelinquencyStatus;
}

export interface DelinquencyEscalationUpdatePayload {
  escalation_stage: EscalationStage;
}
