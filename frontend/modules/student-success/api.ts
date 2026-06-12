import { apiGet } from '@/shared/api/client';
import { useQuery } from '@tanstack/react-query';
import { STUDENT_SUCCESS_API_PATHS } from './constants';
import type {
  StudentAdvisorRuntime,
  StudentAcademicRiskRuntime,
  StudentAttendanceRiskRuntime,
  StudentInterventionRuntime,
  StudentRegistryRuntimeResponse,
  StudentRetentionRuntime,
  StudentSuccessRuntimeShellResponse,
} from './types';

export const studentSuccessApi = {
  getRuntimeShell: () => apiGet<StudentSuccessRuntimeShellResponse>(STUDENT_SUCCESS_API_PATHS.runtimeShell),
  getStudentRegistryRuntime: () => apiGet<StudentRegistryRuntimeResponse>(STUDENT_SUCCESS_API_PATHS.studentRegistry),
  getStudentRetentionRuntime: () => apiGet<StudentRetentionRuntime>(STUDENT_SUCCESS_API_PATHS.studentRetention),
  getStudentAcademicRiskRuntime: () => apiGet<StudentAcademicRiskRuntime>(STUDENT_SUCCESS_API_PATHS.academicRisk),
  getStudentAttendanceRiskRuntime: () => apiGet<StudentAttendanceRiskRuntime>(STUDENT_SUCCESS_API_PATHS.attendanceRisk),
  getStudentInterventionRuntime: () => apiGet<StudentInterventionRuntime>(STUDENT_SUCCESS_API_PATHS.interventions),
  getStudentAdvisorRuntime: () => apiGet<StudentAdvisorRuntime>(STUDENT_SUCCESS_API_PATHS.advisors),
};

export function useStudentRetentionRuntime() {
  return useQuery({
    queryKey: ['student-success:student-retention-runtime'],
    queryFn: studentSuccessApi.getStudentRetentionRuntime,
    staleTime: 30000,
  });
}

export function useStudentAcademicRiskRuntime() {
  return useQuery({
    queryKey: ['student-success:student-academic-risk-runtime'],
    queryFn: studentSuccessApi.getStudentAcademicRiskRuntime,
    staleTime: 30000,
  });
}

export function useStudentAttendanceRiskRuntime() {
  return useQuery({
    queryKey: ['student-success:student-attendance-risk-runtime'],
    queryFn: studentSuccessApi.getStudentAttendanceRiskRuntime,
    staleTime: 30000,
  });
}

export function useStudentInterventionRuntime() {
  return useQuery({
    queryKey: ['student-success:student-intervention-runtime'],
    queryFn: studentSuccessApi.getStudentInterventionRuntime,
    staleTime: 30000,
  });
}

export function useStudentAdvisorRuntime() {
  return useQuery({
    queryKey: ['student-success:student-advisor-runtime'],
    queryFn: studentSuccessApi.getStudentAdvisorRuntime,
    staleTime: 30000,
  });
}
