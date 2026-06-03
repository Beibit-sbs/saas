import { useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";

export interface LeadRecord {
  id: number;
  tenant_id: number;
  lead_ref: string;
  status: string;
  full_name: string;
  email: string;
  phone?: string | null;
  source_channel: string;
}

export interface ApplicantRecord {
  id: number;
  tenant_id: number;
  lead_id: number;
  applicant_ref: string;
  status: string;
  full_name: string;
  email: string;
}

export interface ApplicationRecord {
  id: number;
  tenant_id: number;
  applicant_id: number;
  application_ref: string;
  status: string;
  program_code: string;
  intake_term: string;
}

interface ListResponse<T> {
  tenant_id: number;
  items: T[];
  fake_metrics: boolean;
  provider_live_enabled: boolean;
  autonomous_decision_enabled: boolean;
  hidden_score_present: boolean;
  human_review_required: boolean;
}

interface ItemResponse<T> {
  tenant_id: number;
  item: T;
  fake_metrics: boolean;
  provider_live_enabled: boolean;
  autonomous_decision_enabled: boolean;
  hidden_score_present: boolean;
  human_review_required: boolean;
}

const API = {
  leads: "/api/admin/admissions-crm/leads",
  leadById: (leadId: number) => `/api/admin/admissions-crm/leads/${leadId}`,
  qualifyLead: (leadId: number) => `/api/admin/admissions-crm/leads/${leadId}/qualify`,
  convertLead: (leadId: number) => `/api/admin/admissions-crm/leads/${leadId}/convert-to-applicant`,
  applicants: "/api/admin/admissions-crm/applicants",
  applicantById: (applicantId: number) => `/api/admin/admissions-crm/applicants/${applicantId}`,
  applications: "/api/admin/admissions-crm/applications",
  applicationById: (applicationId: number) => `/api/admin/admissions-crm/applications/${applicationId}`,
  submitApplication: (applicationId: number) => `/api/admin/admissions-crm/applications/${applicationId}/submit`,
};

const CACHE = {
  leads: ["admissions-crm", "leads"] as const,
  lead: (leadId: number | null) => ["admissions-crm", "lead", leadId] as const,
  applicants: ["admissions-crm", "applicants"] as const,
  applicant: (applicantId: number | null) => ["admissions-crm", "applicant", applicantId] as const,
  applications: ["admissions-crm", "applications"] as const,
  application: (applicationId: number | null) => ["admissions-crm", "application", applicationId] as const,
};

export function useAdmissionsCrmLeads() {
  return useQuery({
    queryKey: CACHE.leads,
    queryFn: () => apiGet<ListResponse<LeadRecord>>(API.leads),
    staleTime: 30000,
  });
}

export function useAdmissionsCrmLead(leadId: number | null) {
  return useQuery({
    queryKey: CACHE.lead(leadId),
    queryFn: () => apiGet<ItemResponse<LeadRecord>>(API.leadById(Number(leadId))),
    enabled: leadId !== null,
    staleTime: 30000,
  });
}

export function useAdmissionsCrmApplicants() {
  return useQuery({
    queryKey: CACHE.applicants,
    queryFn: () => apiGet<ListResponse<ApplicantRecord>>(API.applicants),
    staleTime: 30000,
  });
}

export function useAdmissionsCrmApplicant(applicantId: number | null) {
  return useQuery({
    queryKey: CACHE.applicant(applicantId),
    queryFn: () => apiGet<ItemResponse<ApplicantRecord>>(API.applicantById(Number(applicantId))),
    enabled: applicantId !== null,
    staleTime: 30000,
  });
}

export function useAdmissionsCrmApplications() {
  return useQuery({
    queryKey: CACHE.applications,
    queryFn: () => apiGet<ListResponse<ApplicationRecord>>(API.applications),
    staleTime: 30000,
  });
}

export function useAdmissionsCrmApplication(applicationId: number | null) {
  return useQuery({
    queryKey: CACHE.application(applicationId),
    queryFn: () => apiGet<ItemResponse<ApplicationRecord>>(API.applicationById(Number(applicationId))),
    enabled: applicationId !== null,
    staleTime: 30000,
  });
}

export function useCreateLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      lead_ref: string;
      full_name: string;
      email: string;
      phone?: string | null;
      source_channel?: string;
      metadata?: Record<string, unknown>;
    }) => apiPost<ItemResponse<LeadRecord>>(API.leads, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE.leads });
    },
  });
}

export function useQualifyLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { leadId: number; reason?: string | null }) =>
      apiPost<ItemResponse<LeadRecord>>(API.qualifyLead(payload.leadId), { reason: payload.reason ?? null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE.leads });
    },
  });
}

export function useConvertLeadToApplicant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { leadId: number; applicant_ref: string }) =>
      apiPost<ItemResponse<ApplicantRecord>>(API.convertLead(payload.leadId), {
        applicant_ref: payload.applicant_ref,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE.leads });
      queryClient.invalidateQueries({ queryKey: CACHE.applicants });
    },
  });
}

export function useCreateApplicant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      lead_id: number;
      applicant_ref: string;
      full_name: string;
      email: string;
      metadata?: Record<string, unknown>;
    }) => apiPost<ItemResponse<ApplicantRecord>>(API.applicants, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE.applicants });
      queryClient.invalidateQueries({ queryKey: CACHE.leads });
    },
  });
}

export function useCreateApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      applicant_id: number;
      application_ref: string;
      program_code: string;
      intake_term: string;
      metadata?: Record<string, unknown>;
    }) => apiPost<ItemResponse<ApplicationRecord>>(API.applications, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE.applications });
    },
  });
}

export function useSubmitApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { applicationId: number; note?: string | null }) =>
      apiPost<ItemResponse<ApplicationRecord>>(API.submitApplication(payload.applicationId), {
        note: payload.note ?? null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE.applications });
    },
  });
}

export function useAdmissionsCrmSummary() {
  const leads = useAdmissionsCrmLeads();
  const applicants = useAdmissionsCrmApplicants();
  const applications = useAdmissionsCrmApplications();

  const summary = useMemo(() => {
    const leadItems = leads.data?.items ?? [];
    const applicantItems = applicants.data?.items ?? [];
    const applicationItems = applications.data?.items ?? [];

    const submittedApplications = applicationItems.filter((item) => item.status === "application_submitted").length;
    const startedApplications = applicationItems.filter((item) => item.status === "application_started").length;

    return {
      leads: leadItems.length,
      applicants: applicantItems.length,
      applications: applicationItems.length,
      submittedApplications,
      startedApplications,
      archivedLeads: leadItems.filter((item) => item.status === "archived").length,
      archivedApplications: applicationItems.filter((item) => item.status === "archived").length,
      hasIncompleteData: !leads.data || !applicants.data || !applications.data,
    };
  }, [leads.data, applicants.data, applications.data]);

  return {
    summary,
    isLoading: leads.isLoading || applicants.isLoading || applications.isLoading,
    isError: leads.isError || applicants.isError || applications.isError,
    errors: [leads.error, applicants.error, applications.error].filter(Boolean),
  };
}
