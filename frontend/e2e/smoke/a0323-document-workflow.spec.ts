import { expect, test, type Page } from "@playwright/test";
import type {
  CorrespondenceItem,
  DashboardSummary,
  Document,
  DocumentDetail,
  OrderDecree,
} from "@/modules/document-workflow/types";

const DOCUMENT_BASE_BFF = "/api/bff/admin/documents";

const FULL_PERMISSIONS = [
  "platform.admin.read",
  "platform.admin.write",
  "admin.dashboard.read",
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
];

const READ_ONLY_PERMISSIONS = [
  "platform.admin.read",
  "admin.dashboard.read",
  "admin.documents.dashboard.read",
  "admin.documents.read",
  "admin.documents.audit.read",
  "admin.decrees.read",
  "admin.correspondence.read",
];

const FIXTURE_DOCUMENT: Document = {
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
  linked_assignment_id: 501,
  linked_decree_id: null,
  version: 3,
  created_at: "2026-05-18T10:00:00Z",
  updated_at: "2026-05-20T10:30:00Z",
  archived_at: null,
};

const FIXTURE_DOCUMENT_DETAIL: DocumentDetail = {
  ...FIXTURE_DOCUMENT,
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
      assignment_id: 501,
      link_type: "SOURCE_DOCUMENT",
      created_by_user_id: 1,
      created_at: "2026-05-20T13:00:00Z",
    },
  ],
};

const FIXTURE_DEGREE: OrderDecree = {
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
  linked_assignment_id: 501,
  created_by_user_id: 1,
  version: 2,
  created_at: "2026-05-18T08:00:00Z",
  updated_at: "2026-05-21T08:30:00Z",
  archived_at: null,
};

const FIXTURE_CORRESPONDENCE_OUTGOING: CorrespondenceItem = {
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
  linked_assignment_id: 501,
  created_by_user_id: 1,
  created_at: "2026-05-21T09:00:00Z",
  updated_at: "2026-05-21T09:10:00Z",
  archived_at: null,
};

const FIXTURE_CORRESPONDENCE_INCOMING: CorrespondenceItem = {
  id: 302,
  tenant_id: 1,
  direction: "INCOMING",
  subject: "Incoming Compliance Request",
  correspondence_type: "LETTER",
  sender_name: "Compliance Officer",
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
};

const FIXTURE_ARCHIVED_DOCUMENT: Document = {
  ...FIXTURE_DOCUMENT,
  id: 102,
  title: "Archived Policy Memo",
  status: "ARCHIVED",
  archived_at: "2026-05-01T09:00:00Z",
};

const FIXTURE_ARCHIVED_DEGREE: OrderDecree = {
  ...FIXTURE_DEGREE,
  id: 202,
  title: "Archived Rector Order",
  status: "ARCHIVED",
  archived_at: "2026-05-02T09:00:00Z",
};

const FIXTURE_ARCHIVED_CORRESPONDENCE: CorrespondenceItem = {
  ...FIXTURE_CORRESPONDENCE_OUTGOING,
  id: 303,
  subject: "Archived Ministry Letter",
  status: "ARCHIVED",
  archived_at: "2026-05-03T09:00:00Z",
};

const FIXTURE_DASHBOARD_REAL: DashboardSummary = {
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
  data_source: "computed_from_documents",
  fake_metrics: false,
  generated_at: "2026-05-21T10:00:00Z",
  incomplete_data: false,
};

const FIXTURE_DASHBOARD_FAKE: DashboardSummary = {
  ...FIXTURE_DASHBOARD_REAL,
  fake_metrics: true,
};

function paginated<T>(items: T[]) {
  return { items, total: items.length, page: 1, page_size: 50 };
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
  options: { permissions?: string[]; roles?: string[] } = {},
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
          displayName: "Test Documents Admin",
          roles: options.roles ?? ["admin"],
          permissions: options.permissions ?? FULL_PERMISSIONS,
          tenantId: 1,
        },
      }),
    });
  });
}

async function stubDocumentWorkflowApis(
  page: Page,
  options: { dashboardMode?: "real" | "fake" } = {},
) {
  await page.route(`**${DOCUMENT_BASE_BFF}**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();

    const ok = async (body: unknown, status = 200) => {
      await route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(body),
      });
    };

    if (method === "GET" && path === `${DOCUMENT_BASE_BFF}/dashboard/summary`) {
      await ok(options.dashboardMode === "fake" ? FIXTURE_DASHBOARD_FAKE : FIXTURE_DASHBOARD_REAL);
      return;
    }

    if (method === "GET" && path === DOCUMENT_BASE_BFF) {
      const items: Document[] = url.searchParams.get("status") === "ARCHIVED"
        ? [FIXTURE_ARCHIVED_DOCUMENT]
        : [FIXTURE_DOCUMENT];
      await ok(paginated(items));
      return;
    }

    if (method === "POST" && path === DOCUMENT_BASE_BFF) {
      const payload = JSON.parse(request.postData() || "{}");
      await ok(
        {
          ...FIXTURE_DOCUMENT,
          id: 150,
          status: "DRAFT",
          title: payload.title ?? "Created Document",
          document_type: payload.document_type ?? "REPORT",
          registry_number: null,
          linked_assignment_id: payload.linked_assignment_id ?? null,
        },
        201,
      );
      return;
    }

    if (method === "GET" && path === `${DOCUMENT_BASE_BFF}/${FIXTURE_DOCUMENT.id}`) {
      await ok(FIXTURE_DOCUMENT_DETAIL);
      return;
    }

    if (method === "GET" && path === `${DOCUMENT_BASE_BFF}/${FIXTURE_DOCUMENT.id}/audit`) {
      await ok([
        {
          id: 701,
          entity_type: "document",
          entity_id: FIXTURE_DOCUMENT.id,
          event_type: "DOCUMENT_APPROVED",
          actor_user_id: 1,
          actor_role: "admin",
          action: "approve",
          payload_json: {},
          created_at: "2026-05-21T10:00:00Z",
        },
      ]);
      return;
    }

    if (method === "GET" && path === `${DOCUMENT_BASE_BFF}/${FIXTURE_DOCUMENT.id}/history`) {
      await ok([
        {
          id: 702,
          document_id: FIXTURE_DOCUMENT.id,
          from_status: "REGISTERED",
          to_status: "UNDER_REVIEW",
          actor_user_id: 1,
          reason: "Sent to review",
          created_at: "2026-05-20T11:00:00Z",
        },
      ]);
      return;
    }

    if (method === "POST" && path.includes(`/link-assignment/`)) {
      await ok({
        id: 999,
        document_id: FIXTURE_DOCUMENT.id,
        assignment_id: 777,
        link_type: "SOURCE_DOCUMENT",
        created_by_user_id: 1,
        created_at: "2026-05-21T10:10:00Z",
      });
      return;
    }

    if (method === "GET" && path === `${DOCUMENT_BASE_BFF}/decrees`) {
      const items: OrderDecree[] = url.searchParams.get("status") === "ARCHIVED"
        ? [FIXTURE_ARCHIVED_DEGREE]
        : [FIXTURE_DEGREE];
      await ok(paginated(items));
      return;
    }

    if (method === "GET" && path === `${DOCUMENT_BASE_BFF}/decrees/${FIXTURE_DEGREE.id}`) {
      await ok(FIXTURE_DEGREE);
      return;
    }

    if (method === "GET" && path === `${DOCUMENT_BASE_BFF}/correspondence`) {
      const items: CorrespondenceItem[] = url.searchParams.get("status") === "ARCHIVED"
        ? [FIXTURE_ARCHIVED_CORRESPONDENCE]
        : [FIXTURE_CORRESPONDENCE_OUTGOING, FIXTURE_CORRESPONDENCE_INCOMING];
      await ok(paginated(items));
      return;
    }

    if (method === "GET" && path === `${DOCUMENT_BASE_BFF}/correspondence/${FIXTURE_CORRESPONDENCE_OUTGOING.id}`) {
      await ok(FIXTURE_CORRESPONDENCE_OUTGOING);
      return;
    }

    if (method === "POST" && path === `${DOCUMENT_BASE_BFF}/correspondence/incoming`) {
      await ok(FIXTURE_CORRESPONDENCE_INCOMING, 201);
      return;
    }

    if (method === "POST" && path === `${DOCUMENT_BASE_BFF}/correspondence/outgoing`) {
      await ok(FIXTURE_CORRESPONDENCE_OUTGOING, 201);
      return;
    }

    if (method === "POST" && path.endsWith("/route")) {
      await ok(FIXTURE_CORRESPONDENCE_OUTGOING);
      return;
    }

    if (method === "POST" && path.endsWith("/register")) {
      await ok(FIXTURE_CORRESPONDENCE_OUTGOING);
      return;
    }

    if (method === "POST" && path.endsWith("/sent-metadata")) {
      await ok({
        ...FIXTURE_CORRESPONDENCE_OUTGOING,
        status: "SENT_METADATA_ONLY",
        sent_at: "2026-05-21T12:00:00Z",
      });
      return;
    }

    if (method === "POST" && path.endsWith("/archive")) {
      await ok({ success: true });
      return;
    }

    await route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ detail: `Unhandled test route: ${method} ${path}` }),
    });
  });
}

test.beforeEach(async ({ page }) => {
  await forceEnglishLocale(page);
});

test.describe("A-032.3 document workflow smoke", () => {
  test("route accessibility and primary headings render across the 6 main routes", async ({ page }) => {
    await stubAuthSession(page);
    await stubDocumentWorkflowApis(page);

    const routes = [
      ["/console/documents", /Document registry/i],
      ["/console/documents/new", /New document/i],
      ["/console/documents/decrees", /Decree registry/i],
      ["/console/documents/correspondence", /Correspondence registry/i],
      ["/console/documents/dashboard", /Document workflow dashboard/i],
      ["/console/documents/archive", /^Archive$/i],
    ] as const;

    for (const [route, heading] of routes) {
      await page.goto(route);
      await expect(page.getByRole("heading", { name: heading })).toBeVisible();
    }
  });

  test("document lifecycle surface renders anti-fake notices and supports draft creation", async ({ page }) => {
    await stubAuthSession(page);
    await stubDocumentWorkflowApis(page);

    await page.goto("/console/documents");
    await expect(page.locator('[data-testid="document-registry-no-hard-delete"]')).toBeVisible();
    await expect(page.getByRole("button", { name: /^delete$/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /hard delete/i })).toHaveCount(0);
    await expect(page.getByRole("link", { name: /^delete$/i })).toHaveCount(0);
    await expect(page.getByRole("link", { name: /hard delete/i })).toHaveCount(0);

    await page.goto(`/console/documents/${FIXTURE_DOCUMENT.id}`);
    await expect(page.locator('[data-testid="signature-metadata-notice"]')).toBeVisible();
    await expect(page.locator('[data-testid="no-automatic-signing-notice"]')).toBeVisible();
    await expect(page.locator('[data-testid="registry-official-notice"]')).toBeVisible();
    await expect(page.locator('[data-testid="assignment-link-human-notice"]')).toBeVisible();
    await expect(page.locator('[data-testid="assignment-link-status-notice"]')).toBeVisible();
    await expect(page.getByRole("button", { name: /approve/i })).toBeVisible();

    await page.goto("/console/documents/new");
    await page.getByPlaceholder("Senate briefing note").fill("E2E Created Document");
    await page.getByRole("button", { name: /Create document/i }).click();
    await expect(page.getByRole("link", { name: /Open created document/i })).toBeVisible();
  });

  test("decree workflow surface exposes signing guardrails and permission-aware actions", async ({ page }) => {
    await stubAuthSession(page);
    await stubDocumentWorkflowApis(page);

    await page.goto("/console/documents/decrees");
    await expect(page.getByText("Appointment Order")).toBeVisible();

    await page.goto(`/console/documents/decrees/${FIXTURE_DEGREE.id}`);
    await expect(page.getByText("Signed metadata only.")).toBeVisible();
    await expect(page.getByText("No auto-signature.")).toBeVisible();
    await expect(page.getByText("No auto-approval.")).toBeVisible();
    await expect(page.getByRole("button", { name: /Record signed metadata/i })).toBeVisible();
    await expect(page.getByText("Registry number is official workflow metadata.")).toBeVisible();
  });

  test("correspondence workflow surface shows metadata-only delivery boundaries", async ({ page }) => {
    await stubAuthSession(page);
    await stubDocumentWorkflowApis(page);

    await page.goto("/console/documents/correspondence");
    await expect(page.getByText("Ministry Response Letter")).toBeVisible();
    await page.getByRole("button", { name: /Select/i }).first().click();
    await expect(page.getByText("Sent metadata only.")).toBeVisible();
    await expect(page.getByText("Delivered metadata only.")).toBeVisible();
    await expect(page.getByText("No provider delivery integration.")).toBeVisible();
    await expect(page.getByText("No fake sent/delivered status.")).toBeVisible();

    await page.goto("/console/documents/correspondence/incoming/new");
    await expect(page.getByRole("heading", { name: /New incoming correspondence/i })).toBeVisible();
    await expect(page.getByText("Received metadata only.")).toBeVisible();

    await page.goto("/console/documents/correspondence/outgoing/new");
    await expect(page.getByRole("heading", { name: /New outgoing correspondence/i })).toBeVisible();
    await expect(page.getByText("Sent metadata only.")).toBeVisible();
    await expect(page.getByText("No provider delivery integration.")).toBeVisible();
  });

  test("dashboard renders trusted metrics and blocks fake metrics payloads", async ({ page }) => {
    await stubAuthSession(page);
    await stubDocumentWorkflowApis(page);

    await page.goto("/console/documents/dashboard");
    await expect(page.locator('[data-testid="computed-from-documents-label"]')).toBeVisible();
    await expect(page.locator('[data-testid="kpi-total-documents"]')).toContainText("10");

    const fakePage = await page.context().newPage();
    await forceEnglishLocale(fakePage);
    await stubAuthSession(fakePage);
    await stubDocumentWorkflowApis(fakePage, { dashboardMode: "fake" });
    await fakePage.goto("/console/documents/dashboard");
    await expect(fakePage.locator('[data-testid="document-workflow-data-quality-error"]')).toBeVisible();
    await expect(fakePage.getByText(/^Dashboard data could not be verified\.$/)).toBeVisible();
    await expect(fakePage.getByText(/fake_metrics=true/i)).toBeVisible();
    await fakePage.close();
  });

  test("archive page renders archived records without hard delete semantics", async ({ page }) => {
    await stubAuthSession(page);
    await stubDocumentWorkflowApis(page);

    await page.goto("/console/documents/archive");
    await expect(page.getByText("Archived Policy Memo")).toBeVisible();
    await expect(page.getByText("Archived Rector Order")).toBeVisible();
    await expect(page.getByText("Archived Ministry Letter")).toBeVisible();
    await expect(page.getByRole("button", { name: /^delete$/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /hard delete/i })).toHaveCount(0);
    await expect(page.getByRole("link", { name: /^delete$/i })).toHaveCount(0);
    await expect(page.getByRole("link", { name: /hard delete/i })).toHaveCount(0);
  });

  test("read-only permissions hide mutation UI and block create route access", async ({ page }) => {
    await stubAuthSession(page, { permissions: READ_ONLY_PERMISSIONS, roles: ["auditor"] });
    await stubDocumentWorkflowApis(page);

    await page.goto("/console/documents");
    await expect(page.getByRole("link", { name: /New document/i })).toHaveCount(0);

    await page.goto(`/console/documents/${FIXTURE_DOCUMENT.id}`);
    await expect(page.getByRole("button", { name: /Approve/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /Link assignment/i })).toHaveCount(0);

    await page.goto("/console/documents/new");
    await expect(page.getByText(/Access Denied/i)).toBeVisible();
  });
});