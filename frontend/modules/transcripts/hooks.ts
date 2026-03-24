import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import type { Transcript } from "./types";

export function useTranscript(studentId: string) {
  return useQuery({
    queryKey: ["transcripts", studentId],
    queryFn: () => apiGet<Transcript>(`/api/admin/students/${studentId}/transcript`),
    enabled: !!studentId,
  });
}
