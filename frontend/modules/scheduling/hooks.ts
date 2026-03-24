import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { schedulingApi } from "./api";
import type { CourseSection, CreateSectionPayload } from "./types";

export const SECTIONS_KEY = "sections";

export function useSections(params?: {
  page?: number;
  page_size?: number;
  semester?: string;
  status?: string;
  tenant_id?: string;
}) {
  return useQuery({
    queryKey: [SECTIONS_KEY, params],
    queryFn: () => schedulingApi.list(params),
  });
}

export function useSection(id: string) {
  return useQuery({
    queryKey: [SECTIONS_KEY, id],
    queryFn: () => schedulingApi.get(id),
    enabled: !!id,
  });
}

export function useCreateSection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateSectionPayload) => schedulingApi.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [SECTIONS_KEY] }),
  });
}

export function useUpdateSection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<CreateSectionPayload & { status: CourseSection["status"] }> }) =>
      schedulingApi.update(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [SECTIONS_KEY] }),
  });
}
