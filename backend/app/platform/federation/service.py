from __future__ import annotations

from typing import Any

from app.platform.federation.repository import FederationRepository
from app.platform.uow import UnitOfWork


_SHARED_FEDERATION_REPOSITORY = FederationRepository()


class FederationService:
    def __init__(self, repository: FederationRepository | None = None) -> None:
        self._repository = repository or _SHARED_FEDERATION_REPOSITORY

    def clear_state(self) -> None:
        self._repository.clear_state()

    # ------------------------------------------------------------------
    # Institutions
    # ------------------------------------------------------------------

    def create_institution(
        self,
        *,
        name: str,
        code: str,
        country: str,
        inst_type: str = "university",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with UnitOfWork() as uow:
            return self._repository.create_institution(
                name=name,
                code=code,
                country=country,
                inst_type=inst_type,
                metadata_json=metadata or {},
                conn=uow.conn,
            )

    def list_institutions(self) -> list[dict[str, Any]]:
        with UnitOfWork() as uow:
            return self._repository.list_institutions(conn=uow.conn)

    def get_institution(self, institution_id: int) -> dict[str, Any] | None:
        with UnitOfWork() as uow:
            return self._repository.get_institution(institution_id, conn=uow.conn)

    # ------------------------------------------------------------------
    # Tenant linking
    # ------------------------------------------------------------------

    def register_tenant_under_institution(
        self,
        *,
        institution_id: int,
        tenant_id: int,
        role: str = "institution_admin",
    ) -> dict[str, Any]:
        with UnitOfWork() as uow:
            institution = self._repository.get_institution(institution_id, conn=uow.conn)
            if institution is None:
                raise ValueError(f"Institution {institution_id} not found")
            return self._repository.link_tenant_to_institution(
                institution_id=institution_id,
                tenant_id=tenant_id,
                role=role,
                conn=uow.conn,
            )

    def list_institution_tenants(self, institution_id: int) -> list[dict[str, Any]]:
        with UnitOfWork() as uow:
            return self._repository.list_institution_tenants(institution_id, conn=uow.conn)

    # ------------------------------------------------------------------
    # Institution overview (cross-tenant analytics aggregation)
    # ------------------------------------------------------------------

    def list_institution_overview(self, institution_id: int) -> dict[str, Any]:
        with UnitOfWork() as uow:
            institution = self._repository.get_institution(institution_id, conn=uow.conn)
            if institution is None:
                raise ValueError(f"Institution {institution_id} not found")

            tenant_ids = self._repository.get_tenant_ids_for_institution(
                institution_id, conn=uow.conn
            )

            # Cross-tenant KPI aggregation
            students_total = 0
            enrollments_total = 0
            automation_failures_total = 0
            failed_jobs_total = 0

            for tid in tenant_ids:
                dashboard = _get_dashboard_safe(tid, uow)
                cards = list(dashboard.get("cards") or [])
                students_total += _card_value(cards, "total_students")
                enrollments_total += _card_value(cards, "total_enrollments")
                failed_jobs_total += _card_value(cards, "total_failed_jobs")

                # Automation health per tenant
                health = _get_automation_health_safe(tid, uow)
                automation_failures_total += int(health.get("failing_rules", 0))

            kpi_cards = [
                {"metric_key": "institution_students_total", "title": "Total Students", "value": students_total},
                {"metric_key": "institution_enrollments_total", "title": "Total Enrollments", "value": enrollments_total},
                {"metric_key": "institution_failed_jobs", "title": "Failed Jobs", "value": failed_jobs_total},
                {"metric_key": "institution_automation_failures", "title": "Automation Failures", "value": automation_failures_total},
            ]

            return {
                "institution": institution,
                "tenant_count": len(tenant_ids),
                "students_total": students_total,
                "enrollments_total": enrollments_total,
                "automation_health": {
                    "automation_failures_total": automation_failures_total,
                },
                "kpi_cards": kpi_cards,
            }


# ------------------------------------------------------------------
# Module-level singletons and convenience functions
# ------------------------------------------------------------------

federation_service = FederationService()


def create_institution(
    *,
    name: str,
    code: str,
    country: str,
    inst_type: str = "university",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return federation_service.create_institution(
        name=name, code=code, country=country, inst_type=inst_type, metadata=metadata
    )


def list_institutions() -> list[dict[str, Any]]:
    return federation_service.list_institutions()


def get_institution(institution_id: int) -> dict[str, Any] | None:
    return federation_service.get_institution(institution_id)


def register_tenant_under_institution(
    *,
    institution_id: int,
    tenant_id: int,
    role: str = "institution_admin",
) -> dict[str, Any]:
    return federation_service.register_tenant_under_institution(
        institution_id=institution_id, tenant_id=tenant_id, role=role
    )


def list_institution_tenants(institution_id: int) -> list[dict[str, Any]]:
    return federation_service.list_institution_tenants(institution_id)


def list_institution_overview(institution_id: int) -> dict[str, Any]:
    return federation_service.list_institution_overview(institution_id)


def clear_federation_state() -> None:
    federation_service.clear_state()


# ------------------------------------------------------------------
# Aggregation helpers (safe wrappers that never raise)
# ------------------------------------------------------------------

def _get_dashboard_safe(tenant_id: int, uow: UnitOfWork) -> dict[str, Any]:
    try:
        from app.platform.kpi import service as kpi_service
        return kpi_service.get_rector_dashboard(tenant_id=tenant_id, uow=uow)
    except Exception:  # pragma: no cover
        return {"cards": []}


def _get_automation_health_safe(tenant_id: int, uow: UnitOfWork) -> dict[str, Any]:
    try:
        from app.platform.automation import service as automation_service
        rules = automation_service.list_rules(tenant_id=tenant_id, uow=uow)
        failing = sum(1 for r in rules if r.get("status") in ("failing", "degraded"))
        return {"failing_rules": failing, "total_rules": len(rules)}
    except Exception:  # pragma: no cover
        return {"failing_rules": 0, "total_rules": 0}


def _card_value(cards: list[dict[str, Any]], metric_key: str) -> int:
    for card in cards:
        if str(card.get("metric_key")) == metric_key:
            return int(card.get("value") or 0)
    return 0
