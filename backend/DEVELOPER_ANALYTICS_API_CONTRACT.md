# Developer Analytics Events Contract (Minimal API v1)

Endpoint: `GET /api/dev/analytics/events`

Related analytics endpoints:
- `GET /api/dev/analytics/kpis/latest`
- `GET /api/dev/analytics/kpi`

Auth and scope:
- Requires `X-App-Key` and `X-App-Secret`
- Requires developer scope `analytics.read`
- Tenant is resolved from developer credentials only (no manual tenant override)
- Read surface is platform-managed entitlement gated (tenant capability gate via platform feature flags)
- Policy model is governed rollout (platform-managed, centralized):
  - `analytics/developer_read = true` -> allow
  - `analytics/developer_read = false` -> deny (`explicit_disabled`)
  - `analytics/developer_read` absent ->
    - allow for legacy-compatible tenants by default
    - deny when governed marker `analytics/developer_read_required = true` is set (`missing_entitlement_denied`)

Entitlement deny path (stable):
- When tenant entitlement for analytics read surface is disabled, endpoints return `403` with detail `analytics entitlement required`
- Deny path remains tenant-safe and does not leak plan internals
- Capability key: module `analytics`, key `developer_read`
- Governed strict marker: module `analytics`, key `developer_read_required`
- Platform-managed rollout write path for strict marker:
  - `PUT /api/v1/admin/tenants/{tenant_id}/features/analytics/developer_read_required`
  - payload: `{ "enabled": true|false }`
  - marker is managed through platform admin feature API (no ad hoc state mutation)
- Platform-managed rollout inspection read path:
  - `GET /api/v1/admin/tenants/{tenant_id}/analytics/entitlement-rollout-state`
  - admin/platform authorized and tenant-scoped
  - returns:
    - `marker_enabled` (`analytics/developer_read_required`, nullable)
    - `feature_enabled` (`analytics/developer_read`, nullable)
    - `effective_state`:
      - `legacy_compatible_allow`
      - `strict_required_missing`
      - `explicitly_enabled`
      - `explicitly_disabled`
    - `is_entitled` (effective allow/deny boolean)
- Platform rollout visibility summary path:
  - `GET /api/v1/admin/tenants/analytics/entitlement-rollout-summary?limit=<n>`
  - platform/admin authorized, bounded, and limited to canonical platform tenant context for cross-tenant visibility
  - returns compact per-tenant items with:
    - `tenant_id`
    - `marker_enabled`
    - `feature_enabled`
    - `effective_state`
    - `is_entitled`
  - effective states are computed by the same centralized policy helper used by per-tenant inspection and developer enforcement
  - this path is for platform rollout operations visibility, not for developer API consumption

Query parameters (bounded):
- `limit` (int): page size, clamped to `[1, 100]`, default `50`
- `ordering` (string): only `created_at_desc`
- `cursor` (string): opaque signed pagination token returned by API (`client-opaque`)
- `event_type` (string): exact event type filter
- `date_from` (date, YYYY-MM-DD): inclusive lower date bound
- `date_to` (date, YYYY-MM-DD): inclusive upper date bound

Date range guardrails:
- `date_from <= date_to`
- maximum range is 31 days

Validation and misuse handling (stable):
- invalid or tampered cursor -> `400 invalid cursor`
- unsupported ordering -> `422`
- invalid date range -> `422`
- oversize/undersize `limit` is clamped to bounded contract range `[1, 100]`
- authentication/scope failures remain enforced by developer auth dependency (`401/403`)
- entitlement failures are enforced by platform-managed analytics entitlement guard (`403`)

Response shape (stable):
- `tenant_id`
- `total` (number of items in current page)
- `limit`
- `ordering`
- `next_cursor` (string or null)
- `data_as_of` (timestamp or null): latest data timestamp represented by this response page
- `freshness_status` (`fresh` | `stale` | `empty`)
- `served_at` (timestamp): when API served this response
- `applied_filters`:
  - `event_type`
  - `date_from`
  - `date_to`
- `items` (analytics event projections)

KPI latest response additions (`GET /api/dev/analytics/kpis/latest`):
- `data_as_of` (timestamp): mirrors snapshot `updated_at`
- `freshness_status`:
  - `fresh` when `snapshot_date` is current UTC date
  - `stale` when latest snapshot date is older
- `served_at` (timestamp)

KPI dashboard response additions (`GET /api/dev/analytics/kpi`):
- `data_as_of` (timestamp or null): mirrors dashboard `generated_at`
- `freshness_status`:
  - `empty` when dashboard cards are empty
  - `fresh` when `snapshot_date` is current UTC date
  - `stale` otherwise
- `served_at` (timestamp)

Pagination semantics:
- Default order: newest first (`created_at desc, id desc`)
- `next_cursor` is an opaque token built from ordering/filter context and the last item anchor when page is full (`len(items) == limit`), otherwise `null`
- Cursor tokens are signed, tenant-scoped, and ordering/filter-specific; clients must treat them as opaque and must not construct or mutate them manually
- Empty page is returned as `items: []` with `next_cursor: null`

Observability:
- Analytics developer requests emit structured request logs on success/guarded/denied paths with tenant/app scope and bounded filter metadata (no sensitive payload logging)
- Contract misuse paths are observable via runtime counters (`developer_analytics_contract_total`) and security signals (`developer.analytics.contract_denied`)

Bounded metadata policy:
- Serving metadata is intentionally high-level and bounded.
- API exposes freshness/data-as-of signals without leaking internal storage layout, background worker internals, or implementation-specific table details.
