export type AcademicOperationsRuntimeShellSection = {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
};

export type AcademicOperationsRuntimeShellSafety = {
  read_only: boolean;
  aggregator_only: boolean;
  tenant_aware: boolean;
  summary_read_required: boolean;
  workflow_execution_enabled: boolean;
  approval_execution_enabled: boolean;
  background_jobs_enabled: boolean;
  provider_mutation_enabled: boolean;
  limitations: string[];
};

export type AcademicOperationsRuntimeShellResponse = {
  tenant_id: number;
  owner_module: string;
  runtime_shell: string;
  runtime_mode: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
  runtime_shell_summary: AcademicOperationsRuntimeShellSection;
  runtime_shell_domain: AcademicOperationsRuntimeShellSection;
  runtime_shell_runtime: AcademicOperationsRuntimeShellSection;
  runtime_shell_integration: AcademicOperationsRuntimeShellSection;
  runtime_shell_readiness: AcademicOperationsRuntimeShellSection;
  safety: AcademicOperationsRuntimeShellSafety;
};

export type AcademicRegistryRuntimeSection = {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
};

export type AcademicRegistryRuntimeOverview = {
  owner_module: string;
  runtime_scope: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
};

export type AcademicRegistryRuntimeStatistics = {
  academic_periods_total: number;
  academic_groups_total: number;
  curriculum_registry_total: number;
  course_catalog_linkage_total: number;
  student_registry_linkage_total: number;
  canonical_bridge_total: number;
};

export type AcademicRegistryRuntimeIntegrationStatus = {
  provider: string;
  status: string;
  integration_mode: string;
  ready: boolean;
  evidence_count: number;
  read_only: boolean;
};

export type AcademicRegistryRuntimeHealth = {
  healthy: boolean;
  consistency_score: number;
  issues: string[];
};

export type AcademicRegistryRuntimeReadiness = {
  ready_for_runtime: boolean;
  checklist: string[];
  readiness_score: number;
};

export type AcademicRegistryRuntimeResponse = {
  tenant_id: number;
  overview: AcademicRegistryRuntimeOverview;
  registry_statistics: AcademicRegistryRuntimeStatistics;
  academic_periods: AcademicRegistryRuntimeSection;
  academic_groups: AcademicRegistryRuntimeSection;
  curriculum_linkage: AcademicRegistryRuntimeSection;
  catalog_linkage: AcademicRegistryRuntimeSection;
  sis_status: AcademicRegistryRuntimeIntegrationStatus;
  lms_status: AcademicRegistryRuntimeIntegrationStatus;
  health: AcademicRegistryRuntimeHealth;
  readiness: AcademicRegistryRuntimeReadiness;
};

export type CurriculumRuntimeSection = {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
};

export type CurriculumRuntimeOverview = {
  owner_module: string;
  runtime_scope: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
};

export type CurriculumRuntimeStatistics = {
  program_structures_total: number;
  curriculum_versions_total: number;
  curriculum_health_score: number;
  course_catalog_linkage_total: number;
  prerequisite_chains_total: number;
  learning_outcomes_total: number;
  academic_plans_total: number;
  canonical_bridge_total: number;
};

export type CurriculumRuntimeHealth = {
  healthy: boolean;
  consistency_score: number;
  issues: string[];
};

export type CurriculumRuntimeRisks = {
  risk_score: number;
  open_risks: number;
  indicators: string[];
};

export type CurriculumRuntimeReadiness = {
  ready_for_runtime: boolean;
  checklist: string[];
  readiness_score: number;
};

export type CurriculumRuntimeResponse = {
  tenant_id: number;
  overview: CurriculumRuntimeOverview;
  curriculum_statistics: CurriculumRuntimeStatistics;
  program_structures: CurriculumRuntimeSection;
  curriculum_versions: CurriculumRuntimeSection;
  curriculum_health: CurriculumRuntimeHealth;
  course_catalog_linkage: CurriculumRuntimeSection;
  prerequisite_chains: CurriculumRuntimeSection;
  learning_outcomes_summary: CurriculumRuntimeSection;
  curriculum_risks: CurriculumRuntimeRisks;
  curriculum_readiness: CurriculumRuntimeReadiness;
};

export type TimetableRuntimeOverview = {
  owner_module: string;
  runtime_scope: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
};

export type TimetableRuntimeStatistics = {
  course_sections_total: number;
  schedules_total: number;
  calendar_periods_total: number;
  rooms_total: number;
  instructors_total: number;
  students_total: number;
  conflicts_total: number;
  capacity_alerts_total: number;
  canonical_bridge_total: number;
};

export type TimetableRuntimeSection = {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
};

export type TimetableRoomUtilization = {
  records: number;
  utilization_rate: number;
  underutilized_rooms: number;
  overloaded_rooms: number;
  read_only: boolean;
};

export type TimetableInstructorAllocation = {
  records: number;
  assigned_instructors: number;
  unassigned_sections: number;
  read_only: boolean;
};

export type TimetableScheduleConflicts = {
  records: number;
  conflict_rate: number;
  critical_conflicts: number;
  read_only: boolean;
};

export type TimetableCapacityIndicators = {
  records: number;
  over_capacity_sections: number;
  under_capacity_sections: number;
  read_only: boolean;
};

export type TimetableRuntimeHealth = {
  healthy: boolean;
  consistency_score: number;
  issues: string[];
};

export type TimetableRuntimeReadiness = {
  ready_for_runtime: boolean;
  checklist: string[];
  readiness_score: number;
};

export type TimetableRuntimeResponse = {
  tenant_id: number;
  overview: TimetableRuntimeOverview;
  timetable_statistics: TimetableRuntimeStatistics;
  academic_calendar_summary: TimetableRuntimeSection;
  room_utilization: TimetableRoomUtilization;
  instructor_allocation: TimetableInstructorAllocation;
  student_schedule_summary: TimetableRuntimeSection;
  schedule_conflicts: TimetableScheduleConflicts;
  capacity_indicators: TimetableCapacityIndicators;
  timetable_health: TimetableRuntimeHealth;
  timetable_readiness: TimetableRuntimeReadiness;
};

export type AttendanceRuntimeOverview = {
  owner_module: string;
  runtime_scope: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
};

export type AttendanceRuntimeStatistics = {
  tracked_students_total: number;
  tracked_courses_total: number;
  average_attendance_rate: number;
  at_risk_students_total: number;
  intervention_candidates_total: number;
  trend_windows_total: number;
  canonical_bridge_total: number;
};

export type AttendanceDistribution = {
  excellent_band: number;
  good_band: number;
  warning_band: number;
  critical_band: number;
  read_only: boolean;
};

export type AttendanceTrends = {
  improving_count: number;
  stable_count: number;
  declining_count: number;
  trend_score: number;
  read_only: boolean;
};

export type AttendanceRiskSummary = {
  risk_score: number;
  open_risks: number;
  primary_risks: string[];
  read_only: boolean;
};

export type AttendanceRuntimeSection = {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
};

export type AttendanceSignals = {
  generated_signals: number;
  signal_types: string[];
  read_only: boolean;
};

export type AttendanceReadiness = {
  ready_for_runtime: boolean;
  checklist: string[];
  readiness_score: number;
};

export type AttendanceRuntimeResponse = {
  tenant_id: number;
  overview: AttendanceRuntimeOverview;
  attendance_statistics: AttendanceRuntimeStatistics;
  attendance_distribution: AttendanceDistribution;
  attendance_trends: AttendanceTrends;
  attendance_risk_summary: AttendanceRiskSummary;
  high_risk_population: AttendanceRuntimeSection;
  course_attendance_health: AttendanceRuntimeSection;
  attendance_intervention_candidates: AttendanceRuntimeSection;
  attendance_signals: AttendanceSignals;
  attendance_readiness: AttendanceReadiness;
};

export type AssessmentRuntimeOverview = {
  owner_module: string;
  runtime_scope: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
};

export type AssessmentRuntimeStatistics = {
  exams_total: number;
  completed_exams_total: number;
  gradebook_entries_total: number;
  grading_distribution_total: number;
  schedule_alignment_total: number;
  assessment_signals_total: number;
  canonical_bridge_total: number;
};

export type AssessmentRuntimeSection = {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
};

export type AssessmentGradingDistribution = {
  excellent_band: number;
  good_band: number;
  warning_band: number;
  critical_band: number;
  read_only: boolean;
};

export type AssessmentRiskSummary = {
  risk_score: number;
  open_risks: number;
  indicators: string[];
  read_only: boolean;
};

export type AssessmentSignals = {
  generated_signals: number;
  signal_types: string[];
  read_only: boolean;
};

export type AssessmentReadiness = {
  ready_for_runtime: boolean;
  checklist: string[];
  readiness_score: number;
};

export type AssessmentRuntimeResponse = {
  tenant_id: number;
  overview: AssessmentRuntimeOverview;
  assessment_statistics: AssessmentRuntimeStatistics;
  exam_governance_summary: AssessmentRuntimeSection;
  gradebook_readiness: AssessmentRuntimeSection;
  grading_distribution: AssessmentGradingDistribution;
  assessment_schedule_alignment: AssessmentRuntimeSection;
  assessment_risk_summary: AssessmentRiskSummary;
  high_risk_assessments: AssessmentRuntimeSection;
  assessment_signals: AssessmentSignals;
  assessment_readiness: AssessmentReadiness;
};

export type TeachingLoadRuntimeOverview = {
  owner_module: string;
  runtime_scope: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
};

export type TeachingLoadRuntimeStatistics = {
  tracked_faculty_total: number;
  department_groups_total: number;
  high_utilization_total: number;
  low_utilization_total: number;
  high_risk_assignments_total: number;
  teaching_load_signals_total: number;
  canonical_bridge_total: number;
};

export type TeachingLoadRuntimeSection = {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
};

export type FacultyWorkloadDistribution = {
  evenly_distributed_total: number;
  overloaded_total: number;
  underutilized_total: number;
  fairness_alert_total: number;
  read_only: boolean;
};

export type WorkloadUtilization = {
  average_utilization_pct: number;
  median_utilization_pct: number;
  min_utilization_pct: number;
  max_utilization_pct: number;
  utilization_std_dev: number;
  read_only: boolean;
};

export type TeachingLoadRiskSummary = {
  risk_score: number;
  open_risks: number;
  indicators: string[];
  read_only: boolean;
};

export type TeachingLoadSignals = {
  generated_signals: number;
  signal_types: string[];
  read_only: boolean;
};

export type TeachingLoadReadiness = {
  ready_for_runtime: boolean;
  checklist: string[];
  readiness_score: number;
};

export type TeachingLoadRuntimeResponse = {
  tenant_id: number;
  overview: TeachingLoadRuntimeOverview;
  teaching_load_statistics: TeachingLoadRuntimeStatistics;
  faculty_workload_distribution: FacultyWorkloadDistribution;
  workload_utilization: WorkloadUtilization;
  overload_risk_summary: TeachingLoadRiskSummary;
  underutilization_summary: TeachingLoadRuntimeSection;
  faculty_assignment_health: TeachingLoadRuntimeSection;
  coverage_risk_summary: TeachingLoadRiskSummary;
  high_risk_assignments: TeachingLoadRuntimeSection;
  teaching_load_signals: TeachingLoadSignals;
  teaching_load_readiness: TeachingLoadReadiness;
};

export type InternshipRuntimeOverview = {
  owner_module: string;
  runtime_scope: string;
  generated_at: string;
  read_only: boolean;
  aggregator_only: boolean;
};

export type InternshipRuntimeStatistics = {
  participation_rate: number;
  completion_rate: number;
  active_rate: number;
  placement_rate: number;
  total_internships: number;
  active_internships: number;
  completed_internships: number;
  employer_count: number;
};

export type InternshipPlacementDistribution = {
  by_employer: Record<string, number>;
  by_industry: Record<string, number>;
  by_department: Record<string, number>;
  read_only: boolean;
};

export type InternshipCompletionSummary = {
  completed: number;
  active: number;
  overdue: number;
  read_only: boolean;
};

export type InternshipActiveInternshipRecord = {
  internship_identifier: string;
  employer: string;
  student_count: number;
  status: string;
};

export type InternshipRuntimeSection = {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
  items: InternshipActiveInternshipRecord[];
};

export type InternshipEmployerEngagement = {
  employer_participation_rate: number;
  repeat_employers: number;
  placement_volume: number;
  employer_count: number;
  read_only: boolean;
};

export type InternshipRiskSummary = {
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  read_only: boolean;
};

export type InternshipHighRiskInternship = {
  internship_identifier: string;
  employer: string;
  student_count: number;
  risk_reason: string;
};

export type InternshipHighRiskSection = {
  owner_module: string;
  records: number;
  read_only: boolean;
  aggregator_only: boolean;
  source_modules: string[];
  items: InternshipHighRiskInternship[];
};

export type InternshipSignals = {
  generated_signals: number;
  signal_types: string[];
  indicators: string[];
  read_only: boolean;
};

export type InternshipReadiness = {
  readiness_score: number;
  readiness_classification: string;
  readiness_drivers: string[];
  ready_for_runtime: boolean;
};

export type InternshipRuntimeResponse = {
  tenant_id: number;
  overview: InternshipRuntimeOverview;
  internship_statistics: InternshipRuntimeStatistics;
  placement_distribution: InternshipPlacementDistribution;
  completion_summary: InternshipCompletionSummary;
  active_internships: InternshipRuntimeSection;
  employer_engagement: InternshipEmployerEngagement;
  internship_risk_summary: InternshipRiskSummary;
  high_risk_internships: InternshipHighRiskSection;
  internship_signals: InternshipSignals;
  internship_readiness: InternshipReadiness;
};
