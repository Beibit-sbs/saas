import { expect, test, type Page, type Route } from '@playwright/test';

const BASE_URL = process.env.E2E_BASE_URL ?? 'https://nginx';

async function setSessionCookies(page: Page, baseUrl: string) {
  const parsedUrl = new URL(baseUrl);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  const payloadJson = JSON.stringify({
    sub: 'a0536x-admin',
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  const payload = Buffer.from(payloadJson).toString('base64url');
  const token = `fakeheader.${payload}.fakesig`;

  await page.context().addCookies(
    Array.from(cookieOrigins).flatMap((origin) => {
      const secure = new URL(origin).protocol === 'https:';
      return [
        { name: 'admin_token', value: token, url: origin, httpOnly: true, secure, sameSite: 'Lax' as const },
        { name: 'app_access_token', value: token, url: origin, httpOnly: true, secure, sameSite: 'Lax' as const },
      ];
    }),
  );
}

async function stubAuthFlow(page: Page, permissions: string[]) {
  await page.route('**/api/auth/csrf*', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ csrf_token: 'a0536x-csrf' }),
    });
  });

  await page.route('**/api/auth/me/preferences*', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ language: 'en' }),
    });
  });

  for (const pattern of ['**/api/auth/me*', '**/api/bff/auth/me*']) {
    await page.route(pattern, async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          user: {
            sub: 'a0536x-admin',
            displayName: 'A0536X Admin',
            roles: ['admin'],
            tenantId: 1,
            permissions,
          },
        }),
      });
    });
  }
}

async function stubInnovationApis(page: Page) {
  const shellPayload = {
    tenant_id: 1,
    owner_module: 'innovation_commercialization_extension',
    extension_boundary: 'Innovation / Commercialization Extension over closed A-047 Research Brain',
    runtime_mode: 'read_only_extension_shell',
    canonical_base_vertical: 'research_brain_a047_closed_baselined',
    integration_policy: 'no_live_provider_execution',
    bridge_modules: [
      'research_science',
      'research',
      'research_grants',
      'research_ethics',
      'ip_management',
    ],
  };

  const opportunitiesPayload = {
    tenant_id: 1,
    items: [
      {
        opportunity_id: 'ICX-PIPE-001',
        title: 'Innovation Pipeline Summary',
        stage: 'summary',
        readiness: 'advisory',
        source_module: 'research_science',
        notes: 'Read-only extension summary.',
      },
      {
        opportunity_id: 'ICX-COMM-001',
        title: 'Commercialization Cases Summary',
        stage: 'summary',
        readiness: 'advisory',
        source_module: 'research_science',
        notes: 'Read-only extension summary.',
      },
      {
        opportunity_id: 'ICX-START-001',
        title: 'Startup Incubation Summary',
        stage: 'summary',
        readiness: 'advisory',
        source_module: 'research_science',
        notes: 'Read-only extension summary.',
      },
      {
        opportunity_id: 'ICX-IP-001',
        title: 'Patent/IP Commercialization Summary',
        stage: 'summary',
        readiness: 'advisory',
        source_module: 'ip_management',
        notes: 'Read-only extension summary.',
      },
      {
        opportunity_id: 'ICX-GRANT-001',
        title: 'Grant-to-Product Transition Summary',
        stage: 'summary',
        readiness: 'advisory',
        source_module: 'research_grants',
        notes: 'Read-only extension summary.',
      },
      {
        opportunity_id: 'ICX-LAB-001',
        title: 'Lab-to-Market Workflow Summary',
        stage: 'summary',
        readiness: 'advisory',
        source_module: 'research_science',
        notes: 'Read-only extension summary.',
      },
      {
        opportunity_id: 'ICX-PARTNER-001',
        title: 'Industry Partnership Summary',
        stage: 'summary',
        readiness: 'advisory',
        source_module: 'research_science',
        notes: 'Read-only extension summary.',
      },
      {
        opportunity_id: 'ICX-KPI-001',
        title: 'KPI/Dashboard Summary',
        stage: 'summary',
        readiness: 'advisory',
        source_module: 'research_science',
        notes: 'Read-only extension summary.',
      },
    ],
  };

  for (const pattern of [
    '**/api/admin/innovation-commercialization/shell*',
    '**/api/bff/admin/innovation-commercialization/shell*',
  ]) {
    await page.route(pattern, async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(shellPayload),
      });
    });
  }

  for (const pattern of [
    '**/api/admin/innovation-commercialization/opportunities*',
    '**/api/bff/admin/innovation-commercialization/opportunities*',
  ]) {
    await page.route(pattern, async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(opportunitiesPayload),
      });
    });
  }
}

test.describe('A-053.6X-E2E innovation commercialization extension shell', () => {
  test('validates route, boundary messaging, read-only behavior, and summary coverage', async ({ page }) => {
    await stubAuthFlow(page, ['platform.admin.read', 'research_science.overview.read']);
    await stubInnovationApis(page);
    await setSessionCookies(page, BASE_URL);

    await page.goto(`${BASE_URL}/console/innovation-commercialization`);

    await expect(page).toHaveURL(/\/console\/innovation-commercialization/);

    await expect(page.getByTestId('innovation-commercialization-runtime-shell')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('innovation-commercialization-overview')).toBeVisible();
    await expect(page.getByTestId('innovation-commercialization-opportunities')).toBeVisible();

    await expect(page.getByText('Innovation / Commercialization Extension Shell')).toBeVisible();
    await expect(page.getByTestId('innovation-commercialization-overview')).toContainText(
      'Innovation / Commercialization Extension over closed A-047 Research Brain',
    );

    await expect(page.getByTestId('innovation-commercialization-opportunities')).toContainText('Innovation Pipeline Summary');
    await expect(page.getByTestId('innovation-commercialization-opportunities')).toContainText('Commercialization Cases Summary');
    await expect(page.getByTestId('innovation-commercialization-opportunities')).toContainText('Startup Incubation Summary');
    await expect(page.getByTestId('innovation-commercialization-opportunities')).toContainText('Patent/IP Commercialization Summary');
    await expect(page.getByTestId('innovation-commercialization-opportunities')).toContainText('Grant-to-Product Transition Summary');
    await expect(page.getByTestId('innovation-commercialization-opportunities')).toContainText('Lab-to-Market Workflow Summary');
    await expect(page.getByTestId('innovation-commercialization-opportunities')).toContainText('Industry Partnership Summary');
    await expect(page.getByTestId('innovation-commercialization-opportunities')).toContainText('KPI/Dashboard Summary');

    const actionButtons = page.getByRole('button', {
      name: /create|new|edit|update|delete|save|submit|sync|connect|approve/i,
    });
    await expect(actionButtons).toHaveCount(0);

    await expect(page.locator('body')).toContainText(/No external live provider execution|no_live_provider_execution/i);
    await expect(page.locator('body')).not.toContainText(/production[- ]?ready|L5|L6|GCC|product[- ]?ready/i);
    await expect(page.locator('body')).not.toContainText(/scopus|orcid|web of science|startup registry|patent office/i);
  });

  test('renders deterministic error state when shell APIs fail', async ({ page }) => {
    await stubAuthFlow(page, ['platform.admin.read', 'research_science.overview.read']);
    await setSessionCookies(page, BASE_URL);

    for (const pattern of [
      '**/api/admin/innovation-commercialization/shell*',
      '**/api/bff/admin/innovation-commercialization/shell*',
    ]) {
      await page.route(pattern, async (route: Route) => {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'stubbed shell error' }),
        });
      });
    }

    for (const pattern of [
      '**/api/admin/innovation-commercialization/opportunities*',
      '**/api/bff/admin/innovation-commercialization/opportunities*',
    ]) {
      await page.route(pattern, async (route: Route) => {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'stubbed opportunities error' }),
        });
      });
    }

    await page.goto(`${BASE_URL}/console/innovation-commercialization`);

    await expect(page.getByText('Failed to load Innovation / Commercialization runtime shell.')).toBeVisible({ timeout: 30_000 });
  });
});
