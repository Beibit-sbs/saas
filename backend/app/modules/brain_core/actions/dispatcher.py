from __future__ import annotations

from typing import Any, Callable

from app.modules.brain_core.actions.notification_actions import NotificationActionDispatcher
from app.modules.brain_core.actions.workflow_actions import InMemoryWorkflowActionDispatcher


class ActionDispatcher:
    """Dispatches action plan items to workflow/notification sinks."""

    _MAX_DISPATCH_ATTEMPTS = 3

    def __init__(
        self,
        *,
        on_workflow_case_outcome: Callable[[dict[str, Any], dict[str, Any], str], dict[str, Any]] | None = None,
    ) -> None:
        self._workflow = InMemoryWorkflowActionDispatcher()
        self._notifications = NotificationActionDispatcher()
        self._on_workflow_case_outcome = on_workflow_case_outcome

    def dispatch(self, *, tenant_id: int, decision_id: str, actions: list[dict]) -> list[dict]:
        results: list[dict] = []

        for action in actions:
            name = action.get("name")
            payload = dict(action.get("payload") or {})

            if name == "create_intervention_case":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._workflow.create_intervention_case(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "create_supervision_task":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._workflow.create_supervision_task(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "create_workload_review_task":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._workflow.create_workload_review_task(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "create_collections_case":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._workflow.create_collections_case(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "create_replenishment_task":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._workflow.create_replenishment_task(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "initiate_procurement_request":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._workflow.initiate_procurement_request(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "notify_procurement_team":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._notifications.notify_procurement_team(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "create_accreditation_remediation_workflow":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._workflow.create_accreditation_remediation_workflow(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "create_platform_reliability_incident":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._workflow.create_platform_reliability_incident(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "create_research_remediation_workflow":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._workflow.create_research_remediation_workflow(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "create_facility_incident_workflow":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._workflow.create_facility_incident_workflow(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "create_cleaning_recovery_task":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._workflow.create_cleaning_recovery_task(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "create_student_support_case":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._workflow.create_student_support_case(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "create_disciplinary_review_case":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._workflow.create_disciplinary_review_case(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "notify_advisor":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._notifications.notify_advisor(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "notify_faculty":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._notifications.notify_faculty(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "notify_finance":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._notifications.notify_finance(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "notify_operations":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._notifications.notify_operations(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "notify_compliance":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._notifications.notify_compliance(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "notify_platform":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._notifications.notify_platform(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "notify_research_office":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._notifications.notify_research_office(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "notify_facilities_team":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._notifications.notify_facilities_team(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            if name == "notify_student_success_team":
                results.append(
                    self._dispatch_with_retry(
                        action_name=name,
                        handler=lambda: self._notifications.notify_student_success_team(
                            tenant_id=tenant_id,
                            decision_id=decision_id,
                            payload=payload,
                        ),
                    )
                )
                continue

            results.append({"action": name, "status": "skipped", "reason": "unsupported_action"})

        return results

    def _dispatch_with_retry(self, *, action_name: str, handler: Callable[[], dict]) -> dict:
        last_error = "unknown_dispatch_error"
        for attempt in range(1, self._MAX_DISPATCH_ATTEMPTS + 1):
            try:
                return {
                    "action": action_name,
                    "attempts": attempt,
                    **handler(),
                }
            except Exception as exc:  # noqa: BLE001 - fail-safe dispatch path
                last_error = str(exc)

        return {
            "action": action_name,
            "status": "escalated",
            "reason": "dispatch_failed_after_retries",
            "attempts": self._MAX_DISPATCH_ATTEMPTS,
            "error": last_error,
        }

    def snapshot(self) -> dict:
        return {
            "workflow_cases": self._workflow.snapshot(),
            "notifications": self._notifications.snapshot(),
        }

    def record_workflow_case_outcome(self, *, case_id: str, payload: dict, actor: str) -> dict:
        case_result = self._workflow.record_case_outcome(case_id=case_id, payload=payload, actor=actor)
        if case_result.get("status") != "recorded" or self._on_workflow_case_outcome is None:
            return case_result

        case = case_result.get("item")
        if not isinstance(case, dict):
            return case_result

        feedback_result = self._on_workflow_case_outcome(case, dict(payload), actor)
        return {
            **case_result,
            **feedback_result,
            "case": case,
        }
