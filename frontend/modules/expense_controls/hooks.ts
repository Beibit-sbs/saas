import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type {
  CostCenterCreatePayload,
  CostCenterItemResponse,
  CostCentersResponse,
  ExpenseBrainContext,
  ExpenseRecordCreatePayload,
  ExpenseRecordItemResponse,
  ExpenseRecordsResponse,
} from "./types";

const BASE = "/api/admin/expense-controls";
const KEY = "expense-controls";

export function useExpenseRecords(filters?: {
  cost_center_id?: number;
  status?: string;
}) {
  return useQuery({
    queryKey: [KEY, "expenses", filters ?? {}],
    queryFn: () => {
      const params = new URLSearchParams();
      if (typeof filters?.cost_center_id === "number") {
        params.set("cost_center_id", String(filters.cost_center_id));
      }
      if (filters?.status) {
        params.set("status", filters.status);
      }

      const query = params.toString();
      const url = query.length > 0 ? `${BASE}/expenses?${query}` : `${BASE}/expenses`;
      return apiGet<ExpenseRecordsResponse>(url);
    },
  });
}

export function useCostCenters(filters?: { active?: boolean }) {
  return useQuery({
    queryKey: [KEY, "cost-centers", filters ?? {}],
    queryFn: () => {
      const params = new URLSearchParams();
      if (typeof filters?.active === "boolean") {
        params.set("active", String(filters.active));
      }

      const query = params.toString();
      const url = query.length > 0 ? `${BASE}/cost-centers?${query}` : `${BASE}/cost-centers`;
      return apiGet<CostCentersResponse>(url);
    },
  });
}

export function useExpenseBrainContext() {
  return useQuery({
    queryKey: [KEY, "brain-context"],
    queryFn: () => apiGet<ExpenseBrainContext>(`${BASE}/brain-context`),
  });
}

export function useCreateCostCenter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CostCenterCreatePayload) =>
      apiPost<CostCenterItemResponse>(`${BASE}/cost-centers`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEY] });
    },
  });
}

export function useCreateExpenseRecord() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ExpenseRecordCreatePayload) =>
      apiPost<ExpenseRecordItemResponse>(`${BASE}/expenses`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEY] });
    },
  });
}
