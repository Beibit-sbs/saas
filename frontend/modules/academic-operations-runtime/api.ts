import { apiGet } from '@/shared/api/client';
import { ACADEMIC_OPERATIONS_RUNTIME_PATHS } from './constants';
import type {
  AttendanceRuntimeResponse,
  AcademicOperationsDashboardRuntimeResponse,
  AssessmentRuntimeResponse,
  AcademicOperationsRuntimeShellResponse,
  AcademicRegistryRuntimeResponse,
  AcademicOperationsSignalsRuntimeResponse,
  CurriculumRuntimeResponse,
  InternshipRuntimeResponse,
  TeachingLoadRuntimeResponse,
  TimetableRuntimeResponse,
} from './types';

export const academicOperationsRuntimeApi = {
  getRuntimeShell: () => apiGet<AcademicOperationsRuntimeShellResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.runtimeShell),
  getAcademicRegistryRuntime: () =>
    apiGet<AcademicRegistryRuntimeResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.academicRegistryRuntime),
  getCurriculumRuntime: () => apiGet<CurriculumRuntimeResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.curriculumRuntime),
  getTimetableRuntime: () => apiGet<TimetableRuntimeResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.timetableRuntime),
  getAttendanceRuntime: () => apiGet<AttendanceRuntimeResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.attendanceRuntime),
  getAssessmentRuntime: () => apiGet<AssessmentRuntimeResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.assessmentRuntime),
  getTeachingLoadRuntime: () => apiGet<TeachingLoadRuntimeResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.teachingLoadRuntime),
  getInternshipRuntime: () => apiGet<InternshipRuntimeResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.internshipRuntime),
  getAcademicOperationsSignalsRuntime: () =>
    apiGet<AcademicOperationsSignalsRuntimeResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.signalsRuntime),
  getAcademicOperationsDashboardRuntime: () =>
    apiGet<AcademicOperationsDashboardRuntimeResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.dashboardRuntime),
};
