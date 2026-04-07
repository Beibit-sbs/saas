import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { admissionsApi } from "./api";
import type {
  ApplicationStage,
  CreateApplicantPayload,
  CreateApplicationPayload,
  MakeDecisionPayload,
  StageTransitionPayload,
} from "./types";

const APPLICANTS_KEY = "admissions-applicants";
const APPLICATIONS_KEY = "admissions-applications";

function useInvalidateApplicants() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: [APPLICANTS_KEY] });
}

function useInvalidateApplications() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: [APPLICATIONS_KEY] });
}

// ---------------------------------------------------------------------------
// Applicants
// ---------------------------------------------------------------------------

export function useApplicants(params?: {
  program_id?: number;
  application_year?: number;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: [APPLICANTS_KEY, "list", params],
    queryFn: () => admissionsApi.listApplicants(params),
    refetchInterval: 30_000,
  });
}

export function useApplicant(id: number | null) {
  return useQuery({
    queryKey: [APPLICANTS_KEY, "detail", id],
    queryFn: () => admissionsApi.getApplicant(id!),
    enabled: id !== null,
  });
}

export function useCreateApplicant() {
  const invalidate = useInvalidateApplicants();
  return useMutation({
    mutationFn: (data: CreateApplicantPayload) => admissionsApi.createApplicant(data),
    onSuccess: invalidate,
  });
}

export function useUpdateApplicant() {
  const invalidate = useInvalidateApplicants();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CreateApplicantPayload> }) =>
      admissionsApi.updateApplicant(id, data),
    onSuccess: invalidate,
  });
}

// ---------------------------------------------------------------------------
// Applications
// ---------------------------------------------------------------------------

export function useApplications(params?: {
  program_id?: number;
  stage?: ApplicationStage;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: [APPLICATIONS_KEY, "list", params],
    queryFn: () => admissionsApi.listApplications(params),
    refetchInterval: 30_000,
  });
}

export function useApplication(id: number | null) {
  return useQuery({
    queryKey: [APPLICATIONS_KEY, "detail", id],
    queryFn: () => admissionsApi.getApplication(id!),
    enabled: id !== null,
  });
}

export function useCreateApplication() {
  const invalidate = useInvalidateApplications();
  return useMutation({
    mutationFn: (data: CreateApplicationPayload) => admissionsApi.createApplication(data),
    onSuccess: invalidate,
  });
}

export function useSubmitApplication() {
  const invalidate = useInvalidateApplications();
  return useMutation({
    mutationFn: ({ id, expectedVersion }: { id: number; expectedVersion: number }) =>
      admissionsApi.submitApplication(id, expectedVersion),
    onSuccess: invalidate,
  });
}

export function useTransitionStage() {
  const invalidate = useInvalidateApplications();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: StageTransitionPayload }) =>
      admissionsApi.transitionStage(id, data),
    onSuccess: invalidate,
  });
}

export function useMakeDecision() {
  const invalidate = useInvalidateApplications();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: MakeDecisionPayload }) =>
      admissionsApi.makeDecision(id, data),
    onSuccess: invalidate,
  });
}

export function useApplicationDecision(applicationId: number | null) {
  return useQuery({
    queryKey: [APPLICATIONS_KEY, "decision", applicationId],
    queryFn: () => admissionsApi.getDecision(applicationId!),
    enabled: applicationId !== null,
    retry: false,
  });
}

export function useApplicationDocuments(applicationId: number | null) {
  return useQuery({
    queryKey: [APPLICATIONS_KEY, "documents", applicationId],
    queryFn: () => admissionsApi.listDocuments(applicationId!),
    enabled: applicationId !== null,
  });
}
