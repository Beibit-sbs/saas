export interface RequirementStatus {
  requirement_item_id: number;
  course_id: number;
  course_name?: string | null;
  required: boolean;
  credits: number;
  completed: boolean;
}

export interface DegreeProgress {
  student_profile_id: number;
  program_id: number;
  program_name?: string | null;
  requirement_id: number;
  requirement_name: string;
  credits_earned: number;
  minimum_credits: number;
  gpa: number | string | null;
  minimum_gpa: number | string;
  completed_requirements: RequirementStatus[];
  remaining_requirements: RequirementStatus[];
  graduation_eligible: boolean;
}

export interface GraduationEligibility {
  student_profile_id: number;
  eligible: boolean;
  credits_earned: number;
  minimum_credits: number;
  gpa: number | string | null;
  minimum_gpa: number | string;
  remaining_required_items: number;
}

export interface DegreeProgressConsistencyIssue {
  issue_type: string;
  student_profile_id: number | null;
  program_id: number | null;
  requirement_id: number | null;
  active_requirement_count: number | null;
}

export interface DegreeProgressConsistencyReport {
  active_primary_binding_count: number;
  active_requirement_count: number;
  requirement_item_count: number;
  issue_count: number;
  issues: DegreeProgressConsistencyIssue[];
}

export interface ProgramRequirementItem {
  id: number;
  tenant_id: number;
  requirement_id: number;
  course_id: number;
  required: boolean;
  credits: number;
}

export interface ProgramRequirement {
  id: number;
  tenant_id: number;
  program_id: number;
  name: string;
  minimum_credits: number;
  minimum_gpa: number | string;
  is_active: boolean;
  items: ProgramRequirementItem[];
}

export interface ProgramRequirementListResponse {
  total: number;
  items: ProgramRequirement[];
}

export interface CreateProgramRequirementItemPayload {
  course_id: number;
  credits: number;
  required?: boolean;
}

export interface CreateProgramRequirementPayload {
  program_id: number;
  name: string;
  minimum_credits: number;
  minimum_gpa?: number;
  is_active?: boolean;
  items: CreateProgramRequirementItemPayload[];
}
