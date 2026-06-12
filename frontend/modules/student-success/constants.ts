export const STUDENT_SUCCESS_API_PATHS = {
  runtimeShell: '/api/v1/student-success/runtime-shell',
  studentRegistry: '/api/v1/student-success/student-registry',
  studentRetention: '/api/v1/student-success/student-retention',
  academicRisk: '/api/v1/student-success/academic-risk',
  attendanceRisk: '/api/v1/student-success/attendance-risk',
  interventions: '/api/v1/student-success/interventions',
  advisors: '/api/v1/student-success/advisors',
  signals: '/api/v1/student-success/signals',
} as const;

export const STUDENT_SUCCESS_ROUTES = {
  runtimeShell: '/console/student-success/runtime-shell',
  studentRegistry: '/console/student-success/student-registry',
  studentRetention: '/console/student-success/student-retention',
  academicRisk: '/console/student-success/academic-risk',
  attendanceRisk: '/console/student-success/attendance-risk',
  interventions: '/console/student-success/interventions',
  advisors: '/console/student-success/advisors',
  signals: '/console/student-success/signals',
  overview: '/console/student-success',
} as const;
