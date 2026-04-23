import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type {
  HrEmployeeCreatePayload,
  HrEmployeeItemResponse,
  HrEmployeeListResponse,
  HrEmployeeStatus,
  HrEmployeeStatusUpdatePayload,
  PayrollCycleCreatePayload,
  PayrollCycleItemResponse,
  PayrollCycleListResponse,
  PayrollCycleStatus,
  PayrollCycleStatusUpdatePayload,
} from "./types";

const BASE = "/api/admin/hr-payroll";
const EMPLOYEE_KEY = "hr-employees";
const CYCLE_KEY = "hr-payroll-cycles";

export function useHrEmployees(filters?: {
  status?: HrEmployeeStatus;
  department_id?: string;
}) {
  const params: Record<string, string> = {};
  if (filters?.status) params.status = filters.status;
  if (filters?.department_id) params.department_id = filters.department_id;

  return useQuery({
    queryKey: [EMPLOYEE_KEY, filters?.status ?? "all", filters?.department_id ?? "all"],
    queryFn: () =>
      apiGet<HrEmployeeListResponse>(
        `${BASE}/employees`,
        Object.keys(params).length > 0 ? params : undefined,
      ),
  });
}

export function useCreateHrEmployee() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: HrEmployeeCreatePayload) =>
      apiPost<HrEmployeeItemResponse>(`${BASE}/employees`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [EMPLOYEE_KEY] }),
  });
}

export function useUpdateHrEmployeeStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      employeeId,
      payload,
    }: {
      employeeId: number;
      payload: HrEmployeeStatusUpdatePayload;
    }) =>
      apiPatch<HrEmployeeItemResponse>(`${BASE}/employees/${employeeId}/status`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [EMPLOYEE_KEY] }),
  });
}

export function usePayrollCycles(status?: PayrollCycleStatus) {
  const params: Record<string, string> = {};
  if (status) params.status = status;

  return useQuery({
    queryKey: [CYCLE_KEY, status ?? "all"],
    queryFn: () =>
      apiGet<PayrollCycleListResponse>(
        `${BASE}/cycles`,
        Object.keys(params).length > 0 ? params : undefined,
      ),
  });
}

export function useCreatePayrollCycle() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: PayrollCycleCreatePayload) =>
      apiPost<PayrollCycleItemResponse>(`${BASE}/cycles`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [CYCLE_KEY] }),
  });
}

export function useUpdatePayrollCycleStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      cycleId,
      payload,
    }: {
      cycleId: number;
      payload: PayrollCycleStatusUpdatePayload;
    }) =>
      apiPatch<PayrollCycleItemResponse>(`${BASE}/cycles/${cycleId}/status`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [CYCLE_KEY] }),
  });
}
