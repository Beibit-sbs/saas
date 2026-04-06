import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import { interventionsApi } from "./api";
import type {
  AddInterventionActionPayload,
  AssignInterventionPayload,
  UpdateInterventionStatusPayload,
} from "./types";

export const INTERVENTIONS_KEY = "interventions";

export function useInterventionCases(params?: {
  page?: number;
  page_size?: number;
  status?: string;
  severity?: string;
  assignee_ref?: string;
  overdue_only?: boolean;
}) {
  return useQuery({
    queryKey: [INTERVENTIONS_KEY, "cases", params],
    queryFn: () => interventionsApi.listCases(params),
    refetchInterval: 15_000,
  });
}

export function useInterventionCase(id: string) {
  return useQuery({
    queryKey: [INTERVENTIONS_KEY, "case", id],
    queryFn: () => interventionsApi.getCase(id),
    enabled: Boolean(id),
    refetchInterval: 10_000,
  });
}

export function useInterventionActions(caseId: string, limit = 20) {
  return useQuery({
    queryKey: [INTERVENTIONS_KEY, "actions", caseId, limit],
    queryFn: () => interventionsApi.listActions(caseId, limit),
    enabled: Boolean(caseId),
    refetchInterval: 15_000,
  });
}

function useInvalidateInterventions() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: [INTERVENTIONS_KEY] });
}

export function useTakeInterventionCase() {
  const invalidate = useInvalidateInterventions();
  return useMutation({
    mutationFn: ({ id, expectedVersion }: { id: string; expectedVersion: number }) => interventionsApi.takeCase(id, expectedVersion),
    onSuccess: invalidate,
  });
}

export function useAssignInterventionCase() {
  const invalidate = useInvalidateInterventions();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: AssignInterventionPayload }) => interventionsApi.assignCase(id, body),
    onSuccess: invalidate,
  });
}

export function useUpdateInterventionStatus() {
  const invalidate = useInvalidateInterventions();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateInterventionStatusPayload }) => interventionsApi.updateStatus(id, body),
    onSuccess: invalidate,
  });
}

export function useAddInterventionAction() {
  const invalidate = useInvalidateInterventions();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: AddInterventionActionPayload }) => interventionsApi.addAction(id, body),
    onSuccess: invalidate,
  });
}

// ---------------------------------------------------------------------------
// Student name lookup for intervention drawer (chains 2 requests)
// ---------------------------------------------------------------------------

type StudentProfileStub = { person_id: number };
type PersonStub = { first_name: string; last_name: string; email: string };

export function useStudentName(studentProfileId: string | null) {
  const profileQuery = useQuery<StudentProfileStub>({
    queryKey: ["student-profile", studentProfileId],
    queryFn: () => apiGet<StudentProfileStub>(`/api/admin/students/${studentProfileId}`),
    enabled: Boolean(studentProfileId),
    staleTime: 5 * 60_000,
    retry: false,
  });

  const personId = profileQuery.data?.person_id ?? null;
  const personQuery = useQuery<PersonStub>({
    queryKey: ["person", personId],
    queryFn: () => apiGet<PersonStub>(`/api/admin/profiles/people/${personId}`),
    enabled: Boolean(personId),
    staleTime: 5 * 60_000,
    retry: false,
  });

  const name = personQuery.data
    ? `${personQuery.data.first_name} ${personQuery.data.last_name}`.trim()
    : null;

  return {
    name,
    email: personQuery.data?.email ?? null,
    isLoading: profileQuery.isLoading || personQuery.isLoading,
  };
}
