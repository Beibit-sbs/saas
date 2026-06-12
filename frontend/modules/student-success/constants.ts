export const STUDENT_SUCCESS_API_PATHS = {
  runtimeShell: '/api/v1/student-success/runtime-shell',
  studentRegistry: '/api/v1/student-success/student-registry',
  studentRetention: '/api/v1/student-success/student-retention',
} as const;

export const STUDENT_SUCCESS_ROUTES = {
  runtimeShell: '/console/student-success/runtime-shell',
  studentRegistry: '/console/student-success/student-registry',
  studentRetention: '/console/student-success/student-retention',
  overview: '/console/student-success',
} as const;
