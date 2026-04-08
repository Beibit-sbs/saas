export interface Course {
  id: number;
  tenant_id?: string | null;
  course_code: string;
  title: string;
  credits: number;
  program_id: number;
  status: string;
}

export interface CoursesResponse {
  courses: Course[];
}

export interface CourseItemResponse {
  course: Course;
}

export interface CreateCoursePayload {
  course_code: string;
  title: string;
  credits: number;
  program_id: number;
  status: string;
}

export interface UpdateCoursePayload extends CreateCoursePayload {}

export interface DeleteCourseResponse {
  deleted: boolean;
  course: Course;
}
