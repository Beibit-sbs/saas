export const ACADEMIC_OPERATIONS_RUNTIME_API_BASE = '/api/v1/academic-operations';

export const ACADEMIC_OPERATIONS_RUNTIME_PATHS = {
  runtimeShell: `${ACADEMIC_OPERATIONS_RUNTIME_API_BASE}/runtime-shell`,
  academicRegistryRuntime: '/api/academic-operations/runtime/academic-registry',
  curriculumRuntime: '/api/academic-operations/runtime/curriculum',
  timetableRuntime: '/api/academic-operations/runtime/timetable',
  attendanceRuntime: '/api/academic-operations/runtime/attendance',
  assessmentRuntime: '/api/academic-operations/runtime/assessment',
  teachingLoadRuntime: '/api/academic-operations/runtime/teaching-load',
  internshipRuntime: '/api/academic-operations/runtime/internship',
  signalsRuntime: '/api/academic-operations/runtime/signals',
  dashboardRuntime: '/api/academic-operations/runtime/dashboard',
} as const;
