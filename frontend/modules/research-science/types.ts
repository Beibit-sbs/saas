export interface ResearchScienceBoundaryFlags {
  human_review_required: boolean;
  autonomous_decision: boolean;
  provider_integration_enabled: boolean;
  external_database_sync_enabled: boolean;
  official_verification_enabled: boolean;
  hidden_score_present: boolean;
  fake_metrics?: boolean;
  fake_evidence?: boolean;
  fake_publication?: boolean;
  fake_certificate?: boolean;
  fake_grant_evidence?: boolean;
  autonomous_ethics_approval_enabled?: boolean;
  autonomous_grant_submission_enabled?: boolean;
  autonomous_publication_verification_enabled?: boolean;
  incomplete_data: boolean;
  limitations: string[];
  source_matrix_row_id?: string | null;
  source_capability_id?: string | null;
}

export interface ResearchScienceListResponse<T> {
  items: T[];
}

export interface ResearchScienceRequestBase {
  status?: string | null;
  title?: string | null;
  notes?: string | null;
  external_ref?: string | null;
  student_ref?: string | null;
  faculty_ref?: string | null;
  department_ref?: string | null;
  program_ref?: string | null;
  project_ref?: string | null;
  publication_ref?: string | null;
  conference_ref?: string | null;
  grant_ref?: string | null;
  ethics_ref?: string | null;
  bridge_ref?: string | null;
  source_matrix_row_id?: string | null;
  source_capability_id?: string | null;
  incomplete_data?: boolean;
  limitations?: string[];
  metadata?: Record<string, unknown>;
}

export interface ResearchScienceMetadataEntity extends ResearchScienceBoundaryFlags {
  id: number;
  tenant_id: number;
  status: string;
  metadata: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
  archived_at: string | null;
  created_by_user_id?: string | null;
  updated_by_user_id?: string | null;
}

export interface ResearchScienceHealthResponse {
  tenant_id: number;
  module: string;
  target_level: string;
  foundation_status: string;
  runtime_mode: string;
  contract_version: string;
  provider_integration_enabled: boolean;
  external_database_sync_enabled: boolean;
  official_verification_enabled: boolean;
  hidden_score_present: boolean;
  fake_metrics: boolean;
  incomplete_data: boolean;
  limitations: string[];
  route_count: number;
  table_count: number;
}

export interface ResearchScienceDashboardResponse extends ResearchScienceBoundaryFlags {
  tenant_id: number;
  fake_metrics: boolean;
  generated_at: string | null;
  contract_version: string;
  source_spec_commit: string;
  master_matrix_commit: string;
  master_matrix_rows: number;
  capability_count: number;
  data_source: string;
  projects_summary: Record<string, number>;
  student_research_summary: Record<string, number>;
  supervision_summary: Record<string, number>;
  publications_summary: Record<string, number>;
  conferences_summary: Record<string, number>;
  grants_summary: Record<string, number>;
  ethics_summary: Record<string, number>;
  evidence_summary: Record<string, number>;
  bridge_summary: Record<string, number>;
  brain_readiness_summary: Record<string, number>;
  boundary_summary: Record<string, boolean>;
}

export interface ResearchScienceMatrixSummaryResponse {
  contract_version: string;
  source_spec_commit: string;
  source_product_map_commit: string;
  master_matrix_commit: string;
  master_matrix_rows: number;
  capability_count: number;
  runtime_mode: string;
  autonomy_mode: string;
  route_count_expected: string;
  table_count_expected: number;
}

export interface ResearchScienceLimitationsResponse {
  items: string[];
}

export interface ResearchProject extends ResearchScienceMetadataEntity {
  project_ref: string;
  department_ref?: string | null;
  program_ref?: string | null;
  external_ref?: string | null;
  title: string;
  notes?: string | null;
}

export interface StudentResearchWork extends ResearchScienceMetadataEntity {
  student_ref?: string | null;
  faculty_ref?: string | null;
  project_ref?: string | null;
  publication_ref?: string | null;
  conference_ref?: string | null;
  topic_title: string;
  notes?: string | null;
}

export interface ScientificSupervision extends ResearchScienceMetadataEntity {
  student_ref?: string | null;
  faculty_ref?: string | null;
  project_ref?: string | null;
  supervision_ref: string;
  notes?: string | null;
}

export interface PublicationMetadata extends ResearchScienceMetadataEntity {
  publication_ref: string;
  faculty_ref?: string | null;
  student_ref?: string | null;
  project_ref?: string | null;
  external_ref?: string | null;
  title: string;
  fake_publication: boolean;
  autonomous_publication_verification_enabled: boolean;
}

export interface ConferenceParticipation extends ResearchScienceMetadataEntity {
  conference_ref: string;
  faculty_ref?: string | null;
  student_ref?: string | null;
  project_ref?: string | null;
  external_ref?: string | null;
  title: string;
  fake_certificate: boolean;
}

export interface GrantApplication extends ResearchScienceMetadataEntity {
  grant_ref: string;
  project_ref?: string | null;
  department_ref?: string | null;
  faculty_ref?: string | null;
  external_ref?: string | null;
  title: string;
  fake_grant_evidence: boolean;
  autonomous_grant_submission_enabled: boolean;
}

export interface GrantDeliverable extends ResearchScienceMetadataEntity {
  grant_ref?: string | null;
  project_ref?: string | null;
  external_ref?: string | null;
  deliverable_ref: string;
  title: string;
  fake_grant_evidence: boolean;
  autonomous_grant_submission_enabled: boolean;
}

export interface ResearchEthicsRequest extends ResearchScienceMetadataEntity {
  ethics_ref: string;
  project_ref?: string | null;
  faculty_ref?: string | null;
  student_ref?: string | null;
  title: string;
  autonomous_ethics_approval_enabled: boolean;
}

export interface ResearchEthicsAmendment extends ResearchScienceMetadataEntity {
  ethics_ref?: string | null;
  project_ref?: string | null;
  external_ref?: string | null;
  amendment_ref: string;
  title: string;
}

export interface ResearchEvidence extends ResearchScienceMetadataEntity {
  source_entity_type: string;
  source_entity_id?: number | null;
  evidence_type: string;
  title: string;
  description?: string | null;
  reference_uri?: string | null;
  storage_ref?: string | null;
  submitted_by_user_id?: string | null;
  submitted_at?: string | null;
  verification_status: string;
  verified_by_user_id?: string | null;
  reviewed_at?: string | null;
  provider_verified: boolean;
  official_external_verification: boolean;
  fake_evidence: boolean;
}

export interface ResearchAuditEvent {
  id: number;
  tenant_id: number;
  event_type: string;
  source_entity_type: string;
  source_entity_id?: number | null;
  actor_user_id?: string | null;
  previous_status?: string | null;
  new_status?: string | null;
  payload: Record<string, unknown>;
  request_id?: string | null;
  created_at: string | null;
  human_review_required: boolean;
  autonomous_decision: boolean;
  provider_integration_enabled: boolean;
  hidden_score_present: boolean;
}

export interface ResearchStatusHistory {
  id: number;
  tenant_id: number;
  source_entity_type: string;
  source_entity_id?: number | null;
  previous_status?: string | null;
  new_status: string;
  changed_by_user_id?: string | null;
  changed_at: string | null;
  reason?: string | null;
  metadata: Record<string, unknown>;
  human_review_required: boolean;
}

export interface ResearchBridge extends ResearchScienceMetadataEntity {
  bridge_target: string;
  source_entity_type: string;
  source_entity_id?: number | null;
  target_reference?: string | null;
  bridge_status: string;
  bridge_ref?: string | null;
  read_only_first: boolean;
  mutation_allowed: boolean;
  provider_sync_enabled: boolean;
  external_submission_enabled: boolean;
}

export interface ResearchBridgeSummary {
  tenant_id: number;
  bridge_counts: Record<string, number>;
  read_only_first: boolean;
  mutation_allowed: boolean;
  provider_sync_enabled: boolean;
  external_submission_enabled: boolean;
}

export interface ResearchProjectCreatePayload extends ResearchScienceRequestBase {
  project_ref: string;
  title: string;
}

export interface ResearchProjectUpdatePayload extends ResearchScienceRequestBase {
  project_ref?: string | null;
  title?: string | null;
}

export interface StudentResearchWorkCreatePayload extends ResearchScienceRequestBase {
  topic_title: string;
}

export interface StudentResearchWorkUpdatePayload extends ResearchScienceRequestBase {
  topic_title?: string | null;
}

export interface ScientificSupervisionCreatePayload extends ResearchScienceRequestBase {
  supervision_ref: string;
}

export interface ScientificSupervisionUpdatePayload extends ResearchScienceRequestBase {
  supervision_ref?: string | null;
}

export interface PublicationMetadataCreatePayload extends ResearchScienceRequestBase {
  publication_ref: string;
  title: string;
}

export interface PublicationMetadataUpdatePayload extends ResearchScienceRequestBase {
  publication_ref?: string | null;
  title?: string | null;
}

export interface ConferenceParticipationCreatePayload extends ResearchScienceRequestBase {
  conference_ref: string;
  title: string;
}

export interface ConferenceParticipationUpdatePayload extends ResearchScienceRequestBase {
  conference_ref?: string | null;
  title?: string | null;
}

export interface GrantApplicationCreatePayload extends ResearchScienceRequestBase {
  grant_ref: string;
  title: string;
}

export interface GrantApplicationUpdatePayload extends ResearchScienceRequestBase {
  grant_ref?: string | null;
  title?: string | null;
}

export interface GrantDeliverableCreatePayload extends ResearchScienceRequestBase {
  deliverable_ref: string;
  title: string;
}

export interface ResearchEthicsRequestCreatePayload extends ResearchScienceRequestBase {
  ethics_ref: string;
  title: string;
}

export interface ResearchEthicsRequestUpdatePayload extends ResearchScienceRequestBase {
  ethics_ref?: string | null;
  title?: string | null;
}

export interface ResearchEvidenceCreatePayload extends ResearchScienceRequestBase {
  source_entity_type: string;
  source_entity_id?: number | null;
  evidence_type: string;
  title: string;
  description?: string | null;
  reference_uri?: string | null;
  storage_ref?: string | null;
  verification_status?: string;
}

export interface ResearchBridgeCreatePayload extends ResearchScienceRequestBase {
  bridge_target: string;
  source_entity_type: string;
  source_entity_id?: number | null;
  target_reference?: string | null;
  bridge_status?: string | null;
}