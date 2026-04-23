export interface CopilotInsight {
  title: string;
  value: string;
  explanation: string;
}

export interface CopilotSource {
  source_type: string;
  reference: string;
}

export interface CopilotAnswer {
  question: string;
  summary: string;
  insights: CopilotInsight[];
  sources: CopilotSource[];
  warnings: string[];
  recommendations?: unknown[];
}

export interface LessonPlanPayload {
  faculty_id: string;
  course_title: string;
  topic: string;
  student_level?: string;
  duration_minutes?: number;
  learning_objectives?: string[];
}

export interface MaterialPackPayload {
  faculty_id: string;
  course_title: string;
  topic: string;
  material_type?: "slides" | "worksheet" | "quiz" | "reading";
  constraints?: string;
}

export interface FacultyQnAPayload {
  faculty_id: string;
  course_title?: string;
  question: string;
}
