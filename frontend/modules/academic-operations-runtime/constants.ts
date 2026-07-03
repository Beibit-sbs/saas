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

export const ACADEMIC_OPERATIONS_RUNTIME_UI_BASE = '/console/academic-operations';

export const ACADEMIC_OPERATIONS_RUNTIME_NAV_ITEMS = [
  { key: 'runtime-shell', title: 'Runtime Shell', href: `${ACADEMIC_OPERATIONS_RUNTIME_UI_BASE}/runtime-shell` },
  { key: 'dashboard', title: 'Dashboard', href: `${ACADEMIC_OPERATIONS_RUNTIME_UI_BASE}/dashboard` },
  { key: 'academic-registry', title: 'Academic Registry', href: `${ACADEMIC_OPERATIONS_RUNTIME_UI_BASE}/academic-registry` },
  { key: 'curriculum', title: 'Curriculum', href: `${ACADEMIC_OPERATIONS_RUNTIME_UI_BASE}/curriculum` },
  { key: 'timetable', title: 'Timetable', href: `${ACADEMIC_OPERATIONS_RUNTIME_UI_BASE}/timetable` },
  { key: 'attendance', title: 'Attendance', href: `${ACADEMIC_OPERATIONS_RUNTIME_UI_BASE}/attendance` },
  { key: 'assessment', title: 'Assessment', href: `${ACADEMIC_OPERATIONS_RUNTIME_UI_BASE}/assessment` },
  { key: 'teaching-load', title: 'Teaching Load', href: `${ACADEMIC_OPERATIONS_RUNTIME_UI_BASE}/teaching-load` },
  { key: 'internship', title: 'Internship', href: `${ACADEMIC_OPERATIONS_RUNTIME_UI_BASE}/internship` },
  { key: 'signals', title: 'Signals', href: `${ACADEMIC_OPERATIONS_RUNTIME_UI_BASE}/signals` },
] as const;
