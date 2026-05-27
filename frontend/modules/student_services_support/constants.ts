import { PERMISSIONS, type Permission } from '@/shared/config/permissions';
import { getStudentServicesBoundaryLabels } from './boundaryLabels';
import type {
  StudentServicesSafetyFlags,
  StudentServicesSupportRouteDefinition,
  StudentServicesSupportRouteKey,
} from './types';

export const STUDENT_SERVICES_SUPPORT_MODULE = 'student_services_support';
export const STUDENT_SERVICES_SUPPORT_ROUTE_FAMILY = '/console/student-services-support';
export const STUDENT_SERVICES_SUPPORT_API_BASE = '/api/admin/student-services';
export const STUDENT_SERVICES_SUPPORT_PLANNED_ROUTE_COUNT = 10;
export const STUDENT_SERVICES_SUPPORT_BACKEND_ROUTE_COUNT = 15;
export const STUDENT_SERVICES_SUPPORT_PERMISSION_COUNT = 6;
export const STUDENT_SERVICES_SUPPORT_RUNTIME_MODE = 'METADATA_EVIDENCE_READINESS_HUMAN_REVIEW_ONLY';
export const STUDENT_SERVICES_SUPPORT_DATA_SOURCE = 'computed_from_student_services_support_records';

export const STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES = {
  read: PERMISSIONS.STUDENT_SERVICES_SUPPORT_READ,
  write: PERMISSIONS.STUDENT_SERVICES_SUPPORT_WRITE,
  assign: PERMISSIONS.STUDENT_SERVICES_SUPPORT_ASSIGN,
  escalate: PERMISSIONS.STUDENT_SERVICES_SUPPORT_ESCALATE,
  dashboardRead: PERMISSIONS.STUDENT_SERVICES_SUPPORT_DASHBOARD_READ,
  auditRead: PERMISSIONS.STUDENT_SERVICES_SUPPORT_AUDIT_READ,
} as const;

function apiPath(path: string) {
  return `${STUDENT_SERVICES_SUPPORT_API_BASE}${path}`;
}

function endpoint(method: 'GET' | 'POST' | 'PATCH', path: string) {
  return `${method} ${apiPath(path)}`;
}

function routeDefinition(
  key: StudentServicesSupportRouteKey,
  title: string,
  path: string,
  requiredPermission: Permission,
  backendEndpoints: string[],
  dashboardLike = false,
): StudentServicesSupportRouteDefinition {
  return {
    key,
    title,
    path,
    requiredPermission,
    backendEndpoints,
    dashboardLike,
    emptyState: `${title} data is not available yet.`,
    permissionDeniedState: `This route requires ${requiredPermission}.`,
  };
}

export const STUDENT_SERVICES_SUPPORT_SAFETY_FLAGS: StudentServicesSafetyFlags = {
  fake_metrics: false,
  provider_live_enabled: false,
  autonomous_decision_enabled: false,
  hidden_score_present: false,
  human_review_required: true,
  incomplete_data: true,
};

export const STUDENT_SERVICES_SUPPORT_API_PATHS = {
  requests: apiPath('/requests'),
  requestById: (requestId: number) => apiPath(`/requests/${requestId}`),
  requestAssign: (requestId: number) => apiPath(`/requests/${requestId}/assign`),
  requestStatus: (requestId: number) => apiPath(`/requests/${requestId}/status`),
  cases: apiPath('/cases'),
  caseById: (caseId: number) => apiPath(`/cases/${caseId}`),
  caseNotes: (caseId: number) => apiPath(`/cases/${caseId}/notes`),
  caseEvidence: (caseId: number) => apiPath(`/cases/${caseId}/evidence`),
  hardship: apiPath('/hardship'),
  accommodations: apiPath('/accommodations'),
  complaints: apiPath('/complaints'),
  escalations: apiPath('/escalations'),
  dashboardSummary: apiPath('/dashboard/summary'),
} as const;

export const STUDENT_SERVICES_SUPPORT_ROUTES: StudentServicesSupportRouteDefinition[] = [
  routeDefinition(
    'overview',
    'Student Services / Welfare / Support',
    STUDENT_SERVICES_SUPPORT_ROUTE_FAMILY,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read,
    [endpoint('GET', '/requests'), endpoint('GET', '/cases')],
    true,
  ),
  routeDefinition(
    'requests',
    'Service Requests',
    `${STUDENT_SERVICES_SUPPORT_ROUTE_FAMILY}/requests`,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read,
    [endpoint('GET', '/requests'), endpoint('POST', '/requests')],
  ),
  routeDefinition(
    'request-detail',
    'Service Request Detail',
    `${STUDENT_SERVICES_SUPPORT_ROUTE_FAMILY}/requests/[requestId]`,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read,
    [endpoint('GET', '/requests/{request_id}'), endpoint('PATCH', '/requests/{request_id}/assign'), endpoint('PATCH', '/requests/{request_id}/status')],
  ),
  routeDefinition(
    'cases',
    'Support Cases',
    `${STUDENT_SERVICES_SUPPORT_ROUTE_FAMILY}/cases`,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read,
    [endpoint('GET', '/cases'), endpoint('POST', '/cases')],
  ),
  routeDefinition(
    'case-detail',
    'Support Case Detail',
    `${STUDENT_SERVICES_SUPPORT_ROUTE_FAMILY}/cases/[caseId]`,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read,
    [endpoint('GET', '/cases/{case_id}'), endpoint('POST', '/cases/{case_id}/notes'), endpoint('POST', '/cases/{case_id}/evidence')],
  ),
  routeDefinition(
    'hardship',
    'Hardship Readiness',
    `${STUDENT_SERVICES_SUPPORT_ROUTE_FAMILY}/hardship`,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.write,
    [endpoint('POST', '/hardship')],
  ),
  routeDefinition(
    'accommodations',
    'Accommodation Readiness',
    `${STUDENT_SERVICES_SUPPORT_ROUTE_FAMILY}/accommodations`,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.write,
    [endpoint('POST', '/accommodations')],
  ),
  routeDefinition(
    'complaints',
    'Complaints Routing',
    `${STUDENT_SERVICES_SUPPORT_ROUTE_FAMILY}/complaints`,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.write,
    [endpoint('POST', '/complaints')],
  ),
  routeDefinition(
    'escalations',
    'Escalations',
    `${STUDENT_SERVICES_SUPPORT_ROUTE_FAMILY}/escalations`,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.escalate,
    [endpoint('POST', '/escalations')],
  ),
  routeDefinition(
    'dashboard',
    'Student Support Dashboard',
    `${STUDENT_SERVICES_SUPPORT_ROUTE_FAMILY}/dashboard`,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.dashboardRead,
    [endpoint('GET', '/dashboard/summary')],
    true,
  ),
];

export const STUDENT_SERVICES_SUPPORT_NAV_ITEMS = STUDENT_SERVICES_SUPPORT_ROUTES.map((route) => ({
  key: route.key,
  href: route.path.includes('[')
    ? route.path.replace('[requestId]', '1').replace('[caseId]', '1')
    : route.path,
  title: route.title,
}));

export const STUDENT_SERVICES_ROUTE_BOUNDARIES = Object.fromEntries(
  STUDENT_SERVICES_SUPPORT_ROUTES.map((route) => [route.key, getStudentServicesBoundaryLabels(route.key)]),
) as Record<StudentServicesSupportRouteKey, string[]>;
