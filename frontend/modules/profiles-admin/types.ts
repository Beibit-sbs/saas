export interface ProfilePerson {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  status: string;
  version: number;
  created_at: string;
}

export interface ProfileDepartment {
  id: number;
  code: string;
  name: string;
  unit_type: string;
  status: string;
}

export interface ProfilePeopleResponse {
  items: ProfilePerson[];
  total: number;
  page: number;
  page_size: number;
}

export interface ProfileDepartmentsResponse {
  items: ProfileDepartment[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateProfilePersonPayload {
  email: string;
  first_name: string;
  last_name: string;
  status?: string;
}
