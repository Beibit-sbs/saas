from __future__ import annotations

from app.modules.platform_shared.notifications import InMemoryNotificationService, NotificationMessage

# ---------------------------------------------------------------------------
# Locale-aware notification templates (Arabic / GCC TIER-3 compliance)
# ---------------------------------------------------------------------------

_NOTIFICATION_TEMPLATES: dict[str, dict[str, tuple[str, str]]] = {
    # key: {locale: (subject, body)}
    "student_risk": {
        "en": ("Student risk detected", "New intervention case requires advisor review."),
        "ar": ("تم رصد مخاطر للطالب", "تتطلب حالة التدخل الجديدة مراجعة من المرشد الأكاديمي."),
    },
    "faculty_escalation": {
        "en": ("Critical student risk escalation", "Critical risk requires faculty follow-up."),
        "ar": ("تصعيد مخاطر حرجة للطالب", "تستلزم المخاطر الحرجة متابعة من عضو هيئة التدريس."),
    },
    "payment_recovery": {
        "en": ("Payment recovery action required", "Overdue payment risk detected; collections case created."),
        "ar": ("الإجراء المطلوب: استرداد الدفع", "تم رصد مخاطر دفع متأخرة؛ تم إنشاء قضية تحصيل."),
    },
    "budget_variance": {
        "en": ("Budget variance threshold reached", "Procurement review initiated for material budget variance."),
        "ar": ("تم الوصول إلى حد انحراف الميزانية", "بدأت مراجعة المشتريات بسبب انحراف الميزانية."),
    },
    "supply_risk": {
        "en": ("Supply risk detected", "Consumable stock is below threshold; replenishment started."),
        "ar": ("تم رصد مخاطر في الإمداد", "مخزون المواد الاستهلاكية أقل من الحد الأدنى؛ بدأت عملية التزويد."),
    },
    "accreditation_risk": {
        "en": ("Accreditation compliance risk detected", "Remediation workflow created for accreditation risk."),
        "ar": ("تم رصد مخاطر امتثال الاعتماد", "تم إنشاء سير عمل للمعالجة بسبب مخاطر الاعتماد."),
    },
    "platform_reliability": {
        "en": ("Platform reliability degradation detected", "Reliability incident workflow created."),
        "ar": ("تم رصد تدهور في موثوقية المنصة", "تم إنشاء سير عمل لحادثة الموثوقية."),
    },
    "research_risk": {
        "en": ("Research risk detected", "Research remediation workflow created."),
        "ar": ("تم رصد مخاطر في البحث العلمي", "تم إنشاء سير عمل لمعالجة مخاطر البحث العلمي."),
    },
    "campus_operations": {
        "en": ("Campus operations issue detected", "Campus operations workflow created."),
        "ar": ("تم رصد مشكلة في عمليات الحرم الجامعي", "تم إنشاء سير عمل لعمليات الحرم الجامعي."),
    },
    "student_life_risk": {
        "en": ("Student life risk detected", "Student support workflow created for wellbeing signal."),
        "ar": ("تم رصد مخاطر في حياة الطالب", "تم إنشاء سير عمل دعم الطالب لإشارة الرفاهية."),
    },
}


def get_notification_template(key: str, locale: str = "en") -> tuple[str, str]:
    """Return (subject, body) for *key* in *locale*, falling back to English."""
    templates = _NOTIFICATION_TEMPLATES.get(key, {})
    if locale in templates:
        return templates[locale]
    return templates.get("en", (key, key))


class NotificationActionDispatcher:
    def __init__(self, notification_service: InMemoryNotificationService | None = None) -> None:
        self._notifications = notification_service or InMemoryNotificationService()

    def notify_advisor(self, *, tenant_id: int, decision_id: str, payload: dict, locale: str = "en") -> dict:
        advisor_id = payload.get("advisor_id") or "advisor:unassigned"
        subject, body = get_notification_template("student_risk", locale)
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient=str(advisor_id),
                subject=subject,
                body=body,
                metadata={"decision_id": decision_id, "student_id": payload.get("student_id")},
            )
        )

    def notify_faculty(self, *, tenant_id: int, decision_id: str, payload: dict, locale: str = "en") -> dict:
        faculty_id = payload.get("faculty_id") or "faculty:unassigned"
        subject, body = get_notification_template("faculty_escalation", locale)
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient=str(faculty_id),
                subject=subject,
                body=body,
                metadata={"decision_id": decision_id, "student_id": payload.get("student_id")},
            )
        )

    def notify_finance(self, *, tenant_id: int, decision_id: str, payload: dict, locale: str = "en") -> dict:
        subject, body = get_notification_template("payment_recovery", locale)
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="finance:collections",
                subject=subject,
                body=body,
                metadata={"decision_id": decision_id, "student_id": payload.get("student_id")},
            )
        )

    def notify_procurement_team(self, *, tenant_id: int, decision_id: str, payload: dict, locale: str = "en") -> dict:
        subject, body = get_notification_template("budget_variance", locale)
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="procurement:office",
                subject=subject,
                body=body,
                metadata={
                    "decision_id": decision_id,
                    "budget_code": payload.get("budget_code"),
                    "vendor_code": payload.get("vendor_code"),
                    "contract_code": payload.get("contract_code"),
                },
            )
        )

    def notify_operations(self, *, tenant_id: int, decision_id: str, payload: dict, locale: str = "en") -> dict:
        subject, body = get_notification_template("supply_risk", locale)
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="operations:supply",
                subject=subject,
                body=body,
                metadata={"decision_id": decision_id, "stock_item_id": payload.get("stock_item_id")},
            )
        )

    def notify_compliance(self, *, tenant_id: int, decision_id: str, payload: dict, locale: str = "en") -> dict:
        subject, body = get_notification_template("accreditation_risk", locale)
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="compliance:office",
                subject=subject,
                body=body,
                metadata={
                    "decision_id": decision_id,
                    "accreditation_id": payload.get("accreditation_id"),
                    "new_status": payload.get("new_status"),
                },
            )
        )

    def notify_platform(self, *, tenant_id: int, decision_id: str, payload: dict, locale: str = "en") -> dict:
        subject, body = get_notification_template("platform_reliability", locale)
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="platform:reliability",
                subject=subject,
                body=body,
                metadata={
                    "decision_id": decision_id,
                    "workflow_name": payload.get("workflow_name"),
                    "integration_key": payload.get("integration_key"),
                    "severity": payload.get("severity"),
                },
            )
        )

    def notify_research_office(self, *, tenant_id: int, decision_id: str, payload: dict, locale: str = "en") -> dict:
        subject, body = get_notification_template("research_risk", locale)
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="research:office",
                subject=subject,
                body=body,
                metadata={
                    "decision_id": decision_id,
                    "grant_id": payload.get("grant_id"),
                    "publication_id": payload.get("publication_id"),
                    "research_project_id": payload.get("research_project_id"),
                },
            )
        )

    def notify_facilities_team(self, *, tenant_id: int, decision_id: str, payload: dict, locale: str = "en") -> dict:
        subject, body = get_notification_template("campus_operations", locale)
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="operations:facilities",
                subject=subject,
                body=body,
                metadata={
                    "decision_id": decision_id,
                    "facility_code": payload.get("facility_code"),
                    "room_code": payload.get("room_code"),
                    "severity": payload.get("severity"),
                },
            )
        )

    def notify_student_success_team(self, *, tenant_id: int, decision_id: str, payload: dict, locale: str = "en") -> dict:
        subject, body = get_notification_template("student_life_risk", locale)
        return self._notifications.send(
            NotificationMessage(
                tenant_id=int(tenant_id),
                channel="in_app",
                recipient="student_success:office",
                subject=subject,
                body=body,
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
