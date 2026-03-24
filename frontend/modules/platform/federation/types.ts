export type Institution = {
  id: number;
  name: string;
  code: string;
  country: string;
  type: "university" | "college" | "institute" | string;
  status: "active" | "inactive" | string;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type FederationMember = {
  id: number;
  institution_id: number;
  tenant_id: number;
  role: "institution_admin" | "federation_admin" | "platform_admin" | string;
  created_at: string;
};

export type InstitutionKpiCard = {
  metric_key: string;
  title: string;
  value: number;
};

export type InstitutionOverview = {
  institution: Institution;
  tenant_count: number;
  students_total: number;
  enrollments_total: number;
  automation_health: Record<string, unknown>;
  kpi_cards: InstitutionKpiCard[];
};

export type InstitutionCreateRequest = {
  name: string;
  code: string;
  country: string;
  type?: string;
  metadata?: Record<string, unknown>;
};

export type LinkTenantRequest = {
  tenant_id: number;
  role?: string;
};
