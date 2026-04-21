/**
 * React Query hooks for Academic Integrity module API communication.
 */

"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  IntegrityCase,
  IntegrityCaseCreateRequest,
  IntegrityCaseStatusUpdate,
  IntegrityCaseListResponse,
  IntegrityCaseDetailResponse,
} from "./types";

const API_BASE = "/api/admin/academic-integrity";

export function useIntegrityCases(page = 1, pageSize = 20, studentId?: string, status?: string) {
  return useQuery({
    queryKey: ["integrity-cases", page, pageSize, studentId, status],
    queryFn: async (): Promise<IntegrityCaseListResponse> => {
      const params = new URLSearchParams();
      params.set("page", page.toString());
      params.set("page_size", pageSize.toString());
      if (studentId) params.set("student_id", studentId);
      if (status) params.set("status", status);

      const response = await fetch(`${API_BASE}/cases?${params.toString()}`, {
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch cases: ${response.statusText}`);
      }

      return response.json();
    },
  });
}

export function useIntegrityCase(caseId: string) {
  return useQuery({
    queryKey: ["integrity-case", caseId],
    queryFn: async (): Promise<IntegrityCaseDetailResponse> => {
      const response = await fetch(`${API_BASE}/cases/${caseId}`, {
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch case: ${response.statusText}`);
      }

      return response.json();
    },
    enabled: !!caseId,
  });
}

export function useCreateIntegrityCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: IntegrityCaseCreateRequest): Promise<IntegrityCaseDetailResponse> => {
      const response = await fetch(`${API_BASE}/cases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`Failed to create case: ${response.statusText}`);
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrity-cases"] });
    },
  });
}

export function useUpdateIntegrityCaseStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ caseId, ...payload }: IntegrityCaseStatusUpdate & { caseId: string }): Promise<IntegrityCaseDetailResponse> => {
      const response = await fetch(`${API_BASE}/cases/${caseId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`Failed to update case status: ${response.statusText}`);
      }

      return response.json();
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["integrity-cases"] });
      queryClient.invalidateQueries({ queryKey: ["integrity-case", variables.caseId] });
    },
  });
}
