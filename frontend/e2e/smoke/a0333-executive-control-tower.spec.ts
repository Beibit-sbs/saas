import { expect, test, type Page } from "@playwright/test";
import {
  MetricFailureMode,
  MetricGroupId,
  MetricReadiness,
  MetricRuntimeStatus,
  type AssignmentExecutionSummaryResponse,
  type AuditComplianceSummaryResponse,
  type DepartmentPerformanceSummaryResponse,
  type DocumentWorkflowSummaryResponse,
  type CorrespondenceWorkflowSummaryResponse,
  type DecreeWorkflowSummaryResponse,
  type EvidenceLink,
  type ExecutiveControlTowerHealthResponse,
  type ExecutiveControlTowerMetric,
  type ExecutiveControlTowerMetricGroup,
  type ExecutiveControlTowerSummaryResponse,
  type MetricDetailResponse,
  type MetricRegistryResponse,
  type SlaRiskBottleneckSummaryResponse,
  type StrategyKpiSummaryResponse,
} from "@/modules/executive-control-tower/types";

const EXECUTIVE_BFF_BASE = "/api/bff/admin/executive-control-tower";
const TRUSTED_DATA_SOURCE = "computed_from_governance_workflows";

const FULL_PERMISSIONS = [
  "platform.admin.read",
  "admin.executive_control_tower.read",
  "admin.executive_control_tower.summary.read",
  "admin.executive_control_tower.assignments.read",
  "admin.executive_control_tower.documents.read",
  "admin.executive_control_tower.sla_risk.read",
  "admin.executive_control_tower.strategy.read",
  "admin.executive_control_tower.audit.read",
  "admin.executive_control_tower.department.read",
  "admin.executive_control_tower.metric_registry.read",
] as const;

const LIMITED_PERMISSIONS = [
  "platform.admin.read",
  "admin.executive_control_tower.read",
  "admin.executive_control_tower.summary.read",
] as const;

function baseResponse() {
  return {
    fake_metrics: false,
    data_source: TRUSTED_DATA_SOURCE,
    incomplete_data: true,
    generated_at: "2026-05-21T12:00:00Z",
    limitations: ["Read-only backend foundation only"],
  };
}

function makeEvidenceLink(index: number): EvidenceLink {
  return {
    label: `Evidence ${index}`,
    source_module: "governance_workflows",
    source_entity: "WorkflowRecord",
    source_table: "governance_workflow_events",
    reference_field: "workflow_id",
    reference_value: `gw-${index}`,
    url: null,
    available: true,
    limitations: ["Evidence is read-only during foundation phase."],
  };
}

function makeMetric(
  metricId: string,
  groupId: MetricGroupId,
  overrides: Partial<ExecutiveControlTowerMetric> = {},
): ExecutiveControlTowerMetric {
  return {
    metric_id: metricId,
    metric_group: groupId,
    label: `Metric ${metricId}`,
    description: `Executive control tower metric ${metricId}`,
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
    evidence_links: [makeEvidenceLink(1)],
    data_source: TRUSTED_DATA_SOURCE,
    fake_metrics: false,
    incomplete_data: true,
    limitations: ["Read-only backend foundation only"],
    failure_mode: MetricFailureMode.INCOMPLETE_DATA,
    runtime_status: MetricRuntimeStatus.FOUNDATION_CONTRACT_ONLY,
    readiness: MetricReadiness.CONTRACT_DEFINED,
    ...overrides,
  };
}

function makeGroup(
  groupId: MetricGroupId,
  label: string,
  description: string,
  metrics: ExecutiveControlTowerMetric[],
): ExecutiveControlTowerMetricGroup {
  return {
    group_id: groupId,
    label,
    description,
    metrics,
    fake_metrics: false,
    data_source: TRUSTED_DATA_SOURCE,
    incomplete_data: true,
    limitations: ["Read-only backend foundation only"],
  };
}

function makeSectionResponse<T extends { metric_group: string; group_label: string; metrics: ExecutiveControlTowerMetric[] }>(
  metric_group: MetricGroupId,
  group_label: string,
  metrics: ExecutiveControlTowerMetric[],
): T {
  return {
    ...baseResponse(),
    metric_group,
    group_label,
    metrics,
  } as unknown as T;
}

const overviewMetrics = [
  makeMetric("overview-1", MetricGroupId.EXECUTIVE_OVERVIEW, {
    label: "Decision-ready items",
    value: null,
  }),
  makeMetric("overview-2", MetricGroupId.EXECUTIVE_OVERVIEW, {
    label: "Evidence-linked escalations",
    value: 0,
  }),
];

const assignmentMetrics = [
  makeMetric("assignment-1", MetricGroupId.ASSIGNMENT_EXECUTION, {
    label: "Assignments due this week",
    value: 3,
  }),
];

const documentMetrics = [
  makeMetric("document-1", MetricGroupId.DOCUMENT_WORKFLOW, {
    label: "Documents under review",
    value: 5,
  }),
];

const decreeMetrics = [
  makeMetric("decree-1", MetricGroupId.DECREE_WORKFLOW, {
    label: "Decrees pending signing metadata",
    value: 2,
  }),
];

const correspondenceMetrics = [
  makeMetric("correspondence-1", MetricGroupId.CORRESPONDENCE_WORKFLOW, {
    label: "Outgoing correspondence registry count",
    value: 4,
  }),
];

const slaRiskMetrics = [
  makeMetric("sla-1", MetricGroupId.SLA_RISK_BOTTLENECK, {
    label: "SLA breaches pending review",
    value: null,
    runtime_status: MetricRuntimeStatus.UNAVAILABLE,
    readiness: MetricReadiness.INCOMPLETE_SOURCE,
  }),
];

const strategyMetrics = [
  makeMetric("strategy-1", MetricGroupId.STRATEGY_KPI, {
    label: "Strategy initiative completion",
    value: null,
    runtime_status: MetricRuntimeStatus.DEFERRED_UNTIL_STRATEGY_MODULE,
    readiness: MetricReadiness.FUTURE_CONTRACT,
    limitations: ["Deferred until the strategy source module exists."],
  }),
];

const auditMetrics = [
  makeMetric("audit-1", MetricGroupId.AUDIT_COMPLIANCE, {
    label: "Audit exceptions with evidence",
    value: 4,
  }),
];

const departmentMetrics = [
  makeMetric("department-1", MetricGroupId.DEPARTMENT_PERFORMANCE, {
    label: "Departments with incomplete operational evidence",
    value: null,
  }),
];

const SUMMARY_RESPONSE: ExecutiveControlTowerSummaryResponse = {
  ...baseResponse(),
  groups: [
    makeGroup(
      MetricGroupId.EXECUTIVE_OVERVIEW,
      "Executive Overview",
      "Overview metrics",
      overviewMetrics,
    ),
  ],
};

const ASSIGNMENTS_RESPONSE: AssignmentExecutionSummaryResponse = makeSectionResponse(
  MetricGroupId.ASSIGNMENT_EXECUTION,
  "Assignment Execution",
  assignmentMetrics,
);

const DOCUMENTS_RESPONSE: DocumentWorkflowSummaryResponse = makeSectionResponse(
  MetricGroupId.DOCUMENT_WORKFLOW,
  "Document Workflow",
  documentMetrics,
);

const DECREES_RESPONSE: DecreeWorkflowSummaryResponse = makeSectionResponse(
  MetricGroupId.DECREE_WORKFLOW,
  "Decree Workflow",
  decreeMetrics,
);

const CORRESPONDENCE_RESPONSE: CorrespondenceWorkflowSummaryResponse = makeSectionResponse(
  MetricGroupId.CORRESPONDENCE_WORKFLOW,
  "Correspondence Workflow",
  correspondenceMetrics,
);

const SLA_RISK_RESPONSE: SlaRiskBottleneckSummaryResponse = makeSectionResponse(
  MetricGroupId.SLA_RISK_BOTTLENECK,
  "SLA / Risk / Bottleneck",
  slaRiskMetrics,
);

const STRATEGY_RESPONSE: StrategyKpiSummaryResponse = makeSectionResponse(
  MetricGroupId.STRATEGY_KPI,
  "Strategy KPI",
  strategyMetrics,
);

const AUDIT_RESPONSE: AuditComplianceSummaryResponse = makeSectionResponse(
  MetricGroupId.AUDIT_COMPLIANCE,
  "Audit / Compliance",
  auditMetrics,
);

const DEPARTMENTS_RESPONSE: DepartmentPerformanceSummaryResponse = makeSectionResponse(
  MetricGroupId.DEPARTMENT_PERFORMANCE,
  "Department Performance",
  departmentMetrics,
);

const REGISTRY_METRICS = Array.from({ length: 79 }, (_, index) =>
  makeMetric(`metric-${index + 1}`, MetricGroupId.EXECUTIVE_OVERVIEW, {
    label: `Metric ${index + 1}`,
    permission_required: "admin.executive_control_tower.metric_registry.read",
    evidence_links: [makeEvidenceLink(index + 1)],
  }),
);

const REGISTRY_RESPONSE: MetricRegistryResponse = {
  ...baseResponse(),
  groups: [
    makeGroup(
      MetricGroupId.EXECUTIVE_OVERVIEW,
      "Executive Overview",
      "Overview metrics",
      REGISTRY_METRICS,
    ),
  ],
  total_metrics: 79,
};

const HEALTH_RESPONSE: ExecutiveControlTowerHealthResponse = {
  ...baseResponse(),
  total_groups: 9,
  total_metrics: 79,
  registry_valid: true,
  validation_errors: [],
  read_only_foundation: true,
  runtime_status: MetricRuntimeStatus.FOUNDATION_CONTRACT_ONLY,
};

function metricDetail(metricId: string): MetricDetailResponse {
  const metric = REGISTRY_METRICS.find((item) => item.metric_id === metricId) ?? makeMetric(metricId, MetricGroupId.EXECUTIVE_OVERVIEW);
  return {
    ...baseResponse(),
    metric,
  };
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

async function stubAuthSession(
  page: Page,
  options: { permissions?: readonly string[]; roles?: string[] } = {},
) {
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
          displayName: "Executive Control Tower Admin",
          roles: options.roles ?? ["admin"],
          permissions: options.permissions ?? FULL_PERMISSIONS,
          tenantId: 1,
        },
      }),
    });
  });
}

async function stubExecutiveApis(
  page: Page,
  options: { summaryMode?: "trusted" | "fake" | "wrong-data-source" } = {},
) {
  await page.route(`**${EXECUTIVE_BFF_BASE}**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;

    const ok = async (body: unknown, status = 200) => {
      await route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(body),
      });
    };

    if (request.method() !== "GET") {
      await route.fulfill({
        status: 405,
        contentType: "application/json",
        body: JSON.stringify({ detail: `Unexpected method ${request.method()}` }),
      });
      return;
    }

    if (path === `${EXECUTIVE_BFF_BASE}/summary`) {
      if (options.summaryMode === "fake") {
        await ok({ ...SUMMARY_RESPONSE, fake_metrics: true });
        return;
      }
      if (options.summaryMode === "wrong-data-source") {
        await ok({ ...SUMMARY_RESPONSE, data_source: "hardcoded_mock" });
        return;
      }
      await ok(SUMMARY_RESPONSE);
      return;
    }

    if (path === `${EXECUTIVE_BFF_BASE}/assignments`) {
      await ok(ASSIGNMENTS_RESPONSE);
      return;
    }

    if (path === `${EXECUTIVE_BFF_BASE}/documents`) {
      await ok(DOCUMENTS_RESPONSE);
      return;
    }

    if (path === `${EXECUTIVE_BFF_BASE}/decrees`) {
      await ok(DECREES_RESPONSE);
      return;
    }

    if (path === `${EXECUTIVE_BFF_BASE}/correspondence`) {
      await ok(CORRESPONDENCE_RESPONSE);
      return;
    }

    if (path === `${EXECUTIVE_BFF_BASE}/sla-risk`) {
      await ok(SLA_RISK_RESPONSE);
      return;
    }

    if (path === `${EXECUTIVE_BFF_BASE}/strategy-kpis`) {
      await ok(STRATEGY_RESPONSE);
      return;
    }

    if (path === `${EXECUTIVE_BFF_BASE}/audit-compliance`) {
      await ok(AUDIT_RESPONSE);
      return;
    }

    if (path === `${EXECUTIVE_BFF_BASE}/department-performance`) {
      await ok(DEPARTMENTS_RESPONSE);
      return;
    }

    if (path === `${EXECUTIVE_BFF_BASE}/metric-registry`) {
      await ok(REGISTRY_RESPONSE);
      return;
    }

    if (path === `${EXECUTIVE_BFF_BASE}/health`) {
      await ok(HEALTH_RESPONSE);
      return;
    }

    if (path.startsWith(`${EXECUTIVE_BFF_BASE}/metrics/`)) {
      await ok(metricDetail(path.split("/").at(-1) ?? "metric-1"));
      return;
    }

    await route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ detail: `Unhandled test route: ${path}` }),
    });
  });
}

async function expectNoMutationUi(page: Page) {
  await expect(page.getByRole("button", { name: /dispatch|send now|escalate|auto-?approve|auto-?sign/i })).toHaveCount(0);
  await expect(page.getByRole("link", { name: /dispatch|send now|escalate|auto-?approve|auto-?sign/i })).toHaveCount(0);
}

test.beforeEach(async ({ page }) => {
  await forceEnglishLocale(page);
});

test.describe("A-033.3 executive control tower smoke", () => {
  test("overview route renders trusted overview labels and read-only state", async ({ page }) => {
    await stubAuthSession(page);
    await stubExecutiveApis(page);

    await page.goto("/console/executive-control-tower");

    await expect(page.getByRole("heading", { name: /Executive Control Tower/i }).first()).toBeVisible();
    await expect(page.getByText(/Computed from governance workflows/i).first()).toContainText(
      /Computed from governance workflows/i,
    );
    await expect(page.getByText(/No automated decision is made by this dashboard/i).first()).toContainText(
      /No automated decision is made by this dashboard/i,
    );
    await expect(page.getByText(/Executive Overview/i)).toBeVisible();
    await expect(page.getByText(/Incomplete data remains visible while the backend foundation matures/i)).toBeVisible();
    await expectNoMutationUi(page);
  });

  test("metric registry route renders backend metric contract and detail drawer", async ({ page }) => {
    await stubAuthSession(page);
    await stubExecutiveApis(page);

    await page.goto("/console/executive-control-tower/metric-registry");

    await expect(page.getByRole("heading", { name: /Metric Registry/i })).toBeVisible();
    await expect(page.getByText(/79 backend metrics are listed with formulas, permissions, and evidence/i)).toBeVisible();
    await expect(page.getByRole("columnheader", { name: /^Runtime$/i })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: /^Readiness$/i })).toBeVisible();
    await expect(page.getByText(/Metric 79/i)).toBeVisible();

    await page.getByRole("button", { name: /Open detail/i }).first().click();
    await expect(page.getByRole("heading", { name: /Metric detail/i })).toBeVisible();
    await expect(page.getByText(/^Formula$/i)).toBeVisible();
    await expect(page.getByLabel("Metric detail").getByText(/^Permission$/i)).toBeVisible();
    await expect(page.getByText(/^Limitations$/i).first()).toBeVisible();
    await expect(page.getByText(/Evidence 1/i)).toBeVisible();
    await expect(page.getByText(/Evidence is read-only during foundation phase/i)).toBeVisible();
    await expect(page.getByText(/fake KPI/i)).toHaveCount(0);
  });

  test("assignments route shows operational visibility wording and no punitive controls", async ({ page }) => {
    await stubAuthSession(page);
    await stubExecutiveApis(page);

    await page.goto("/console/executive-control-tower/assignments");

    await expect(page.getByRole("heading", { name: /Assignment Execution/i })).toBeVisible();
    await expect(page.getByText(/Operational visibility only with no ranking or punitive behavior/i).first()).toBeVisible();
    await expect(page.getByText(/No executor punishment or ranking/i)).toBeVisible();
    await expectNoMutationUi(page);
  });

  test("documents route renders document decree and correspondence panels with honest boundaries", async ({ page }) => {
    await stubAuthSession(page);
    await stubExecutiveApis(page);

    await page.goto("/console/executive-control-tower/documents");

    await expect(page.getByRole("heading", { name: /Document Workflow/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /^Document Workflow$/i }).first()).toBeVisible();
    await expect(page.getByRole("heading", { name: /^Decree Workflow$/i }).first()).toBeVisible();
    await expect(page.getByRole("heading", { name: /^Correspondence Workflow$/i }).first()).toBeVisible();
    await expect(page.getByText(/Signed metadata only where applicable. No fake delivery status and no e-signature claim/i)).toBeVisible();
    await expect(page.getByText(/Signed metadata only where relevant. No fake delivery or dispatch claims/i)).toBeVisible();
    await expect(page.getByText(/provider delivery/i)).toHaveCount(0);
  });

  test("sla and risk route renders no auto-escalation or hidden score language", async ({ page }) => {
    await stubAuthSession(page);
    await stubExecutiveApis(page);

    await page.goto("/console/executive-control-tower/sla-risk");

    await expect(page.getByRole("heading", { name: /SLA \/ Risk \/ Bottleneck/i }).first()).toBeVisible();
    await expect(page.getByText(/Operational SLA and bottleneck visibility with no auto-escalation action/i).first()).toBeVisible();
    await expect(page.getByText(/Operational indicators only. No auto-escalation button and no hidden score/i)).toBeVisible();
    await expect(page.getByText(/Unavailable/i)).toBeVisible();
    await expect(page.getByTestId("incomplete-data-notice").first()).toBeVisible();
  });

  test("strategy route renders deferred future-contract state without invented progress", async ({ page }) => {
    await stubAuthSession(page);
    await stubExecutiveApis(page);

    await page.goto("/console/executive-control-tower/strategy");

    await expect(page.getByRole("heading", { name: /Strategy KPI/i })).toBeVisible();
    await expect(page.getByText(/Future-contract metrics only. No fake progress and no invented initiatives/i).first()).toBeVisible();
    await expect(page.getByText(/Future-contract strategy metrics remain deferred until a real strategy source exists/i)).toBeVisible();
    await expect(page.getByText(/Future contract/i).first()).toBeVisible();
  });

  test("audit route renders read-only compliance language without production or L5/L6 claims", async ({ page }) => {
    await stubAuthSession(page);
    await stubExecutiveApis(page);

    await page.goto("/console/executive-control-tower/audit");

    await expect(page.getByRole("heading", { name: /Audit \/ Compliance/i }).first()).toBeVisible();
    await expect(page.getByText(/Read-only audit visibility with limitations shown explicitly/i).first()).toBeVisible();
    await expect(page.getByText(/Audit and compliance visibility only. No production-ready or L5\/L6 claim is made here/i)).toBeVisible();
    await expect(page.getByText(/^Limitations$/i).first()).toBeVisible();
  });

  test("departments route renders operational visibility without ranking or scoring", async ({ page }) => {
    await stubAuthSession(page);
    await stubExecutiveApis(page);

    await page.goto("/console/executive-control-tower/departments");

    await expect(page.getByRole("heading", { name: /Department Performance/i }).first()).toBeVisible();
    await expect(page.getByText(/Operational visibility only with no employee ranking or punitive score/i).first()).toBeVisible();
    await expect(page.getByText(/Operational visibility only. No employee ranking and no punitive score/i).first()).toBeVisible();
  });

  test("permission gate blocks metric registry route when registry permission is missing", async ({ page }) => {
    await stubAuthSession(page, { permissions: LIMITED_PERMISSIONS, roles: ["auditor"] });
    await stubExecutiveApis(page);

    await page.goto("/console/executive-control-tower/metric-registry");
    await page.waitForLoadState("networkidle");

    await expect(page.getByRole("heading", { name: /Access Denied/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Metric Registry/i })).toHaveCount(0);
  });

  test("data quality guard blocks fake metrics and wrong data source responses", async ({ page }) => {
    await stubAuthSession(page);
    await stubExecutiveApis(page, { summaryMode: "fake" });

    await page.goto("/console/executive-control-tower");
    await expect(page.locator('[data-testid="executive-control-tower-data-quality-error"]')).toBeVisible();
    await expect(page.getByText(/fake_metrics=true/i)).toBeVisible();

    const mismatchPage = await page.context().newPage();
    await forceEnglishLocale(mismatchPage);
    await stubAuthSession(mismatchPage);
    await stubExecutiveApis(mismatchPage, { summaryMode: "wrong-data-source" });

    await mismatchPage.goto("/console/executive-control-tower");
    await expect(mismatchPage.locator('[data-testid="executive-control-tower-data-quality-error"]')).toBeVisible();
    await expect(mismatchPage.getByText(/expected computed_from_governance_workflows, received hardcoded_mock/i)).toBeVisible();
    await mismatchPage.close();
  });
});