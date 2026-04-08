export interface FacultyMember {
  id: number;
  tenant_id?: string | null;
  faculty_id: string;
  first_name: string;
  last_name: string;
  department: string;
  email: string;
  status: string;
}

export interface FacultyListResponse {
  faculty: FacultyMember[];
}

export interface FacultyItemResponse {
  faculty: FacultyMember;
}

export interface CreateFacultyPayload {
  faculty_id: string;
  first_name: string;
  last_name: string;
  department: string;
  email: string;
  status: string;
}

export interface UpdateFacultyPayload extends CreateFacultyPayload {}

export interface DeleteFacultyResponse {
  deleted: boolean;
  faculty: FacultyMember;
}
