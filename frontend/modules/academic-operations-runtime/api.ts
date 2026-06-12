import { apiGet } from '@/shared/api/client';
import { ACADEMIC_OPERATIONS_RUNTIME_PATHS } from './constants';
import type { AcademicOperationsRuntimeShellResponse } from './types';

export const academicOperationsRuntimeApi = {
  getRuntimeShell: () => apiGet<AcademicOperationsRuntimeShellResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.runtimeShell),
};
