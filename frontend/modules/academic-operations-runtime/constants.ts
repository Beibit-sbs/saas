export const ACADEMIC_OPERATIONS_RUNTIME_API_BASE = '/api/v1/academic-operations';

export const ACADEMIC_OPERATIONS_RUNTIME_PATHS = {
  runtimeShell: `${ACADEMIC_OPERATIONS_RUNTIME_API_BASE}/runtime-shell`,
  academicRegistryRuntime: '/api/academic-operations/runtime/academic-registry',
} as const;
