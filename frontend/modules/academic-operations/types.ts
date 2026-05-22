export interface AcademicOperationsBoundaryFlags {
  human_review_required: boolean;
  automated_decision: boolean;
  provider_integration_enabled: boolean;
  platonus_sync_enabled: boolean;
  sis_sync_enabled: boolean;
  hidden_score_present: boolean;
  fake_metrics: boolean;
  official_grade_publication_enabled: boolean;
  automated_grading_enabled: boolean;
  automatic_sanction_enabled: boolean;
  incomplete_data: boolean;
  limitations: string[];
  source_matrix_row_id: string | null;
  source_capability_id: string | null;
}

export type AcademicOperationsLimitations = string[];

export interface AcademicOperationsListResponse<T> {
  items: T[];
}

export interface AcademicOperationsRequestBase {
  status?: string | null;
  notes?: string | null;
  external_ref?: string | null;
  student_ref?: string | null;
  faculty_ref?: string | null;
  course_ref?: string | null;
  canonical_module_ref?: string | null;
  source_matrix_row_id?: string | null;
  source_capability_id?: string | null;
  incomplete_data?: boolean;
  limitations?: string[];
}

export interface AcademicOperationsMetadataEntity extends AcademicOperationsBoundaryFlags {
  id: number;
  tenant_id: number;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  archived_at: string | null;
  created_by_user_id?: string | null;
  updated_by_user_id?: string | null;
}

export interface AcademicOperationsHealth {
  tenant_id: number;
  module: string;
  target_level: string;
  foundation_status: string;
  duplicate_module_policy: string;
  provider_integration_enabled: boolean;
  platonus_sync_enabled: boolean;
  sis_sync_enabled: boolean;
  hidden_score_present: boolean;
  fake_metrics: boolean;
  incomplete_data: boolean;
  limitations: string[];
  route_count: number;
  table_count: number;
}

export interface AcademicOperationsDashboard {
  tenant_id: number;
  fake_metrics: boolean;
  data_source: string;
  master_matrix_commit: string;
  master_matrix_rows: number;
  incomplete_data: boolean;
  limitations: string[];
  counts: Record<string, number>;
  canonical_bridge_counts: Record<string, number>;
}

export interface AcademicOperationsMatrixSummary {
  master_matrix_commit: string;
  master_matrix_rows: number;
  contract_version: string;
  target_level: string;
  duplicate_module_policy: string;
  true_new_modules: string[];
  canonical_reuse_map: Record<string, string>;
  bridge_map: Record<string, string>;
  forbidden_runtime_claims: string[];
  required_limitations: string[];
}

export interface AcademicOperationsCanonicalReuseSummary {
  duplicate_module_policy?: string;
  canonical_reuse_map?: Record<string, string>;
  bridge_map?: Record<string, string>;
  true_new_modules?: string[];
  required_limitations?: string[];
  forbidden_runtime_claims?: string[];
  [key: string]: unknown;
}

export interface AcademicGroup extends AcademicOperationsMetadataEntity {
  group_code: string;
  group_name: string;
  external_ref?: string | null;
  notes?: string | null;
}

export interface AcademicGroupCreateRequest extends AcademicOperationsRequestBase {
  group_code: string;
  group_name: string;
}

export interface AcademicGroupUpdateRequest extends AcademicOperationsRequestBase {
  group_name?: string | null;
}

export interface Cohort extends AcademicOperationsMetadataEntity {
  cohort_code: string;
  cohort_name: string;
  academic_group_ref?: string | null;
  notes?: string | null;
}

export interface CohortCreateRequest extends AcademicOperationsRequestBase {
  cohort_code: string;
  cohort_name: string;
  academic_group_ref?: string | null;
}

export interface CohortUpdateRequest extends AcademicOperationsRequestBase {
  cohort_name?: string | null;
  academic_group_ref?: string | null;
}

export interface CourseRegistrationMetadata extends AcademicOperationsMetadataEntity {
  student_ref?: string | null;
  course_ref?: string | null;
  canonical_module_ref?: string | null;
  metadata: Record<string, unknown>;
  notes?: string | null;
}

export interface CourseRegistrationMetadataCreateRequest extends AcademicOperationsRequestBase {
  metadata?: Record<string, unknown>;
}

export interface GradebookMetadata extends AcademicOperationsMetadataEntity {
  student_ref?: string | null;
  course_ref?: string | null;
  gradebook_key: string;
  metadata: Record<string, unknown>;
}

export interface GradebookMetadataCreateRequest extends AcademicOperationsRequestBase {
  gradebook_key: string;
  metadata?: Record<string, unknown>;
}

export interface GradebookMetadataUpdateRequest extends AcademicOperationsRequestBase {
  metadata?: Record<string, unknown> | null;
}

export interface RetakePlan extends AcademicOperationsMetadataEntity {
  student_ref?: string | null;
  course_ref?: string | null;
  plan_code: string;
  retake_window?: string | null;
}

export interface RetakePlanCreateRequest extends AcademicOperationsRequestBase {
  plan_code: string;
  retake_window?: string | null;
}

export interface RetakePlanUpdateRequest extends AcademicOperationsRequestBase {
  retake_window?: string | null;
}

export interface SummerSemesterTerm extends AcademicOperationsMetadataEntity {
  term_code: string;
  display_name: string;
  calendar_ref?: string | null;
}

export interface SummerSemesterTermCreateRequest extends AcademicOperationsRequestBase {
  term_code: string;
  display_name: string;
  calendar_ref?: string | null;
}

export interface SummerSemesterTermUpdateRequest extends AcademicOperationsRequestBase {
  display_name?: string | null;
  calendar_ref?: string | null;
}

export interface AdvisorTutorAssignment extends AcademicOperationsMetadataEntity {
  student_ref?: string | null;
  faculty_ref?: string | null;
  assignment_code: string;
  notes?: string | null;
}

export interface AdvisorTutorAssignmentCreateRequest extends AcademicOperationsRequestBase {
  assignment_code: string;
}

export interface AdvisorTutorAssignmentUpdateRequest extends AcademicOperationsRequestBase {
  assignment_code?: string | null;
}

export interface CanonicalModuleBridge extends AcademicOperationsMetadataEntity {
  bridge_type: string;
  canonical_module_ref: string;
  external_ref?: string | null;
  metadata: Record<string, unknown>;
}

export interface CanonicalModuleBridgeCreateRequest extends AcademicOperationsRequestBase {
  bridge_type: string;
  canonical_module_ref: string;
  metadata?: Record<string, unknown>;
}

export interface BridgeSummary extends AcademicOperationsMetadataEntity {
  bridge_key: string;
  student_ref?: string | null;
  external_ref?: string | null;
  metadata: Record<string, unknown>;
}

export interface AcademicOperationsAuditEvent {
  id: number;
  tenant_id: number;
  entity_type: string;
  entity_id: number | null;
  event_type: string;
  action: string;
  actor_user_id?: string | null;
  previous_status?: string | null;
  new_status?: string | null;
  human_review_required: boolean;
  automated_decision: boolean;
  provider_integration_enabled: boolean;
  payload: Record<string, unknown>;
  created_at: string | null;
}

export interface AcademicOperationsEvidence extends AcademicOperationsMetadataEntity {
  entity_type: string;
  entity_id: number | null;
  evidence_kind: string;
  external_ref?: string | null;
  metadata: Record<string, unknown>;
}

export interface AcademicOperationsEvidenceCreateRequest extends AcademicOperationsRequestBase {
  entity_type: string;
  entity_id?: number | null;
  evidence_kind: string;
  metadata?: Record<string, unknown>;
}