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

export interface FacultyContract {
  id: number;
  tenant_id?: string | null;
  faculty_id: string;
  contract_type: string;
  start_date: string;
  end_date?: string | null;
  fte_ratio: number;
  max_credit_hours: number;
  status: string;
  notes?: string | null;
}

export interface FacultyContractListResponse {
  contracts: FacultyContract[];
}

export interface FacultyContractItemResponse {
  contract: FacultyContract;
}

export interface CreateFacultyContractPayload {
  faculty_id: string;
  contract_type: string;
  start_date: string;
  end_date?: string | null;
  fte_ratio: number;
  max_credit_hours: number;
  status: string;
  notes?: string | null;
}

export interface UpdateFacultyContractStatusPayload {
  status: string;
  notes?: string | null;
}
