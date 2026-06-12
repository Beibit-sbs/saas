import { apiGet } from '@/shared/api/client';
import { useQuery } from '@tanstack/react-query';
import { STUDENT_SUCCESS_API_PATHS } from './constants';
import type {
  StudentRegistryRuntimeResponse,
  StudentRetentionRuntime,
  StudentSuccessRuntimeShellResponse,
} from './types';

export const studentSuccessApi = {
  getRuntimeShell: () => apiGet<StudentSuccessRuntimeShellResponse>(STUDENT_SUCCESS_API_PATHS.runtimeShell),
  getStudentRegistryRuntime: () => apiGet<StudentRegistryRuntimeResponse>(STUDENT_SUCCESS_API_PATHS.studentRegistry),
  getStudentRetentionRuntime: () => apiGet<StudentRetentionRuntime>(STUDENT_SUCCESS_API_PATHS.studentRetention),
};

export function useStudentRetentionRuntime() {
  return useQuery({
    queryKey: ['student-success:student-retention-runtime'],
    queryFn: studentSuccessApi.getStudentRetentionRuntime,
    staleTime: 30000,
  });
}
