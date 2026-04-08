export interface Program {
  id: number;
  tenant_id?: string | null;
  program_code: string;
  title: string;
  degree_type: string;
  faculty: string;
  status: string;
}

export interface ProgramsResponse {
  programs: Program[];
}

export interface ProgramItemResponse {
  program: Program;
}

export interface CreateProgramPayload {
  program_code: string;
  title: string;
  degree_type: string;
  faculty: string;
  status: string;
}

export interface UpdateProgramPayload extends CreateProgramPayload {}

export interface DeleteProgramResponse {
  deleted: boolean;
  program: Program;
}
