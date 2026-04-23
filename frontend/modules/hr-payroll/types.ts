export type HrEmployeeStatus =
  | "active"
  | "on_leave"
  | "terminated"
  | "onboarding"
  | "offboarding";

export type PayrollCycleStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed";

export interface HrEmployee {
  id: number;
  tenant_id?: string | null;
  employee_code: string;
  full_name: string;
  department_id: string;
  role_title: string;
  status: HrEmployeeStatus;
}

export interface PayrollCycle {
  id: number;
  tenant_id?: string | null;
  cycle_code: string;
  period_label: string;
  total_gross: number;
  total_net: number;
  employee_count: number;
  status: PayrollCycleStatus;
}

export interface HrEmployeeListResponse {
  items: HrEmployee[];
}

export interface HrEmployeeItemResponse {
  item: HrEmployee;
}

export interface PayrollCycleListResponse {
  items: PayrollCycle[];
}

export interface PayrollCycleItemResponse {
  item: PayrollCycle;
}

export interface HrEmployeeCreatePayload {
  employee_code: string;
  full_name: string;
  department_id: string;
  role_title: string;
  status?: HrEmployeeStatus;
}

export interface HrEmployeeStatusUpdatePayload {
  status: HrEmployeeStatus;
}

export interface PayrollCycleCreatePayload {
  cycle_code: string;
  period_label: string;
  total_gross: number;
  total_net: number;
  employee_count: number;
  status?: PayrollCycleStatus;
}

export interface PayrollCycleStatusUpdatePayload {
  status: PayrollCycleStatus;
}
