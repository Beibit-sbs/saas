import { apiGet } from '@/shared/api/client';
import { STUDENT_SUCCESS_API_PATHS } from './constants';
import type { StudentSuccessRuntimeShellResponse } from './types';

export const studentSuccessApi = {
  getRuntimeShell: () => apiGet<StudentSuccessRuntimeShellResponse>(STUDENT_SUCCESS_API_PATHS.runtimeShell),
};
