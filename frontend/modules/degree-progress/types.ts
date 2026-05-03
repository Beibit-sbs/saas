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
  gpa: number | null;
  minimum_gpa: number;
  completed_requirements: RequirementStatus[];
  remaining_requirements: RequirementStatus[];
  graduation_eligible: boolean;
}

export interface GraduationEligibility {
  student_profile_id: number;
  eligible: boolean;
  credits_earned: number;
  minimum_credits: number;
  gpa: number | null;
  minimum_gpa: number;
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
