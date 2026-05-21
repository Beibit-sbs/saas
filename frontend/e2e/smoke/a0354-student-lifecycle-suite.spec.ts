import { expect, test, type Page } from "@playwright/test";

const BFF_BASE = "/api/bff/admin/student-lifecycle";
const BASE_URL = process.env.E2E_BASE_URL ?? "https://nginx";
const TRUSTED_SOURCE = "computed_from_student_lifecycle_metadata";

const FULL_PERMISSIONS = [
  "platform.admin.read",
  "student_lifecycle.dashboard.read",
  "student_lifecycle.health.read",
  "student_lifecycle.applicants.read",
  "student_lifecycle.applicants.create",
  "student_lifecycle.applicants.update",
  "student_lifecycle.applicants.status.update",
  "student_lifecycle.students.read",
  "student_lifecycle.students.create",
  "student_lifecycle.students.update",
  "student_lifecycle.students.status.update",
  "student_lifecycle.enrollment.read",
  "student_lifecycle.enrollment.create",
  "student_lifecycle.enrollment.update",
  "student_lifecycle.enrollment.review",
  "student_lifecycle.records.read",
  "student_lifecycle.records.create",
  "student_lifecycle.records.result_metadata.write",
  "student_lifecycle.transcripts.read",
  "student_lifecycle.transcripts.preview",
  "student_lifecycle.degree_progress.read",
  "student_lifecycle.degree_progress.compute",
  "student_lifecycle.graduation_readiness.review",
  "student_lifecycle.requests.read",
  "student_lifecycle.requests.create",
  "student_lifecycle.requests.review",
  "student_lifecycle.appeals.read",
  "student_lifecycle.appeals.create",
  "student_lifecycle.appeals.review",
  "student_lifecycle.interventions.read",
  "student_lifecycle.interventions.signal.create",
  "student_lifecycle.interventions.plan.create",
  "student_lifecycle.interventions.followup.write",
  "student_lifecycle.audit.read",
  "student_lifecycle.evidence.read",
  "student_lifecycle.evidence.attach",
  "student_lifecycle.admin.read",
] as const;

const DASHBOARD_RESPONSE = {
  tenant_id: 1,
  generated_at: "2026-05-22T12:00:00Z",
  fake_metrics: false,
  data_source: TRUSTED_SOURCE,
  incomplete_data: true,
  applicant_counts_by_status: { UNDER_REVIEW: 1 },
  student_counts_by_status: { ACTIVE: 1 },
  enrollment_counts_by_status: { REGISTRAR_REVIEW: 1 },
  transcript_preview_counts: { GENERATED_UNOFFICIAL_PREVIEW: 1 },
  degree_progress_counts: { HUMAN_REVIEW_REQUIRED: 1 },
  request_counts_by_status: { UNDER_REVIEW: 1 },
  appeal_counts_by_status: { COMMITTEE_REVIEW: 1 },
  intervention_counts_by_status: { ADVISOR_REVIEW_REQUIRED: 1 },
  human_review_required_count: 7,
  provider_integration_enabled: false,
  automated_decision_count: 0,
  hidden_score_present: false,
  limitations: ["Metadata only", "Incomplete data"],
};

const HEALTH_RESPONSE = {
  tenant_id: 1,
  generated_at: "2026-05-22T12:00:00Z",
  module_name: "student_lifecycle",
  route_count: 44,
  table_count: 14,
  fake_metrics: false,
  data_source: TRUSTED_SOURCE,
  incomplete_data: true,
  limitations: ["Metadata only"],
  provider_integration_enabled: false,
  automated_decision_count: 0,
  hidden_score_present: false,
};

const APPLICANTS_RESPONSE = [
  {
    id: 101,
    tenant_id: 1,
    status: "UNDER_REVIEW",
    applicant_code: "applicant-demo-001",
    program_interest: "Demo Program",
    entry_term: "2026-FALL",
    notes: "Synthetic applicant record for browser validation.",
    source_available: true,
    archived_at: null,
    created_at: "2026-05-22T10:00:00Z",
    updated_at: "2026-05-22T10:10:00Z",
    human_review_required: true,
    automated_decision: false,
    provider_integration_enabled: false,
    limitations: ["Metadata only"],
  },
];

const STUDENTS_RESPONSE = [
  {
    id: 201,
    tenant_id: 1,
    status: "ACTIVE",
    student_code: "student-demo-001",
    source_applicant_id: 101,
    program_code: "DEMO-PROGRAM",
    notes: "Synthetic student profile for browser validation.",
    archived_at: null,
    created_at: "2026-05-22T10:20:00Z",
    updated_at: "2026-05-22T10:30:00Z",
    human_review_required: true,
    automated_decision: false,
    provider_integration_enabled: false,
    limitations: ["Metadata only"],
  },
];

const ENROLLMENTS_RESPONSE = [
  {
    id: 301,
    tenant_id: 1,
    status: "REGISTRAR_REVIEW",
    student_id: 201,
    term_code: "2026-FALL",
    notes: "enrollment-demo-001",
    archived_at: null,
    created_at: "2026-05-22T10:40:00Z",
    updated_at: "2026-05-22T10:50:00Z",
    human_review_required: true,
    automated_decision: false,
    provider_integration_enabled: false,
    limitations: ["Metadata only", "Audit-backed transition"],
  },
];

const ACADEMIC_RECORDS_RESPONSE = [
  {
    id: 401,
    tenant_id: 1,
    status: "REVIEW_REQUIRED",
    student_id: 201,
    record_name: "Demo Semester Record",
    source_available: false,
    result_metadata: { record_ref: "record-demo-001" },
    created_at: "2026-05-22T11:00:00Z",
    updated_at: "2026-05-22T11:10:00Z",
    human_review_required: true,
    automated_decision: false,
    provider_integration_enabled: false,
    limitations: ["Metadata only", "Source unavailable"],
  },
];

const TRANSCRIPTS_RESPONSE = [
  {
    id: 501,
    tenant_id: 1,
    status: "GENERATED_UNOFFICIAL_PREVIEW",
    student_id: 201,
    academic_record_id: 401,
    official_document: false,
    preview_payload: { reference: "transcript-preview-demo-001" },
    created_at: "2026-05-22T11:20:00Z",
    updated_at: "2026-05-22T11:30:00Z",
    human_review_required: true,
    automated_decision: false,
    provider_integration_enabled: false,
    limitations: ["Unofficial preview", "Metadata only"],
  },
];

const DEGREE_PROGRESS_RESPONSE = {
  id: 601,
  tenant_id: 1,
  status: "HUMAN_REVIEW_REQUIRED",
  student_id: 201,
  data_source: TRUSTED_SOURCE,
  incomplete_data: true,
  hidden_score_present: false,
  completion_summary: { completed: 90, missing: 10 },
  created_at: "2026-05-22T11:40:00Z",
  updated_at: "2026-05-22T11:50:00Z",
  human_review_required: true,
  automated_decision: false,
  provider_integration_enabled: false,
  limitations: ["Incomplete data", "Computed from available sources only"],
};

const REQUESTS_RESPONSE = [
  {
    id: 701,
    tenant_id: 1,
    status: "UNDER_REVIEW",
    student_id: 201,
    request_type: "LEAVE",
    description: "Demo request metadata only",
    decision_note: null,
    archived_at: null,
    created_at: "2026-05-22T12:00:00Z",
    updated_at: "2026-05-22T12:05:00Z",
    human_review_required: true,
    automated_decision: false,
    provider_integration_enabled: false,
    limitations: ["Metadata only"],
  },
];

const APPEALS_RESPONSE = [
  {
    id: 801,
    tenant_id: 1,
    status: "COMMITTEE_REVIEW",
    student_id: 201,
    appeal_type: "GRADE",
    description: "Demo appeal metadata only",
    decision_note: null,
    archived_at: null,
    created_at: "2026-05-22T12:10:00Z",
    updated_at: "2026-05-22T12:15:00Z",
    human_review_required: true,
    automated_decision: false,
    provider_integration_enabled: false,
    limitations: ["Metadata only"],
  },
];

const INTERVENTIONS_RESPONSE = [
  {
    id: 901,
    tenant_id: 1,
    status: "ADVISOR_REVIEW_REQUIRED",
    student_id: 201,
    signal_type: "ATTENDANCE",
    plan_summary: "Demo support outreach plan",
    hidden_score_present: false,
    followups: [{ step: "Call", scheduled_for: "2026-05-23" }],
    archived_at: null,
    created_at: "2026-05-22T12:20:00Z",
    updated_at: "2026-05-22T12:25:00Z",
    human_review_required: true,
    automated_decision: false,
    provider_integration_enabled: false,
    limitations: ["Support visibility only"],
  },
];

const AUDIT_RESPONSE = [
  {
    id: 1001,
    tenant_id: 1,
    entity_type: "request",
    entity_id: 701,
    event_type: "STUDENT_REQUEST_REVIEWED",
    actor_user_id: "reviewer-demo-001",
    previous_status: "SUBMITTED",
    new_status: "UNDER_REVIEW",
    human_review_required: true,
    automated_decision: false,
    provider_integration_enabled: false,
    action: "review_request",
    request_id: "request-demo-001",
    payload: {},
    created_at: "2026-05-22T12:30:00Z",
  },
];

const EVIDENCE_RESPONSE = [
  {
    id: 1101,
    tenant_id: 1,
    audit_event_id: 1001,
    entity_type: "request",
    entity_id: 701,
    evidence_type: "NOTE",
    evidence_ref: "evidence-demo-001",
    created_at: "2026-05-22T12:35:00Z",
  },
];

const ROUTE_EXPECTATIONS = [
  { path: "/console/student-lifecycle", heading: "Student Lifecycle Suite", boundary: "Provider integration not enabled" },
  { path: "/console/student-lifecycle/applicants", heading: "Applicants", boundary: "Human review required" },
  { path: "/console/student-lifecycle/students", heading: "Students", boundary: "Provider integration not enabled" },
  { path: "/console/student-lifecycle/enrollment", heading: "Enrollment", boundary: "Audit-backed transition" },
  { path: "/console/student-lifecycle/academic-records", heading: "Academic records", boundary: "Source unavailable" },
  { path: "/console/student-lifecycle/transcripts", heading: "Transcript previews", boundary: "Unofficial preview" },
  { path: "/console/student-lifecycle/degree-progress", heading: "Degree progress", boundary: "No automatic graduation eligibility decision" },
  { path: "/console/student-lifecycle/requests", heading: "Student requests", boundary: "Decision metadata only" },
  { path: "/console/student-lifecycle/appeals", heading: "Student appeals", boundary: "No autonomous appeal decision" },
  { path: "/console/student-lifecycle/interventions", heading: "Interventions", boundary: "Support visibility only" },
  { path: "/console/student-lifecycle/audit", heading: "Audit", boundary: "Audit-backed transition" },
] as const;

function pageUrl(path: string) {
  return new URL(path, BASE_URL).toString();
}

async function forceEnglishLocale(page: Page) {
  const parsedUrl = new URL(BASE_URL);
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
  const parsedUrl = new URL(BASE_URL);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  const payloadJson = JSON.stringify({
    sub: "student-lifecycle-admin",
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  const payload = Buffer.from(payloadJson).toString("base64url");
  const fakeToken = `fakeheader.${payload}.fakesig`;

  await page.context().addCookies(
    Array.from(cookieOrigins).flatMap((url) => {
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
    }),
  );

  for (const pattern of ["**/api/auth/me*", "**/api/bff/auth/me*"]) {
    await page.route(pattern, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          authenticated: true,
          user: {
            sub: "student-lifecycle-admin",
            displayName: "Student Lifecycle E2E Admin",
            roles: ["admin"],
            permissions,
            tenantId: 1,
          },
        }),
      });
    });
  }
}

async function stubStudentLifecycleApis(page: Page) {
  await page.route(`**${BFF_BASE}**`, async (route) => {
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
      await ok({ detail: "Mutation not used in smoke E2E." }, 405);
      return;
    }

    if (path === `${BFF_BASE}/dashboard`) return ok(DASHBOARD_RESPONSE);
    if (path === `${BFF_BASE}/health`) return ok(HEALTH_RESPONSE);
    if (path === `${BFF_BASE}/applicants`) return ok(APPLICANTS_RESPONSE);
    if (path === `${BFF_BASE}/students`) return ok(STUDENTS_RESPONSE);
    if (path === `${BFF_BASE}/enrollment`) return ok(ENROLLMENTS_RESPONSE);
    if (path === `${BFF_BASE}/academic-records`) return ok(ACADEMIC_RECORDS_RESPONSE);
    if (path === `${BFF_BASE}/transcripts`) return ok(TRANSCRIPTS_RESPONSE);
    if (path.startsWith(`${BFF_BASE}/degree-progress/`)) return ok(DEGREE_PROGRESS_RESPONSE);
    if (path === `${BFF_BASE}/requests`) return ok(REQUESTS_RESPONSE);
    if (path === `${BFF_BASE}/appeals`) return ok(APPEALS_RESPONSE);
    if (path === `${BFF_BASE}/interventions/plans`) return ok(INTERVENTIONS_RESPONSE);
    if (path === `${BFF_BASE}/audit`) return ok(AUDIT_RESPONSE);
    if (path === `${BFF_BASE}/evidence`) return ok(EVIDENCE_RESPONSE);

    await ok({ detail: `Unhandled Student Lifecycle stub path: ${path}` }, 404);
  });
}

async function bootStudentLifecycle(page: Page, options: { permissions?: readonly string[] } = {}) {
  await forceEnglishLocale(page);
  await stubAuthSession(page, options.permissions ?? FULL_PERMISSIONS);
  await stubStudentLifecycleApis(page);
}

test.describe("A-035.4 Student Lifecycle Suite browser E2E", () => {
  test("Scenario 1 — overview dashboard loads", async ({ page }) => {
    await bootStudentLifecycle(page);

    await page.goto(pageUrl("/console/student-lifecycle"));

    await expect(page.getByRole("heading", { name: "Student Lifecycle Suite", level: 1 })).toBeVisible();
    await expect(page.getByTestId("fake-metrics-label")).toContainText("fake_metrics=false");
    await expect(page.getByTestId("data-source-label")).toContainText(TRUSTED_SOURCE);
    await expect(page.getByTestId("student-lifecycle-boundary-banner")).toContainText("No automated decision is made");
    await expect(page.getByTestId("student-lifecycle-boundary-banner")).toContainText("Provider integration not enabled");
    await expect(page.locator("body")).toContainText("No hidden risk score");
  });

  test("Scenario 2 — applicants route", async ({ page }) => {
    await bootStudentLifecycle(page);

    await page.goto(pageUrl("/console/student-lifecycle/applicants"));

    await expect(page.getByRole("heading", { name: "Applicants", level: 1 })).toBeVisible();
    await expect(page.getByTestId("student-lifecycle-boundary-banner")).toContainText("Human review required");
    await expect(page.getByTestId("student-lifecycle-boundary-banner")).toContainText("No automated decision is made");
    await expect(page.locator("body")).not.toContainText("provider sync");
  });

  test("Scenario 3 — students route", async ({ page }) => {
    await bootStudentLifecycle(page);

    await page.goto(pageUrl("/console/student-lifecycle/students"));

    await expect(page.getByRole("heading", { name: "Students", level: 1 })).toBeVisible();
    await expect(page.getByText("Provider integration not enabled")).toBeVisible();
    await expect(page.getByText("Metadata only")).toBeVisible();
    await expect(page.locator("body")).not.toContainText(/Platonus sync|SIS sync/i);
  });

  test("Scenario 4 — enrollment route", async ({ page }) => {
    await bootStudentLifecycle(page);

    await page.goto(pageUrl("/console/student-lifecycle/enrollment"));

    await expect(page.getByRole("heading", { name: "Enrollment", level: 1 })).toBeVisible();
    await expect(page.getByTestId("student-lifecycle-boundary-banner")).toContainText("Human review required");
    await expect(page.getByTestId("student-lifecycle-boundary-banner")).toContainText("Audit-backed transition");
    await expect(page.getByTestId("enrollment-review-panel")).toBeVisible();
  });

  test("Scenario 5 — academic records route", async ({ page }) => {
    await bootStudentLifecycle(page);

    await page.goto(pageUrl("/console/student-lifecycle/academic-records"));

    await expect(page.getByRole("heading", { name: "Academic records", level: 1 })).toBeVisible();
    await expect(page.locator("body")).toContainText("Source unavailable");
    await expect(page.locator("body")).toContainText("Metadata only");
    await expect(page.locator("body")).not.toContainText("Official document issued");
  });

  test("Scenario 6 — transcripts route with unofficial preview boundaries", async ({ page }) => {
    await bootStudentLifecycle(page);

    await page.goto(pageUrl("/console/student-lifecycle/transcripts"));

    await expect(page.getByRole("heading", { name: "Transcript previews", level: 1 })).toBeVisible();
    await expect(page.locator("body")).toContainText("Unofficial preview");
    await expect(page.locator("body")).toContainText("Official document not issued");
    await expect(page.locator("body")).toContainText("Digital signature not enabled");
    await expect(page.locator("body")).not.toContainText("official transcript issued");
  });

  test("Scenario 7 — degree progress route with human review boundary", async ({ page }) => {
    await bootStudentLifecycle(page);

    await page.goto(pageUrl("/console/student-lifecycle/degree-progress"));

    await expect(page.getByRole("heading", { name: "Degree progress", level: 1 })).toBeVisible();
    await expect(page.locator("body")).toContainText("Human review required");
    await expect(page.locator("body")).toContainText("No automatic graduation eligibility decision");
    await expect(page.locator("body")).toContainText("Incomplete data");
  });

  test("Scenario 8 — requests route with decision metadata boundary", async ({ page }) => {
    await bootStudentLifecycle(page);

    await page.goto(pageUrl("/console/student-lifecycle/requests"));

    await expect(page.getByRole("heading", { name: "Student requests", level: 1 })).toBeVisible();
    await expect(page.getByTestId("student-request-review-panel")).toContainText("Decision metadata only");
    await expect(page.locator("body")).toContainText("Human review required");
    await expect(page.locator("body")).not.toContainText("autonomous decision enabled");
  });

  test("Scenario 9 — appeals route with no autonomous decision boundary", async ({ page }) => {
    await bootStudentLifecycle(page);

    await page.goto(pageUrl("/console/student-lifecycle/appeals"));

    await expect(page.getByRole("heading", { name: "Student appeals", level: 1 })).toBeVisible();
    await expect(page.getByTestId("student-appeal-review-panel")).toContainText("No autonomous appeal decision");
    await expect(page.locator("body")).toContainText("Human review required");
  });

  test("Scenario 10 — interventions route with support visibility boundary", async ({ page }) => {
    await bootStudentLifecycle(page);

    await page.goto(pageUrl("/console/student-lifecycle/interventions"));

    await expect(page.getByRole("heading", { name: "Interventions", level: 1 })).toBeVisible();
    await expect(page.getByTestId("intervention-plan-panel")).toContainText("Support visibility only");
    await expect(page.locator("body")).toContainText("No hidden risk score");
    await expect(page.getByTestId("intervention-plan-panel")).toContainText("No punitive automation");
  });

  test("Scenario 11 — audit route", async ({ page }) => {
    await bootStudentLifecycle(page);

    await page.goto(pageUrl("/console/student-lifecycle/audit"));

    await expect(page.getByRole("heading", { name: "Audit", level: 1 })).toBeVisible();
    await expect(page.locator("body")).toContainText("Audit-backed transition");
    await expect(page.locator("body")).toContainText("No hard delete");
    await expect(page.getByTestId("audit-log-registry").getByTestId("student-lifecycle-audit-trail-panel")).toBeVisible();
  });

  test("Scenario 12 — browser no-overclaim scan", async ({ page }) => {
    await bootStudentLifecycle(page);

    const forbiddenPhrases = [
      "production ready",
      "sales ready",
      "gcc ready",
      "l5",
      "l6",
      "platonus sync",
      "sis sync",
      "official transcript issued",
      "hidden risk score enabled",
      "autonomous decision enabled",
      "automatic graduation eligibility enabled",
      "provider dispatch",
      "send to provider",
      "fake kpi",
    ];

    for (const route of ROUTE_EXPECTATIONS) {
      await page.goto(pageUrl(route.path));
      const bodyText = (await page.locator("body").innerText()).toLowerCase();
      for (const phrase of forbiddenPhrases) {
        expect(bodyText).not.toContain(phrase);
      }
    }
  });

  test("Scenario 13 — permission boundary smoke", async ({ page }) => {
    await bootStudentLifecycle(page, {
      permissions: FULL_PERMISSIONS.filter((permission) => permission !== "student_lifecycle.applicants.read"),
    });

    await page.goto(pageUrl("/console/student-lifecycle/applicants"));

    await expect(page.getByText("Access Denied")).toBeVisible();
    await expect(page.getByText("You don't have permission to view this content.")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Applicants" })).not.toBeVisible();
  });

  test("Scenario 14 — suite closeout route flow", async ({ page }) => {
    await bootStudentLifecycle(page);

    for (const route of ROUTE_EXPECTATIONS) {
      await page.goto(pageUrl(route.path));
      await expect(page.getByRole("heading", { name: route.heading, level: 1 })).toBeVisible();
      await expect(page.locator("body")).toContainText(route.boundary);
    }

    const finalBody = (await page.locator("body").innerText()).toLowerCase();
    expect(finalBody).not.toContain("official transcript issued");
    expect(finalBody).not.toContain("provider dispatch");
    expect(finalBody).not.toContain("send to provider");
    expect(finalBody).not.toContain("autonomous decision enabled");
  });
});