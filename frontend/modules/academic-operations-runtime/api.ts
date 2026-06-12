import { apiGet } from '@/shared/api/client';
import { ACADEMIC_OPERATIONS_RUNTIME_PATHS } from './constants';
import type {
  AcademicOperationsRuntimeShellResponse,
  AcademicRegistryRuntimeResponse,
  CurriculumRuntimeResponse,
  TimetableRuntimeResponse,
} from './types';

export const academicOperationsRuntimeApi = {
  getRuntimeShell: () => apiGet<AcademicOperationsRuntimeShellResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.runtimeShell),
  getAcademicRegistryRuntime: () =>
    apiGet<AcademicRegistryRuntimeResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.academicRegistryRuntime),
  getCurriculumRuntime: () => apiGet<CurriculumRuntimeResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.curriculumRuntime),
  getTimetableRuntime: () => apiGet<TimetableRuntimeResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.timetableRuntime),
};
