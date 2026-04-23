from __future__ import annotations

from app.modules.platform_shared.notifications import InMemoryNotificationService, NotificationMessage


class NotificationActionDispatcher:
    def __init__(self, notification_service: InMemoryNotificationService | None = None) -> None:
        self._notifications = notification_service or InMemoryNotificationService()

    def notify_advisor(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        advisor_id = payload.get("advisor_id") or "advisor:unassigned"
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient=str(advisor_id),
                subject="Student risk detected",
                body="New intervention case requires advisor review.",
                metadata={"decision_id": decision_id, "student_id": payload.get("student_id")},
            )
        )

    def notify_faculty(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        faculty_id = payload.get("faculty_id") or "faculty:unassigned"
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient=str(faculty_id),
                subject="Critical student risk escalation",
                body="Critical risk requires faculty follow-up.",
                metadata={"decision_id": decision_id, "student_id": payload.get("student_id")},
            )
        )

    def notify_finance(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="finance:collections",
                subject="Payment recovery action required",
                body="Overdue payment risk detected; collections case created.",
                metadata={"decision_id": decision_id, "student_id": payload.get("student_id")},
            )
        )

    def notify_procurement_team(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="procurement:office",
                subject="Budget variance threshold reached",
                body="Procurement review has been initiated for a material budget variance.",
                metadata={
                    "decision_id": decision_id,
                    "budget_code": payload.get("budget_code"),
                    "vendor_code": payload.get("vendor_code"),
                    "contract_code": payload.get("contract_code"),
                },
            )
        )

    def notify_operations(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="operations:supply",
                subject="Supply risk detected",
                body="Consumable stock is below threshold; replenishment/procurement started.",
                metadata={"decision_id": decision_id, "stock_item_id": payload.get("stock_item_id")},
            )
        )

    def notify_compliance(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="compliance:office",
                subject="Accreditation compliance risk detected",
                body="Remediation workflow created for accreditation risk event.",
                metadata={
                    "decision_id": decision_id,
                    "accreditation_id": payload.get("accreditation_id"),
                    "new_status": payload.get("new_status"),
                },
            )
        )

    def notify_platform(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="platform:reliability",
                subject="Platform reliability degradation detected",
                body="Reliability incident workflow has been created for platform signal.",
                metadata={
                    "decision_id": decision_id,
                    "workflow_name": payload.get("workflow_name"),
                    "integration_key": payload.get("integration_key"),
                    "severity": payload.get("severity"),
                },
            )
        )

    def notify_research_office(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="research:office",
                subject="Research risk detected",
                body="Research remediation workflow has been created for a critical signal.",
                metadata={
                    "decision_id": decision_id,
                    "grant_id": payload.get("grant_id"),
                    "publication_id": payload.get("publication_id"),
                    "research_project_id": payload.get("research_project_id"),
                },
            )
        )

    def notify_facilities_team(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="operations:facilities",
                subject="Campus operations issue detected",
                body="A campus operations workflow has been created for a facility or cleaning incident.",
                metadata={
                    "decision_id": decision_id,
                    "facility_code": payload.get("facility_code"),
                    "room_code": payload.get("room_code"),
                    "severity": payload.get("severity"),
                },
            )
        )

    def notify_student_success_team(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="student_success:office",
                subject="Student life risk detected",
                body="Student support workflow created for wellbeing or disciplinary signal.",
                metadata={
                    "decision_id": decision_id,
                    "student_id": payload.get("student_id"),
                    "wellbeing_score": payload.get("wellbeing_score"),
                    "incident_severity": payload.get("incident_severity"),
                },
            )
        )

    def snapshot(self) -> list[dict[str, object]]:
        return self._notifications.snapshot()
