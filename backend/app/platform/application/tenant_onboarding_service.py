from __future__ import annotations

from typing import Any

from app.modules.audit.service import log_admin_action
from app.platform.idempotency.service import IdempotencyService
from app.platform.uow import UnitOfWork


class TenantOnboardingService:
    def __init__(self) -> None:
        self._idempotency = IdempotencyService()

    def onboard_tenant(
        self,
        *,
        slug: str,
        name: str,
        default_plan_code: str,
        actor: str,
        idempotency_key: str,
        fail_step: str | None = None,
    ) -> dict[str, Any]:
        request_payload = {
            "slug": slug,
            "name": name,
            "default_plan_code": default_plan_code,
            "actor": actor,
            "fail_step": fail_step,
        }

        def _execute(uow: UnitOfWork) -> dict[str, Any]:
            tenant = uow.tenant_repository.create_tenant(slug, name, conn=uow.conn)
            tenant_id = int(tenant["tenant_id"])
            if fail_step == "tenant_create":
                raise RuntimeError("injected tenant create failure")

            subscription = uow.billing_repository.assign_subscription(tenant_id, default_plan_code, conn=uow.conn)
            if fail_step == "subscription_assign":
                raise RuntimeError("injected subscription assignment failure")

            usage_metrics = ["workflow.executions", "api.requests", "notification.dispatch"]
            for metric in usage_metrics:
                uow.usage_repository.initialize(tenant_id, metric, conn=uow.conn)
            if fail_step == "usage_init":
                raise RuntimeError("injected usage init failure")

            default_features = [
                ("admissions", "core"),
                ("students", "core"),
                ("enrollments", "core"),
                ("grades", "core"),
                ("scheduling", "core"),
            ]
            features: list[dict[str, Any]] = []
            for module, key in default_features:
                item = uow.feature_flag_repository.set_flag(
                    scope="tenant",
                    tenant_id=tenant_id,
                    module=module,
                    key=key,
                    enabled=True,
                    conn=uow.conn,
                )
                features.append(item)
            if fail_step == "feature_flags":
                raise RuntimeError("injected feature flag setup failure")

            jobs: list[dict[str, Any]] = []
            jobs.append(
                uow.job_repository.enqueue(
                    tenant_id=tenant_id,
                    job_type="onboarding.bootstrap",
                    payload={"tenant_id": tenant_id},
                    max_retries=3,
                    conn=uow.conn,
                )
            )
            jobs.append(
                uow.job_repository.enqueue(
                    tenant_id=tenant_id,
                    job_type="onboarding.data_checks",
                    payload={"tenant_id": tenant_id},
                    max_retries=3,
                    conn=uow.conn,
                )
            )
            if fail_step == "jobs":
                raise RuntimeError("injected onboarding job scheduling failure")

            notification = uow.notification_repository.dispatch(
                tenant_id=tenant_id,
                channel="email",
                target="owner@example.com",
                subject="Tenant onboarding started",
                payload={"tenant_id": tenant_id, "slug": slug},
                conn=uow.conn,
            )
            uow.notification_repository.mark_status(
                int(notification["id"]),
                status="sent",
                last_error=None,
                increment_retry=False,
                conn=uow.conn,
            )
            if fail_step == "notification":
                raise RuntimeError("injected onboarding notification failure")

            log_admin_action(
                actor=actor,
                tenant_id=tenant_id,
                action="platform_core.tenant.onboarding",
                path="/api/v1/admin/tenants/onboarding",
                client_ip="application-service",
                correlation_id=None,
                entity="platform-core",
                result="success",
                metadata={"tenant_id": tenant_id, "plan_code": default_plan_code, "job_count": len(jobs)},
            )

            return {
                "tenant": tenant,
                "subscription": subscription,
                "usage_metrics_initialized": usage_metrics,
                "feature_flags": features,
                "jobs": jobs,
                "notification_id": int(notification["id"]),
            }

        result = self._idempotency.execute(
            tenant_id=1,
            key=idempotency_key,
            operation="tenant_onboarding",
            request_payload=request_payload,
            executor=_execute,
        )
        return {**result.response, "idempotent_replay": result.replayed}
