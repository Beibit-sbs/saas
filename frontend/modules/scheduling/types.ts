export interface CourseSection {
  id: string;
  code: string;
  course_name: string;
  instructor: string | null;
  capacity: number;
  enrolled_count: number;
  semester: string;
  schedule: string | null;
  room: string | null;
  status: "open" | "closed" | "cancelled";
  tenant_id: string;
}

export interface CreateSectionPayload {
  code: string;
  course_name: string;
  instructor?: string;
  capacity: number;
  semester: string;
  schedule?: string;
  room?: string;
  tenant_id: string;
}
