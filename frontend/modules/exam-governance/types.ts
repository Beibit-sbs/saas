/**
 * Exam Governance Types
 * Defines interfaces for exam lifecycle, scheduling, proctoring, and accessibility
 */

export enum ExamStatus {
  SCHEDULED = 'scheduled',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

export enum ProctoringMode {
  IN_PERSON = 'in_person',
  REMOTE = 'remote',
  HYBRID = 'hybrid',
}

export enum AccessibilityAccommodation {
  EXTRA_TIME = 'extra_time',
  SEPARATE_ROOM = 'separate_room',
  ASSISTIVE_TECHNOLOGY = 'assistive_technology',
  READER_SCRIBE = 'reader_scribe',
  LARGE_PRINT = 'large_print',
}

export interface ExamMetadata {
  exam_id: string;
  course_code: string;
  course_title: string;
  faculty_id: string;
  exam_type: 'midterm' | 'final' | 'quiz' | 'practical';
  term_id: string;
  created_at: string;
  updated_at: string;
  status: ExamStatus;
}

export interface ExamSchedule {
  exam_id: string;
  scheduled_date: string;
  scheduled_time: string;
  duration_minutes: number;
  registration_deadline: string;
  instructions?: string;
  is_proctored: boolean;
  proctoring_mode: ProctoringMode;
  created_at: string;
  updated_at: string;
}

export interface ExamRoom {
  room_id: string;
  exam_id: string;
  room_code: string;
  room_name: string;
  capacity: number;
  assigned_count: number;
  location?: string;
  equipment_available: string[];
  created_at: string;
}

export interface ProctorAssignment {
  assignment_id: string;
  exam_id: string;
  proctor_id: string;
  proctor_name: string;
  room_id?: string;
  scheduled_date: string;
  scheduled_time: string;
  responsibilities: string;
  status: 'assigned' | 'confirmed' | 'completed' | 'no_show';
  created_at: string;
}

export interface ExamSession {
  session_id: string;
  exam_id: string;
  session_date: string;
  session_time: string;
  session_number: number;
  max_students: number;
  registered_students: number;
  room_id?: string;
  proctor_id?: string;
  status: ExamStatus;
  start_time?: string;
  end_time?: string;
}

export interface StudentExamRegistration {
  registration_id: string;
  session_id: string;
  student_id: string;
  student_name: string;
  registered_at: string;
  check_in_time?: string;
  check_out_time?: string;
  proctored: boolean;
  accommodations: AccessibilityAccommodation[];
  status: 'registered' | 'checked_in' | 'in_progress' | 'completed' | 'absent';
}

export interface ExamQuestion {
  question_id: string;
  exam_id: string;
  question_number: number;
  question_type: 'multiple_choice' | 'short_answer' | 'essay' | 'fill_blank';
  question_text: string;
  points: number;
  options?: { id: string; text: string; is_correct?: boolean }[];
  rubric?: string;
  created_by: string;
  created_at: string;
}

export interface ExamAccessibility {
  accommodation_id: string;
  exam_id: string;
  student_id: string;
  accommodation_type: AccessibilityAccommodation;
  extra_time_minutes?: number;
  separate_room_required: boolean;
  notes?: string;
  verified: boolean;
  verified_by?: string;
  created_at: string;
}

export interface ExamStatistics {
  exam_id: string;
  total_registered: number;
  total_completed: number;
  avg_score: number;
  highest_score: number;
  lowest_score: number;
  pass_rate: number;
  no_show_count: number;
  accommodated_count: number;
  last_updated: string;
}

export interface ExamDashboardSummary {
  total_exams: number;
  status_breakdown: {
    scheduled: number;
    in_progress: number;
    completed: number;
    cancelled: number;
  };
  upcoming_exams_count: number;
  proctors_needed: number;
  students_with_accommodations: number;
  last_updated: string;
}

export interface ExamListItem {
  exam_id: string;
  course_code: string;
  course_title: string;
  faculty_name: string;
  exam_type: string;
  scheduled_date: string;
  status: ExamStatus;
  registered_count: number;
  updated_at: string;
}

export interface ExamCreatePayload {
  course_code: string;
  course_title: string;
  faculty_id: string;
  exam_type: 'midterm' | 'final' | 'quiz' | 'practical';
  term_id: string;
  scheduled_date: string;
  scheduled_time: string;
  duration_minutes: number;
}

export interface ExamUpdatePayload {
  scheduled_date?: string;
  scheduled_time?: string;
  duration_minutes?: number;
  registration_deadline?: string;
  instructions?: string;
  status?: ExamStatus;
}

export interface ExamSessionCreatePayload {
  exam_id: string;
  session_date: string;
  session_time: string;
  max_students: number;
  room_id?: string;
  proctor_id?: string;
}
