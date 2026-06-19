import { expect, test, type Page } from "@playwright/test";

const EXECUTIVE_BASE_BFF = "/api/bff/admin/executive-control-tower";
const RECTOR_BASE_BFF = "/api/bff/admin/rector-assignments";
const DOCUMENT_BASE_BFF = "/api/bff/admin/documents";

const TRUSTED_EXECUTIVE_SOURCE = "computed_from_governance_workflows";
const TRUSTED_RECTOR_SOURCE = "computed_from_assignments";
const TRUSTED_DOCUMENT_SOURCE = "computed_from_documents";

const FULL_PERMISSIONS = [
  "platform.admin.read",
  "platform.admin.write",
  "admin.dashboard.read",
  "admin.executive_control_tower.read",
  "admin.executive_control_tower.summary.read",
  "admin.executive_control_tower.assignments.read",
  "admin.executive_control_tower.documents.read",
  "admin.executive_control_tower.sla_risk.read",
  "admin.executive_control_tower.strategy.read",
  "admin.executive_control_tower.audit.read",
  "admin.executive_control_tower.department.read",
  "admin.executive_control_tower.metric_registry.read",
  "admin.rector_assignments.dashboard.read",
  "admin.rector_assignments.read",
  "admin.rector_assignments.read_all",
  "admin.rector_assignments.read_department",
  "admin.rector_assignments.create",
  "admin.rector_assignments.assign",
  "admin.rector_assignments.accept",
  "admin.rector_assignments.return",
  "admin.rector_assignments.complete",
  "admin.rector_assignments.escalate",
  "admin.rector_assignments.cancel",
  "admin.rector_assignments.archive",
  "admin.rector_assignments.status.change",
  "admin.rector_assignments.report.submit",
  "admin.rector_assignments.report.review",
  "admin.rector_assignments.evidence.attach",
  "admin.rector_assignments.comment",
  "admin.rector_assignments.audit.read",
  "admin.rector_assignments.templates.manage",
  "admin.rector_assignments.outbox.read",
  "admin.rector_assignments.sla.manage",
  "admin.documents.dashboard.read",
  "admin.documents.admin",
  "admin.documents.read",
  "admin.documents.create",
  "admin.documents.update",
  "admin.documents.register",
  "admin.documents.review",
  "admin.documents.approve",
  "admin.documents.signed_metadata.record",
  "admin.documents.archive",
  "admin.documents.audit.read",
  "admin.documents.link_assignment",
  "admin.decrees.read",
  "admin.decrees.create",
  "admin.decrees.update",
  "admin.decrees.legal_review",
  "admin.decrees.approve_signing",
  "admin.decrees.signed_metadata.record",
  "admin.decrees.register",
  "admin.decrees.archive",
  "admin.correspondence.read",
  "admin.correspondence.create",
  "admin.correspondence.register",
  "admin.correspondence.route",
  "admin.correspondence.sent_metadata.record",
  "admin.correspondence.archive",
  "admin.resolutions.create",
  "admin.resolutions.link_assignment",
] as const;

const EXECUTIVE_BASE_RESPONSE = {
  fake_metrics: false,
  data_source: TRUSTED_EXECUTIVE_SOURCE,
  incomplete_data: true,
  generated_at: "2026-05-22T09:00:00Z",
  limitations: ["Read-only backend foundation only"],
};

const SUMMARY_RESPONSE = {
  ...EXECUTIVE_BASE_RESPONSE,
  groups: [
    {
      group_id: "executive_overview",
      label: "Executive Overview",
      description: "Overview metrics",
      fake_metrics: false,
      data_source: TRUSTED_EXECUTIVE_SOURCE,
      incomplete_data: true,
      limitations: ["Read-only backend foundation only"],
      metrics: [
        {
          metric_id: "overview-1",
          metric_group: "executive_overview",
          label: "Decision-ready items",
          description: "Executive overview metric",
          value: null,
          unit: null,
          source_module: "governance_workflows",
          source_entities: ["WorkflowRecord"],
          source_tables: ["governance_workflow_events"],
          source_fields: ["status"],
          calculation_method: "read_only_registry_contract",
          formula: "count(*)",
          tenant_scope: "tenant_id_required",
          permission_required: "admin.executive_control_tower.read",
          freshness_timestamp: null,
          staleness_threshold_minutes: 60,
          evidence_links: [
            {
              label: "Evidence 1",
              source_module: "governance_workflows",
              source_entity: "WorkflowRecord",
              source_table: "governance_workflow_events",
              reference_field: "workflow_id",
              reference_value: "gw-1",
              url: null,
              available: true,
              limitations: ["Evidence is read-only during foundation phase."],
            },
          ],
          data_source: TRUSTED_EXECUTIVE_SOURCE,
          fake_metrics: false,
          incomplete_data: true,
          limitations: ["Read-only backend foundation only"],
          failure_mode: "INCOMPLETE_DATA",
          runtime_status: "FOUNDATION_CONTRACT_ONLY",
          readiness: "CONTRACT_DEFINED",
        },
      ],
    },
  ],
};

const ASSIGNMENTS_RESPONSE = {
  ...EXECUTIVE_BASE_RESPONSE,
  metric_group: "assignment_execution",
  group_label: "Assignment Execution",
  metrics: [
    {
      metric_id: "assignment-1",
      metric_group: "assignment_execution",
      label: "Assignments due this week",
      description: "Assignment execution metric",
      value: 3,
      unit: null,
      source_module: "governance_workflows",
      source_entities: ["WorkflowRecord"],
      source_tables: ["governance_workflow_events"],
      source_fields: ["status"],
      calculation_method: "read_only_registry_contract",
      formula: "count(*)",
      tenant_scope: "tenant_id_required",
      permission_required: "admin.executive_control_tower.assignments.read",
      freshness_timestamp: null,
      staleness_threshold_minutes: 60,
      evidence_links: [],
      data_source: TRUSTED_EXECUTIVE_SOURCE,
      fake_metrics: false,
      incomplete_data: true,
      limitations: ["Operational visibility only. No executor punishment or ranking."],
      failure_mode: "INCOMPLETE_DATA",
      runtime_status: "FOUNDATION_CONTRACT_ONLY",
      readiness: "CONTRACT_DEFINED",
    },
  ],
};

const DOCUMENTS_RESPONSE = {
  ...EXECUTIVE_BASE_RESPONSE,
  metric_group: "document_workflow",
  group_label: "Document Workflow",
  metrics: [
    {
      metric_id: "document-1",
      metric_group: "document_workflow",
      label: "Documents under review",
      description: "Document workflow metric",
      value: 5,
      unit: null,
      source_module: "governance_workflows",
      source_entities: ["WorkflowRecord"],
      source_tables: ["governance_workflow_events"],
      source_fields: ["status"],
      calculation_method: "read_only_registry_contract",
      formula: "count(*)",
      tenant_scope: "tenant_id_required",
      permission_required: "admin.executive_control_tower.documents.read",
      freshness_timestamp: null,
      staleness_threshold_minutes: 60,
      evidence_links: [],
      data_source: TRUSTED_EXECUTIVE_SOURCE,
      fake_metrics: false,
      incomplete_data: true,
      limitations: ["Operational visibility only."],
      failure_mode: "INCOMPLETE_DATA",
      runtime_status: "FOUNDATION_CONTRACT_ONLY",
      readiness: "CONTRACT_DEFINED",
    },
  ],
};

const AUDIT_RESPONSE = {
  ...EXECUTIVE_BASE_RESPONSE,
  metric_group: "audit_compliance",
  group_label: "Audit / Compliance",
  metrics: [
    {
      metric_id: "audit-1",
      metric_group: "audit_compliance",
      label: "Audit exceptions with evidence",
      description: "Audit metric",
      value: 4,
      unit: null,
      source_module: "governance_workflows",
      source_entities: ["WorkflowRecord"],
      source_tables: ["governance_workflow_events"],
      source_fields: ["status"],
      calculation_method: "read_only_registry_contract",
      formula: "count(*)",
      tenant_scope: "tenant_id_required",
      permission_required: "admin.executive_control_tower.audit.read",
      freshness_timestamp: null,
      staleness_threshold_minutes: 60,
      evidence_links: [],
      data_source: TRUSTED_EXECUTIVE_SOURCE,
      fake_metrics: false,
      incomplete_data: true,
      limitations: ["Read-only backend foundation only"],
      failure_mode: "INCOMPLETE_DATA",
      runtime_status: "FOUNDATION_CONTRACT_ONLY",
      readiness: "CONTRACT_DEFINED",
    },
  ],
};

const EMPTY_SECTION_RESPONSE = {
  ...EXECUTIVE_BASE_RESPONSE,
  metric_group: "placeholder",
  group_label: "Placeholder",
  metrics: [],
};

const REGISTRY_RESPONSE = {
  ...EXECUTIVE_BASE_RESPONSE,
  groups: [
    {
      group_id: "executive_overview",
      label: "Executive Overview",
      description: "Registry overview",
      fake_metrics: false,
      data_source: TRUSTED_EXECUTIVE_SOURCE,
      incomplete_data: true,
      limitations: ["Read-only backend foundation only"],
      metrics: [
        {
          metric_id: "metric-1",
          metric_group: "executive_overview",
          label: "Operational visibility metric",
          description: "Operational visibility only",
          value: null,
          unit: null,
          source_module: "governance_workflows",
          source_entities: ["WorkflowRecord"],
          source_tables: ["governance_workflow_events"],
          source_fields: ["status"],
          calculation_method: "read_only_registry_contract",
          formula: "count(*)",
          tenant_scope: "tenant_id_required",
          permission_required: "admin.executive_control_tower.metric_registry.read",
          freshness_timestamp: null,
          staleness_threshold_minutes: 60,
          evidence_links: [],
          data_source: TRUSTED_EXECUTIVE_SOURCE,
          fake_metrics: false,
          incomplete_data: true,
          limitations: ["Read-only backend foundation only"],
          failure_mode: "INCOMPLETE_DATA",
          runtime_status: "FOUNDATION_CONTRACT_ONLY",
          readiness: "CONTRACT_DEFINED",
        },
        {
          metric_id: "metric-2",
          metric_group: "executive_overview",
          label: "Future contract metric",
          description: "Future contract example",
          value: null,
          unit: null,
          source_module: "governance_workflows",
          source_entities: ["WorkflowRecord"],
          source_tables: ["governance_workflow_events"],
          source_fields: ["status"],
          calculation_method: "read_only_registry_contract",
          formula: "count(*)",
          tenant_scope: "tenant_id_required",
          permission_required: "admin.executive_control_tower.metric_registry.read",
          freshness_timestamp: null,
          staleness_threshold_minutes: 60,
          evidence_links: [],
          data_source: TRUSTED_EXECUTIVE_SOURCE,
          fake_metrics: false,
          incomplete_data: true,
          limitations: ["Deferred until the strategy source module exists."],
          failure_mode: "INCOMPLETE_DATA",
          runtime_status: "DEFERRED_UNTIL_STRATEGY_MODULE",
          readiness: "FUTURE_CONTRACT",
        },
        {
          metric_id: "metric-3",
          metric_group: "executive_overview",
          label: "Foundation-only metric",
          description: "Foundation-only example",
          value: null,
          unit: null,
          source_module: "governance_workflows",
          source_entities: ["WorkflowRecord"],
          source_tables: ["governance_workflow_events"],
          source_fields: ["status"],
          calculation_method: "read_only_registry_contract",
          formula: "count(*)",
          tenant_scope: "tenant_id_required",
          permission_required: "admin.executive_control_tower.metric_registry.read",
          freshness_timestamp: null,
          staleness_threshold_minutes: 60,
          evidence_links: [],
          data_source: TRUSTED_EXECUTIVE_SOURCE,
          fake_metrics: false,
          incomplete_data: true,
          limitations: ["Read-only backend foundation only"],
          failure_mode: "UNAVAILABLE",
          runtime_status: "FOUNDATION_CONTRACT_ONLY",
          readiness: "CONTRACT_DEFINED",
        },
      ],
    },
  ],
  total_metrics: 79,
};

const HEALTH_RESPONSE = {
  ...EXECUTIVE_BASE_RESPONSE,
  total_groups: 9,
  total_metrics: 79,
  registry_valid: true,
  validation_errors: [],
  read_only_foundation: true,
  runtime_status: "FOUNDATION_CONTRACT_ONLY",
};

const RECTOR_DASHBOARD = {
  tenant_id: 1,
  computed_at: "2026-05-22T09:00:00Z",
  total_assignments: 12,
  active_count: 5,
  draft_count: 2,
  overdue_count: 1,
  escalated_count: 0,
  completed_count: 4,
  cancelled_count: 0,
  report_submitted_count: 2,
  returned_count: 1,
  due_this_week: 3,
  due_today: 1,
  completion_rate_30d: 0.67,
  average_days_to_complete: 8.5,
  by_status: { ASSIGNED: 3, IN_PROGRESS: 2, COMPLETED: 4, DRAFT: 2, RETURNED: 1 },
  by_priority: { HIGH: 4, NORMAL: 6, LOW: 2 },
  by_unit: [{ unit_id: 1, unit_name: "Academic Department", count: 7 }],
  top_overdue: [],
  data_source: TRUSTED_RECTOR_SOURCE,
  fake_metrics: false,
};

const RECTOR_ASSIGNMENT_DETAIL = {
  id: 1001,
  tenant_id: 1,
  title: "Improve Student Admission Process",
  description: "Placeholder rector assignment used for unified suite E2E hardening.",
  status: "ASSIGNED",
  priority: "HIGH",
  due_date: "2026-06-01",
  recurrence_type: "NONE",
  version: 1,
  is_overdue: false,
  created_by: 1,
  created_at: "2026-05-15T10:00:00Z",
  updated_at: "2026-05-15T10:00:00Z",
  assignees: [
    {
      id: 1,
      assignment_id: 1001,
      user_id: 42,
      role_on_assignment: "RESPONSIBLE",
      assigned_at: "2026-05-15T10:00:00Z",
      is_lead: true,
    },
  ],
  tasks: [
    {
      id: 1,
      assignment_id: 1001,
      title: "Draft proposal document",
      description: "Create the initial proposal",
      is_completed: false,
      sort_order: 1,
    },
  ],
};

const RECTOR_ASSIGNMENT_LIST = [
  RECTOR_ASSIGNMENT_DETAIL,
  {
    ...RECTOR_ASSIGNMENT_DETAIL,
    id: 1002,
    title: "Annual Budget Review Assignment",
    status: "COMPLETED",
    priority: "NORMAL",
    completed_at: "2026-05-19T15:00:00Z",
  },
  {
    ...RECTOR_ASSIGNMENT_DETAIL,
    id: 1003,
    title: "Returned For Revision Assignment",
    status: "RETURNED",
  },
];

const RECTOR_REPORTS = [
  {
    id: 1,
    assignment_id: 1001,
    submitted_by: 42,
    reporting_period_start: "2026-05-15",
    reporting_period_end: "2026-05-20",
    progress_percent: 60,
    summary: "Completed initial review of admission procedures",
    blockers: "None at this time",
    next_steps: "Draft final report",
    status: "SUBMITTED",
    submitted_at: "2026-05-20T08:00:00Z",
  },
];

const RECTOR_EVIDENCE = [
  {
    id: 1,
    assignment_id: 1001,
    evidence_type: "LINK",
    title: "Admission Process Review Document",
    url: "https://demo.example.invalid/admission-review",
    uploaded_by: 42,
    uploaded_at: "2026-05-20T08:05:00Z",
  },
];

const RECTOR_AUDIT = [
  {
    id: 1,
    assignment_id: 1001,
    event_type: "assignment_created",
    actor_id: 1,
    created_at: "2026-05-15T10:00:00Z",
  },
  {
    id: 2,
    assignment_id: 1001,
    event_type: "status_changed",
    actor_id: 42,
    created_at: "2026-05-15T11:00:00Z",
  },
];

const RECTOR_HISTORY = [
  {
    id: 1,
    assignment_id: 1001,
    old_status: null,
    new_status: "ASSIGNED",
    changed_by: 1,
    changed_at: "2026-05-15T10:00:00Z",
    reason: "Initial assignment",
  },
  {
    id: 2,
    assignment_id: 1001,
    old_status: "ASSIGNED",
    new_status: "ACCEPTED",
    changed_by: 42,
    changed_at: "2026-05-15T11:00:00Z",
  },
];

const RECTOR_TEMPLATES = [
  {
    id: 1,
    name: "Standard Assignment Template",
    description: "Default template for rector assignments",
    default_priority: "NORMAL",
    default_due_days: 30,
    default_recurrence_type: "NONE",
    is_active: true,
    created_by: 1,
    created_at: "2026-01-01T00:00:00Z",
  },
];

const DOCUMENT_DASHBOARD = {
  tenant_id: 1,
  total_documents: 10,
  registered_documents: 4,
  under_review_count: 2,
  returned_for_revision_count: 1,
  approved_count: 1,
  signed_count: 1,
  archived_count: 3,
  incoming_correspondence_count: 2,
  outgoing_correspondence_count: 1,
  overdue_document_reviews: 0,
  documents_linked_to_assignments: 1,
  decrees_pending_signature: 1,
  average_review_cycle_days: 6,
  data_source: TRUSTED_DOCUMENT_SOURCE,
  fake_metrics: false,
  generated_at: "2026-05-22T09:00:00Z",
  incomplete_data: false,
};

const DOCUMENT = {
  id: 101,
  tenant_id: 1,
  title: "Senate Briefing Note",
  document_type: "REPORT",
  status: "UNDER_REVIEW",
  registry_number: "DOC-2026-001",
  registry_date: "2026-05-20T10:00:00Z",
  source_department_id: 42,
  owner_user_id: 7,
  created_by_user_id: 1,
  linked_assignment_id: 1001,
  linked_decree_id: null,
  version: 3,
  created_at: "2026-05-18T10:00:00Z",
  updated_at: "2026-05-20T10:30:00Z",
  archived_at: null,
};

const DOCUMENT_DETAIL = {
  ...DOCUMENT,
  versions: [
    {
      id: 301,
      document_id: 101,
      version_number: 3,
      title: "Senate Briefing Note",
      body_text: "Official briefing body text.",
      metadata_json: {},
      created_by_user_id: 1,
      created_at: "2026-05-20T10:00:00Z",
    },
  ],
  reviews: [
    {
      id: 401,
      document_id: 101,
      reviewer_user_id: 17,
      decision: "APPROVED",
      comment: "Ready for final approval.",
      created_at: "2026-05-20T12:00:00Z",
    },
  ],
  assignment_links: [
    {
      id: 601,
      document_id: 101,
      assignment_id: 1001,
      link_type: "SOURCE_DOCUMENT",
      created_by_user_id: 1,
      created_at: "2026-05-20T13:00:00Z",
    },
  ],
};

const DOCUMENTS_LIST = [
  DOCUMENT,
  {
    ...DOCUMENT,
    id: 102,
    title: "Archived Policy Memo",
    status: "ARCHIVED",
    archived_at: "2026-05-01T09:00:00Z",
  },
];

const DECREE = {
  id: 201,
  tenant_id: 1,
  title: "Appointment Order",
  decree_type: "ORDER",
  status: "APPROVED_FOR_SIGNING",
  registry_number: "DEC-2026-010",
  registry_date: "2026-05-21T08:00:00Z",
  effective_date: "2026-05-25",
  signed_by_user_id: null,
  signed_at: null,
  linked_document_id: 101,
  linked_assignment_id: 1001,
  created_by_user_id: 1,
  version: 2,
  created_at: "2026-05-18T08:00:00Z",
  updated_at: "2026-05-21T08:30:00Z",
  archived_at: null,
};

const DECREES_LIST = [
  DECREE,
  {
    ...DECREE,
    id: 202,
    title: "Archived Rector Order",
    status: "ARCHIVED",
    archived_at: "2026-05-02T09:00:00Z",
  },
];

const CORRESPONDENCE_LIST = [
  {
    id: 301,
    tenant_id: 1,
    direction: "OUTGOING",
    subject: "Ministry Response Letter",
    correspondence_type: "LETTER",
    sender_name: null,
    sender_organization: null,
    recipient_name: "Deputy Minister",
    recipient_organization: "Ministry of Education",
    status: "REGISTERED",
    registry_number: "CORR-2026-015",
    registry_date: "2026-05-21T09:00:00Z",
    received_at: null,
    sent_at: null,
    linked_document_id: 101,
    linked_assignment_id: 1001,
    created_by_user_id: 1,
    created_at: "2026-05-21T09:00:00Z",
    updated_at: "2026-05-21T09:10:00Z",
    archived_at: null,
  },
  {
    id: 302,
    tenant_id: 1,
    direction: "INCOMING",
    subject: "Incoming Compliance Request",
    correspondence_type: "LETTER",
    sender_name: "Compliance Placeholder",
    sender_organization: "External Accreditor",
    recipient_name: null,
    recipient_organization: null,
    status: "REGISTERED",
    registry_number: "CORR-2026-016",
    registry_date: "2026-05-21T09:30:00Z",
    received_at: "2026-05-21T09:20:00Z",
    sent_at: null,
    linked_document_id: 101,
    linked_assignment_id: null,
    created_by_user_id: 1,
    created_at: "2026-05-21T09:20:00Z",
    updated_at: "2026-05-21T09:35:00Z",
    archived_at: null,
  },
];

const DOCUMENT_AUDIT = [
  {
    id: 1,
    document_id: 101,
    event_type: "document_registered",
    actor_id: 1,
    created_at: "2026-05-20T10:00:00Z",
  },
];

const DOCUMENT_HISTORY = [
  {
    id: 1,
    document_id: 101,
    old_status: null,
    new_status: "UNDER_REVIEW",
    changed_by_user_id: 1,
    changed_at: "2026-05-20T10:00:00Z",
    reason: "Initial registration",
  },
];

function paginated<T>(items: T[]) {
  return { items, total: items.length, page: 1, page_size: 50 };
}

function escapeRegex(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function baseMatcher(base: string) {
  return new RegExp(`${escapeRegex(base)}(?:$|\\?.*|/.*)`);
}

async function forceEnglishLocale(page: Page) {
  const configuredUrl = process.env.E2E_BASE_URL ?? "https://nginx";
  const parsedUrl = new URL(configuredUrl);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  await page.context().addCookies(
    Array.from(cookieOrigins).map((url) => ({
      name: "app.locale",
      value: "en",
      url,
      httpOnly: false,
      secure: new URL(url).protocol === "https:",
      sameSite: "Lax" as const,
    })),
  );

  await page.addInitScript(() => {
    document.cookie = "app.locale=en; Path=/; SameSite=Lax";
    window.localStorage.setItem("app.language", "en");
  });
}

async function stubAuthSession(page: Page, permissions: readonly string[] = FULL_PERMISSIONS) {
  const cookieUrl = process.env.E2E_BASE_URL ?? "https://nginx";
  const parsedUrl = new URL(cookieUrl);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  const payloadJson = JSON.stringify({
    sub: "test-admin-id",
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  const payload = Buffer.from(payloadJson).toString("base64url");
  const fakeToken = `fakeheader.${payload}.fakesig`;

  const authCookies = Array.from(cookieOrigins).flatMap((url) => {
    const secure = new URL(url).protocol === "https:";
    return [
      {
        name: "admin_token",
        value: fakeToken,
        url,
        httpOnly: true,
        secure,
        sameSite: "Lax" as const,
      },
      {
        name: "app_access_token",
        value: fakeToken,
        url,
        httpOnly: true,
        secure,
        sameSite: "Lax" as const,
      },
    ];
  });

  await page.context().addCookies(authCookies);

  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user: {
          sub: "test-admin-id",
          displayName: "Executive Governance Demo Admin",
          roles: ["admin"],
          permissions,
          tenantId: 1,
        },
      }),
    });
  });
}

async function stubExecutiveApis(page: Page, guardMode: "trusted" | "fake" = "trusted") {
  await page.route(baseMatcher(EXECUTIVE_BASE_BFF), async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    const relative = pathname.slice(EXECUTIVE_BASE_BFF.length) || "/";

    if (relative.endsWith("/summary") || relative === "/") {
      const body = guardMode === "fake"
        ? { ...SUMMARY_RESPONSE, fake_metrics: true, data_source: "untrusted_demo_source" }
        : SUMMARY_RESPONSE;
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
      return;
    }
    if (relative.endsWith("/assignments")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(ASSIGNMENTS_RESPONSE) });
      return;
    }
    if (relative.endsWith("/documents")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(DOCUMENTS_RESPONSE) });
      return;
    }
    if (relative.endsWith("/decrees") || relative.endsWith("/correspondence") || relative.endsWith("/sla-risk") || relative.endsWith("/strategy") || relative.endsWith("/departments")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(EMPTY_SECTION_RESPONSE) });
      return;
    }
    if (relative.endsWith("/audit")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(AUDIT_RESPONSE) });
      return;
    }
    if (relative.endsWith("/metric-registry")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(REGISTRY_RESPONSE) });
      return;
    }
    if (relative.endsWith("/health")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(HEALTH_RESPONSE) });
      return;
    }
    if (relative.includes("/metric-registry/")) {
      const metricId = relative.split("/").at(-1) ?? "metric-1";
      const metric = REGISTRY_RESPONSE.groups[0].metrics.find((item) => item.metric_id === metricId) ?? REGISTRY_RESPONSE.groups[0].metrics[0];
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ...EXECUTIVE_BASE_RESPONSE, metric }),
      });
      return;
    }

    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(EMPTY_SECTION_RESPONSE) });
  });
}

async function stubRectorApis(page: Page) {
  await page.route(baseMatcher(RECTOR_BASE_BFF), async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    const relative = pathname.slice(RECTOR_BASE_BFF.length) || "/";

    if (relative === "/" || relative === "") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(RECTOR_ASSIGNMENT_LIST) });
      return;
    }
    if (relative.endsWith("/dashboard/summary")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(RECTOR_DASHBOARD) });
      return;
    }
    if (relative.endsWith("/templates")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(RECTOR_TEMPLATES) });
      return;
    }
    if (relative.endsWith("/my") || relative.endsWith("/overdue") || relative.endsWith("/escalations") || relative.endsWith("/notifications") || relative.endsWith("/outbox")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(RECTOR_ASSIGNMENT_LIST) });
      return;
    }
    if (relative.endsWith("/sla-policies") || relative.endsWith("/escalation-policies")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
      return;
    }
    if (relative.includes("/1001/reports")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(RECTOR_REPORTS) });
      return;
    }
    if (relative.includes("/1001/evidence")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(RECTOR_EVIDENCE) });
      return;
    }
    if (relative.includes("/1001/comments")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
      return;
    }
    if (relative.includes("/1001/audit")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(RECTOR_AUDIT) });
      return;
    }
    if (relative.includes("/1001/history") || relative.includes("/1001/status-history")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(RECTOR_HISTORY) });
      return;
    }
    if (relative.includes("/1001")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(RECTOR_ASSIGNMENT_DETAIL) });
      return;
    }

    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(RECTOR_ASSIGNMENT_LIST) });
  });
}

async function stubDocumentApis(page: Page) {
  await page.route(baseMatcher(DOCUMENT_BASE_BFF), async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    const relative = pathname.slice(DOCUMENT_BASE_BFF.length) || "/";

    if (relative === "/" || relative === "") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(paginated(DOCUMENTS_LIST)) });
      return;
    }
    if (relative.endsWith("/dashboard/summary")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(DOCUMENT_DASHBOARD) });
      return;
    }
    if (relative.endsWith("/archive")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ documents: DOCUMENTS_LIST.slice(1), decrees: DECREES_LIST.slice(1), correspondence: [] }),
      });
      return;
    }
    if (relative.endsWith("/decrees")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(paginated(DECREES_LIST)) });
      return;
    }
    if (relative.includes("/decrees/201")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(DECREE) });
      return;
    }
    if (relative.endsWith("/correspondence")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(paginated(CORRESPONDENCE_LIST)) });
      return;
    }
    if (relative.includes("/101/audit")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(DOCUMENT_AUDIT) });
      return;
    }
    if (relative.includes("/101/history")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(DOCUMENT_HISTORY) });
      return;
    }
    if (relative.includes("/101")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(DOCUMENT_DETAIL) });
      return;
    }

    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
  });
}

async function bootstrapSuite(page: Page, options: { executiveGuardMode?: "trusted" | "fake"; permissions?: readonly string[] } = {}) {
  await forceEnglishLocale(page);
  await stubAuthSession(page, options.permissions ?? FULL_PERMISSIONS);
  await stubExecutiveApis(page, options.executiveGuardMode ?? "trusted");
  await stubRectorApis(page);
  await stubDocumentApis(page);
}

function forbiddenTextRegex() {
  return /Production ready|Sales ready|GCC ready|L5\/L6|Send now|Dispatch|Auto escalate/i;
}

async function expectNoOverclaim(page: Page) {
  await expect(page.locator("body")).not.toContainText(forbiddenTextRegex());
}

test.describe("A-034.2 unified executive governance suite smoke", () => {
  test("Scenario 1 — auth entry and control tower overview", async ({ page }) => {
    await bootstrapSuite(page);

    await page.goto("/console/executive-control-tower");

    await expect(page.getByTestId("computed-from-governance-workflows-label").first()).toContainText(
      /Computed from governance workflows/i,
    );
    await expect(page.getByTestId("no-automated-decision-label").first()).toContainText(
      /No automated decision is made by this dashboard/i,
    );
    await expect(page.getByTestId("control-tower-nav-tabs")).toBeVisible();
    await expectNoOverclaim(page);
  });

  test("Scenario 2 — control tower trust guards", async ({ page }) => {
    await bootstrapSuite(page, { executiveGuardMode: "fake" });

    await page.goto("/console/executive-control-tower");

    await expect(page.getByTestId("executive-control-tower-data-quality-error")).toBeVisible();
  });

  test("Scenario 3 — rector assignment navigation", async ({ page }) => {
    await bootstrapSuite(page);

    await page.goto("/console/rector-assignments");

    await expect(page.getByRole("heading", { name: /Rector Assignment Registry/i })).toBeVisible();
    await expect(page.getByTestId("nav-sla-policies")).toBeVisible();
    await expectNoOverclaim(page);
  });

  test("Scenario 4 — assignment detail and evidence flow", async ({ page }) => {
    await bootstrapSuite(page);

    await page.goto("/console/rector-assignments/1001");

    await expect(page.getByRole("heading", { name: "Improve Student Admission Process" })).toBeVisible();
    await expect(page.getByText("Reports")).toBeVisible();
    await expect(page.getByText("Evidence")).toBeVisible();
    await expect(page.getByText("Audit")).toBeVisible();
  });

  test("Scenario 5 — document workflow route", async ({ page }) => {
    await bootstrapSuite(page);

    await page.goto("/console/documents");

    await expect(page.getByText("Senate Briefing Note")).toBeVisible();
    await expect(page.getByTestId("document-registry-no-hard-delete")).toBeVisible();
  });

  test("Scenario 6 — decree workflow", async ({ page }) => {
    await bootstrapSuite(page);

    await page.goto("/console/documents/decrees");

    await expect(page.getByText("Appointment Order")).toBeVisible();

    await page.goto("/console/documents/decrees/201");

    await expect(page.getByText("Appointment Order")).toBeVisible();
    await expect(page.getByText("Signed metadata only.")).toBeVisible();
    await expect(page.getByText("No auto-signature.")).toBeVisible();
    await expect(page.getByText("No auto-approval.")).toBeVisible();
  });

  test("Scenario 7 — correspondence workflow", async ({ page }) => {
    await bootstrapSuite(page);

    await page.goto("/console/documents/correspondence");

    await expect(page.getByText("Ministry Response Letter")).toBeVisible();
    await page.getByRole("button", { name: /Select/i }).first().click();
    await expect(page.getByText("Sent metadata only.")).toBeVisible();
    await expect(page.getByText("Delivered metadata only.")).toBeVisible();
    await expect(page.getByText("No provider delivery integration.")).toBeVisible();
  });

  test("Scenario 8 — metric registry", async ({ page }) => {
    await bootstrapSuite(page);

    await page.goto("/console/executive-control-tower/metric-registry");

    await expect(page.getByText("Metric registry")).toBeVisible();
    await expect(page.getByText("Future contract")).toBeVisible();
    await expect(page.getByText("Foundation-only metric")).toBeVisible();
    await expect(page.getByText("Operational visibility", { exact: false })).toBeVisible();
  });

  test("Scenario 9 — audit and archive routes", async ({ page }) => {
    await bootstrapSuite(page);

    await page.goto("/console/rector-assignments/1001/audit");
    await expect(page.getByText("Audit Trail")).toBeVisible();

    await page.goto("/console/documents/101/audit");
    await expect(page.getByText("Document audit trail")).toBeVisible();

    await page.goto("/console/documents/archive");
    await expect(page.getByRole("heading", { name: /^Archive$/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /hard delete/i })).toHaveCount(0);
    await expect(page.getByRole("link", { name: /hard delete/i })).toHaveCount(0);
  });

  test("Scenario 10 — no-overclaim browser scan", async ({ page }) => {
    await bootstrapSuite(page);

    for (const route of [
      "/console/executive-control-tower",
      "/console/rector-assignments",
      "/console/documents",
      "/console/executive-control-tower/metric-registry",
    ]) {
      await page.goto(route);
      await expectNoOverclaim(page);
    }

    await expect(page.locator("body")).not.toContainText(/fake KPI|provider dispatch|live SMS|live email/i);
  });

  test.skip("Scenario 11 — permission denial smoke (NOT_RUN_UNTIL_PERMISSION_FIXTURE)", async () => {
    // Existing auth stubs allow permission variation, but the denial UX contract is not
    // yet fixed as part of this scoped runtime step. Keep this scenario explicitly skipped.
  });

  test("Scenario 12 — suite closeout path", async ({ page }) => {
    await bootstrapSuite(page);

    await page.goto("/console/executive-control-tower");
    await page.getByTestId("control-tower-nav-tabs").getByRole("link", { name: "Assignments" }).click();
    await expect(page).toHaveURL(/\/console\/executive-control-tower\/assignments$/);

    await page.getByTestId("control-tower-nav-tabs").getByRole("link", { name: "Documents" }).click();
    await expect(page).toHaveURL(/\/console\/executive-control-tower\/documents$/);

    await page.getByTestId("control-tower-nav-tabs").getByRole("link", { name: "Metric registry" }).click();
    await expect(page).toHaveURL(/\/console\/executive-control-tower\/metric-registry$/);

    await expect(page.getByText("Future contract")).toBeVisible();
    await expect(page.locator("body")).not.toContainText(/Send now|Dispatch|Auto escalate/i);
  });
});