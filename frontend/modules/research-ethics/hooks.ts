import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import type {
  ResearchEthicsBrainContext,
  ResearchEthicsReviewListResponse,
} from "./types";

const BASE = "/api/admin/research-ethics";

export function useResearchEthicsReviews(filters?: { status?: string; risk_level?: string }) {
  return useQuery({
    queryKey: ["research-ethics:reviews", filters?.status ?? "all", filters?.risk_level ?? "all"],
    queryFn: () => apiGet<ResearchEthicsReviewListResponse>(`${BASE}/reviews`, {
      status: filters?.status,
      risk_level: filters?.risk_level,
    }),
    staleTime: 60_000,
  });
}

export function useResearchEthicsBrainContext() {
  return useQuery({
    queryKey: ["research-ethics:brain-context"],
    queryFn: () => apiGet<ResearchEthicsBrainContext>(`${BASE}/brain-context`),
    staleTime: 60_000,
  });
}
