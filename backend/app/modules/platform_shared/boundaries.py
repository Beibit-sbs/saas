from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SharedServiceBoundary:
    key: str
    purpose: str
    tenant_scope: str
    actor_security_notes: str
    storage_model: str
    api_boundary: str
    extensibility_notes: str


SHARED_SERVICE_BOUNDARIES: tuple[SharedServiceBoundary, ...] = (
    SharedServiceBoundary(
        key="events",
        purpose="Tenant-aware domain event publication and dispatch",
        tenant_scope="tenant-aware with optional platform events",
        actor_security_notes="Propagate actor and correlation context; avoid secret payloads",
        storage_model="in-process now; outbox/broker-ready abstraction",
        api_boundary="internal publisher/dispatcher contract",
        extensibility_notes="Upgrade publisher to DB outbox and external broker without changing event contract",
    ),
    SharedServiceBoundary(
        key="notifications",
        purpose="Unified user/admin notification dispatch",
        tenant_scope="tenant-scoped templates and recipients",
        actor_security_notes="Separate user notifications and security/admin alerts",
        storage_model="provider-backed queue; template store per tenant",
        api_boundary="notification service contract",
        extensibility_notes="Email/in-app now; SMS/push channels later",
    ),
    SharedServiceBoundary(
        key="files",
        purpose="Tenant-scoped file/media metadata and access boundary",
        tenant_scope="strict tenant ownership",
        actor_security_notes="Path safety, content-type controls, authz checks and audit",
        storage_model="metadata table + pluggable object storage backend",
        api_boundary="file storage service contract",
        extensibility_notes="Local FS now, S3-compatible later",
    ),
    SharedServiceBoundary(
        key="search",
        purpose="Unified tenant-scoped search across modules",
        tenant_scope="tenant-scoped index/query",
        actor_security_notes="Apply module/entity filtering and authz before query return",
        storage_model="in-memory/DB index now; external search engine later",
        api_boundary="search index/query contract",
        extensibility_notes="Vector/AI knowledge search adapter later",
    ),
    SharedServiceBoundary(
        key="workflow",
        purpose="Reusable state-machine for approvals/tasks",
        tenant_scope="tenant workflow definitions and tasks",
        actor_security_notes="Actor-aware transitions with audit trail",
        storage_model="workflow definitions + tasks table",
        api_boundary="workflow transition contract",
        extensibility_notes="Config-driven definitions and SLA automation later",
    ),
    SharedServiceBoundary(
        key="webhooks",
        purpose="External event delivery with signature and retries",
        tenant_scope="tenant-owned subscriptions",
        actor_security_notes="Signed payloads, minimal data exposure, retry/DLQ visibility",
        storage_model="subscription table + delivery jobs/outbox",
        api_boundary="webhook subscription/signing contract",
        extensibility_notes="Provider-managed retries and replay APIs later",
    ),
    SharedServiceBoundary(
        key="entitlements",
        purpose="Module access model above plans/quotas/feature flags",
        tenant_scope="tenant-scoped entitlement snapshot",
        actor_security_notes="No implicit admin bypass; evaluate in tenant context",
        storage_model="derived snapshot + future explicit entitlement table",
        api_boundary="entitlement resolver contract",
        extensibility_notes="Marketplace/module-install entitlement grants later",
    ),
)
