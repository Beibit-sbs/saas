/**
 * Syllabus Governance Types
 * Defines interfaces for syllabus lifecycle and content approval workflow
 */

export enum SyllabusStatus {
  DRAFT = 'draft',
  UNDER_REVIEW = 'under_review',
  APPROVED = 'approved',
  PUBLISHED = 'published',
  ARCHIVED = 'archived',
}

export enum ApprovalStepType {
  DEPARTMENT_CHAIR = 'department_chair',
  ACADEMIC_DEAN = 'academic_dean',
  COMPLIANCE_REVIEW = 'compliance_review',
  FINAL_APPROVAL = 'final_approval',
}

export interface SyllabusMetadata {
  syllabi_id: string;
  course_code: string;
  course_title: string;
  department_id: string;
  faculty_id: string;
  term_id: string;
  created_at: string;
  updated_at: string;
  published_at?: string;
  status: SyllabusStatus;
}

export interface SyllabusContent {
  syllabi_id: string;
  course_description: string;
  learning_outcomes: string[];
  course_requirements: string;
  grading_rubric: string;
  required_readings: string[];
  course_schedule: CourseWeek[];
  attendance_policy: string;
  academic_integrity_statement: string;
  accommodations_statement: string;
  last_modified_by: string;
  last_modified_at: string;
}

export interface CourseWeek {
  week_number: number;
  topic: string;
  readings: string[];
  assignments: string[];
  due_dates: string[];
}

export interface ApprovalStep {
  step_id: string;
  syllabi_id: string;
  step_type: ApprovalStepType;
  assigned_to: string;
  assigned_to_name: string;
  status: 'pending' | 'approved' | 'rejected' | 'skipped';
  feedback?: string;
  submitted_at?: string;
  created_at: string;
  order: number;
}

export interface ApprovalWorkflow {
  workflow_id: string;
  syllabi_id: string;
  current_step: number;
  total_steps: number;
  approval_steps: ApprovalStep[];
  initiated_at: string;
  completed_at?: string;
  status: 'in_progress' | 'completed' | 'cancelled';
  rejection_reason?: string;
}

export interface ContentReviewRequest {
  review_id: string;
  syllabi_id: string;
  requested_by: string;
  requested_at: string;
  review_type: 'content_validation' | 'compliance_check' | 'standard_compliance';
  comments: string;
  issues_found: ReviewIssue[];
  status: 'submitted' | 'in_review' | 'approved' | 'needs_revision';
}

export interface ReviewIssue {
  issue_id: string;
  severity: 'critical' | 'major' | 'minor';
  section: string;
  description: string;
  suggested_fix?: string;
  resolved: boolean;
}

export interface SyllabusVersion {
  version_id: string;
  syllabi_id: string;
  version_number: number;
  created_at: string;
  created_by: string;
  content_hash: string;
  is_current: boolean;
  release_notes?: string;
}

export interface SyllabusTemplate {
  template_id: string;
  department_id: string;
  template_name: string;
  template_content: SyllabusContent;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface SyllabusDashboardSummary {
  total_syllabi: number;
  status_breakdown: {
    draft: number;
    under_review: number;
    approved: number;
    published: number;
    archived: number;
  };
  pending_approvals: number;
  expiring_syllabi: number;
  last_updated: string;
}

export interface SyllabusListItem {
  syllabi_id: string;
  course_code: string;
  course_title: string;
  faculty_name: string;
  status: SyllabusStatus;
  term_id: string;
  updated_at: string;
  approval_stage?: number;
}

export interface SyllabusCreatePayload {
  course_code: string;
  course_title: string;
  department_id: string;
  faculty_id: string;
  term_id: string;
  template_id?: string;
}

export interface SyllabusUpdatePayload {
  course_description?: string;
  learning_outcomes?: string[];
  course_requirements?: string;
  grading_rubric?: string;
  required_readings?: string[];
  course_schedule?: CourseWeek[];
  attendance_policy?: string;
}
