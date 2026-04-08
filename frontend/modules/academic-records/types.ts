export interface AcademicRecord {
  id: number;
  tenant_id?: string | null;
  student_id: number;
  course_id: number;
  grade: string;
  semester: string;
  status: string;
}

export interface AcademicRecordsResponse {
  records: AcademicRecord[];
}

export interface AcademicRecordItemResponse {
  record: AcademicRecord;
}

export interface CreateAcademicRecordPayload {
  student_id: number;
  course_id: number;
  grade: string;
  semester: string;
  status: string;
}

export interface UpdateAcademicRecordPayload extends CreateAcademicRecordPayload {}

export interface DeleteAcademicRecordResponse {
  deleted: boolean;
  record: AcademicRecord;
}
