export type ExpenseRecordStatus = "pending" | "approved" | "rejected" | "paid" | string;

export interface ExpenseRecord {
  id: number;
  tenant_id?: number | null;
  cost_center_id: number;
  category: string;
  amount: number;
  currency: string;
  status: ExpenseRecordStatus;
  description?: string | null;
  payroll_ref?: string | null;
}

export interface CostCenter {
  id: number;
  tenant_id?: number | null;
  name: string;
  code: string;
  department_id?: string | null;
  budget_limit: number;
  currency: string;
  active: boolean;
}

export interface ExpenseBrainContext {
  module: string;
  tenant_id: number;
  total_expenses: number;
  total_cost_centers: number;
  pending_expenses: number;
  approved_expenses: number;
  budget_exceeded_alerts: number;
  risk_level: "low" | "medium" | "high" | string;
}

export interface ExpenseRecordsResponse {
  records: ExpenseRecord[];
}

export interface CostCentersResponse {
  records: CostCenter[];
}

export interface ExpenseRecordItemResponse {
  record: ExpenseRecord;
}

export interface CostCenterItemResponse {
  record: CostCenter;
}

export interface CostCenterCreatePayload {
  name: string;
  code: string;
  department_id?: string;
  budget_limit: number;
  currency?: string;
  active?: boolean;
}

export interface ExpenseRecordCreatePayload {
  cost_center_id: number;
  category: string;
  amount: number;
  currency?: string;
  status?: string;
  description?: string;
  payroll_ref?: string;
}
