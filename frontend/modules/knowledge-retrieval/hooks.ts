import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type {
  IngestDocumentPayload,
  IngestDocumentResponse,
  KnowledgeBaseStats,
  SemanticSearchPayload,
  SemanticSearchResponse,
} from "./types";

const BASE = "/api/admin/knowledge-retrieval";

export function useIngestDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: IngestDocumentPayload) =>
      apiPost<IngestDocumentResponse>(`${BASE}/ingest`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["kr-stats"] }),
  });
}

export function useSemanticSearch() {
  return useMutation({
    mutationFn: (payload: SemanticSearchPayload) =>
      apiPost<SemanticSearchResponse>(`${BASE}/search`, payload),
  });
}

export function useKnowledgeBaseStats() {
  return useQuery<KnowledgeBaseStats>({
    queryKey: ["kr-stats"],
    queryFn: () => apiGet<KnowledgeBaseStats>(`${BASE}/stats`),
  });
}
