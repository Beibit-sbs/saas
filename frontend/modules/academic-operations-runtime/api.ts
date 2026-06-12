import { apiGet } from '@/shared/api/client';
import { ACADEMIC_OPERATIONS_RUNTIME_PATHS } from './constants';
import type { AcademicOperationsRuntimeShellResponse, AcademicRegistryRuntimeResponse } from './types';

export const academicOperationsRuntimeApi = {
  getRuntimeShell: () => apiGet<AcademicOperationsRuntimeShellResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.runtimeShell),
  getAcademicRegistryRuntime: () =>
    apiGet<AcademicRegistryRuntimeResponse>(ACADEMIC_OPERATIONS_RUNTIME_PATHS.academicRegistryRuntime),
};
