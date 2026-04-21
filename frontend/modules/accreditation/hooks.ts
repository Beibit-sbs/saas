"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type {
  AccreditationCreatePayload,
  AccreditationItemResponse,
  AccreditationListResponse,
  AccreditationStandardType,
  AccreditationStatus,
  AccreditationStatusUpdatePayload,
} from "./types";

const BASE = "/api/admin/accreditation-compliance";
const ACCREDITATION_KEY = "accreditation-records";

export function useAccreditation(
  status?: AccreditationStatus,
  standardType?: AccreditationStandardType,
) {
  return useQuery({
    queryKey: [ACCREDITATION_KEY, status ?? "all", standardType ?? "all"],
    queryFn: async (): Promise<AccreditationListResponse> => {
      const params = new URLSearchParams();
      if (status) {
        params.set("status", status);
      }
      if (standardType) {
        params.set("standard_type", standardType);
      }
      const query = params.toString();
      const response = await fetch(query ? `${BASE}?${query}` : BASE, { credentials: "include" });
      if (!response.ok) {
        throw new Error(`Failed to fetch accreditation records: ${response.statusText}`);
      }
      return response.json();
    },
  });
}

export function useCreateAccreditation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: AccreditationCreatePayload): Promise<AccreditationItemResponse> => {
      const response = await fetch(BASE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error(`Failed to create accreditation record: ${response.statusText}`);
      }
      return response.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: [ACCREDITATION_KEY] }),
  });
}

export function useUpdateAccreditationStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      recordId,
      payload,
    }: {
      recordId: number;
      payload: AccreditationStatusUpdatePayload;
    }): Promise<AccreditationItemResponse> => {
      const response = await fetch(`${BASE}/${recordId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error(`Failed to update accreditation status: ${response.statusText}`);
      }
      return response.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: [ACCREDITATION_KEY] }),
  });
}
