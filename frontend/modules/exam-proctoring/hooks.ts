/**
 * Exam Proctoring Hooks
 * React Query hooks for proctoring session oversight.
 * Reuses the exam-governance API backend — no new endpoints required.
 */

import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import type { ProctoredExamListResponse } from "./types";

const GOVERNANCE_BASE = "/api/admin/exam-governance";

/**
 * Fetches the list of proctored exams for oversight.
 * Reuses the exam-governance list endpoint, filtered to proctored sessions.
 */
export function useProctoredExamsList(filters?: {
  status?: string;
  term_id?: string;
}) {
  return useQuery({
    queryKey: ["exam-proctoring:sessions", filters?.status ?? "all", filters?.term_id ?? ""],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append("status", filters.status);
      if (filters?.term_id) params.append("term_id", filters.term_id);
      return apiGet<ProctoredExamListResponse>(
        `${GOVERNANCE_BASE}?${params.toString()}`
      );
    },
    staleTime: 60_000,
    select: (data) => ({
      ...data,
      items: data.items.filter((item) => item.is_proctored),
    }),
  });
}

/**
 * Fetches the exam governance dashboard summary for the proctoring summary cards.
 */
export function useExamProctoringDashboard() {
  return useQuery({
    queryKey: ["exam-proctoring:dashboard"],
    queryFn: () =>
      apiGet<{
        total_exams: number;
        status_breakdown: Record<string, number>;
      }>(`${GOVERNANCE_BASE}/dashboard/summary`),
    staleTime: 60_000,
  });
}
