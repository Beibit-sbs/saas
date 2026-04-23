export type FacultyKpiStatus = "satisfactory" | "needs_improvement" | "on_probation";

export interface FacultyKpi {
  id: number;
  tenant_id?: string | null;
  faculty_id: string;
  name: string;
  department_id: string;
  kpi_period: string;
  teaching_score: number;
  research_score: number;
  service_score: number;
  overall_score: number;
  status: FacultyKpiStatus;
}

export interface FacultyKpiListResponse {
  items: FacultyKpi[];
}

export interface FacultyKpiItemResponse {
  item: FacultyKpi;
}

export interface FacultyKpiCreatePayload {
  faculty_id: string;
  name: string;
  department_id: string;
  kpi_period: string;
  teaching_score: number;
  research_score: number;
  service_score: number;
  overall_score: number;
  status?: FacultyKpiStatus;
}

export interface FacultyKpiStatusUpdatePayload {
  status: FacultyKpiStatus;
}
