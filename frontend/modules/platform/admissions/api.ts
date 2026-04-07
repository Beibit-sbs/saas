import { apiGet, apiPost, apiPatch } from "@/shared/api/client";
import type {
  Applicant,
  ApplicantListResponse,
  Application,
  ApplicationDecision,
  ApplicationDocument,
  ApplicationListResponse,
  CreateApplicantPayload,
  CreateApplicationPayload,
  MakeDecisionPayload,
  StageTransitionPayload,
  StageTransitionResponse,
  ApplicationStage,
} from "./types";

const BASE = "/api/admin/admissions";

export const admissionsApi = {
  // Applicants
  listApplicants: (params?: {
    program_id?: number;
    application_year?: number;
    page?: number;
    page_size?: number;
  }) => apiGet<ApplicantListResponse>(`${BASE}/applicants`, params as Record<string, string | number | boolean | undefined>),

  getApplicant: (id: number) =>
    apiGet<Applicant>(`${BASE}/applicants/${id}`),

  createApplicant: (data: CreateApplicantPayload) =>
    apiPost<Applicant>(`${BASE}/applicants`, data),

  updateApplicant: (id: number, data: Partial<CreateApplicantPayload>) =>
    apiPatch<Applicant>(`${BASE}/applicants/${id}`, data),

  // Applications
  listApplications: (params?: {
    program_id?: number;
    stage?: ApplicationStage;
    page?: number;
    page_size?: number;
  }) => apiGet<ApplicationListResponse>(`${BASE}/applications`, params as Record<string, string | number | boolean | undefined>),

  getApplication: (id: number) =>
    apiGet<Application>(`${BASE}/applications/${id}`),

  createApplication: (data: CreateApplicationPayload) =>
    apiPost<Application>(`${BASE}/applications`, data),

  submitApplication: (id: number, expectedVersion: number) =>
    apiPost<Application>(`${BASE}/applications/${id}/submit`, { expected_version: expectedVersion }),

  transitionStage: (id: number, data: StageTransitionPayload) =>
    apiPost<StageTransitionResponse>(`${BASE}/applications/${id}/stage-transition`, data),

  makeDecision: (id: number, data: MakeDecisionPayload) =>
    apiPost<ApplicationDecision>(`${BASE}/applications/${id}/decision`, data),

  getDecision: (id: number) =>
    apiGet<ApplicationDecision>(`${BASE}/applications/${id}/decision`),

  listDocuments: (applicationId: number) =>
    apiGet<{ total: number; items: ApplicationDocument[] }>(`${BASE}/applications/${applicationId}/documents`),
};
