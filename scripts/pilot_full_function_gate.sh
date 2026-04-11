#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)

run_backend_checks() {
  "${COMPOSE[@]}" run --rm --no-deps backend-tests "$@"
}

PILOT_FRONTEND_TESTS=(
  "__tests__/admin/LocalUsersPage.test.tsx"
  "__tests__/admin/OpsConsolePage.test.tsx"
  "__tests__/admin/AutomationPages.test.tsx"
  "__tests__/admin/AutomationNewPage.test.tsx"
  "__tests__/admin/AutomationTemplatesPage.test.tsx"
  "__tests__/admin/AutomationRuleBuilder.test.tsx"
  "__tests__/admin/RectorDashboardPage.test.tsx"
  "__tests__/admin/AICopilotPage.test.tsx"
  "__tests__/admin/DeveloperAppsPage.test.tsx"
  "__tests__/admin/FederationPage.test.tsx"
  "__tests__/admin/TenantsPage.test.tsx"
  "__tests__/admin/FeatureFlagsPage.test.tsx"
  "__tests__/admin/WorkflowsPage.test.tsx"
  "__tests__/admin/PlatformControlPlanePage.test.tsx"
)

echo "[pilot-full-gate] starting full pilot functionality gate"
bash "${ROOT_DIR}/scripts/preflight_checks.sh"

echo "[pilot-full-gate] baseline pilot-safe gate"
bash "${ROOT_DIR}/scripts/university_pilot_safe_gate.sh"

pushd "${ROOT_DIR}/infra" >/dev/null
echo "[pilot-full-gate] ensuring core dependencies are available"
"${COMPOSE[@]}" up -d db redis

echo "[pilot-full-gate] platform backend capability suite"
run_backend_checks pytest -q --disable-warnings \
  tests/platform/test_platform_automation_workflow_engine_v1.py \
  tests/platform/test_platform_automation_templates.py \
  tests/platform/test_platform_webhooks_v1.py \
  tests/platform/test_platform_kpi_metrics_v1.py \
  tests/platform/test_platform_ai_copilot_foundation_v1.py \
  tests/platform/test_platform_developer_platform_v1.py \
  tests/platform/test_platform_federation_layer_v1.py

echo "[pilot-full-gate] tenant and rollout control suite"
run_backend_checks pytest -q --disable-warnings \
  tests/test_feature_flags_tenant_isolation.py \
  tests/test_local_users_tenant_isolation.py \
  tests/test_tenants.py \
  tests/test_jobs.py

echo "[pilot-full-gate] frontend pilot surfaces"
"${COMPOSE[@]}" run --rm frontend-tests npm run test:frontend -- "${PILOT_FRONTEND_TESTS[@]}"

popd >/dev/null

echo "[pilot-full-gate] operational smoke suite"
bash "${ROOT_DIR}/scripts/platform_smoke_check.sh"

echo "[pilot-full-gate] PASS: all pilot-visible functions are green"