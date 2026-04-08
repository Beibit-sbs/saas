import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type { Transcript, TranscriptSnapshot } from "./types";

export const TRANSCRIPTS_KEY = "transcripts";

export function useTranscript(studentId: string) {
  return useQuery({
    queryKey: [TRANSCRIPTS_KEY, studentId],
    queryFn: () => apiGet<Transcript>(`/api/admin/students/${studentId}/transcript`),
    enabled: !!studentId,
  });
}

export function useCreateTranscriptSnapshot(studentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiPost<TranscriptSnapshot>(`/api/admin/students/${studentId}/transcript/snapshot`),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: [TRANSCRIPTS_KEY, studentId] });
    },
  });
}
