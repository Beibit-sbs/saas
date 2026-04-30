from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import logging
import time
import uuid
from typing import Callable
from uuid import uuid4

from app.core.db import _get_shared_engine, make_session_factory
from app.platform.ai import llm_bridge
from app.modules.brain_core.actions.dispatcher import ActionDispatcher
from app.modules.brain_core.actions.planner import ActionPlanner
from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
from app.modules.brain_core.context_builder import ContextBuilder
from app.modules.brain_core.feedback.outcome_tracker import OutcomeTracker
from app.modules.brain_core.learning.policy_tuning import PolicyTuningEngine
from app.modules.brain_core.learning.quality_tracking import DecisionQualityTracker
from app.modules.brain_core.observability import BrainCoreObservability
from app.modules.brain_core.policy.decision_policy import DecisionPolicyGuard
from app.modules.brain_core.policy.tenant_policy import TenantPolicyProfile, TenantPolicyResolver
from app.modules.brain_core.reasoning.anomaly_detector import AnomalyDetector
from app.modules.brain_core.reasoning.explanation import ExplanationEngine
from app.modules.brain_core.reasoning.engine import ReasoningEngine
from app.modules.brain_core.reasoning.knowledge_retriever import KnowledgeRetriever
from app.modules.brain_core.reasoning.predictor import PredictiveRiskEngine
from app.modules.brain_core.registry import SignalRegistry
from app.modules.observability.metrics import (
    record_brain_action_dispatched,
    record_brain_decision_made,
    record_brain_signal_emitted,
)


logger = logging.getLogger(__name__)


def _coerce_uuid(value: object) -> uuid.UUID:
    """Convert a string/UUID to uuid.UUID, generating a new one on failure."""
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError):
        return uuid4()


def _compute_dedup_key(event_type: str, tenant_id: int, source_entity_type: str, source_entity_id: str) -> str:
    """Return a 64-char hex digest used to deduplicate identical signals."""
    raw = f"{event_type}|{tenant_id}|{source_entity_type}|{source_entity_id}"
    return hashlib.sha256(raw.encode()).hexdigest()


class BrainCoreService:
    """Scenario pipeline for Brain Core v1 (Student Risk first)."""

    def __init__(self) -> None:
        self._context_builder = ContextBuilder()
        self._classifier = RiskClassifier()
        self._reasoning = ReasoningEngine()
        self._planner = ActionPlanner()
        self._outcome_tracker = OutcomeTracker()
        self._quality_tracker = DecisionQualityTracker()
        self._policy_tuning = PolicyTuningEngine()
        self._observability = BrainCoreObservability()
        self._policy_guard = DecisionPolicyGuard()
        self._policy_resolver = TenantPolicyResolver()
        self._anomaly_detector = AnomalyDetector()
        self._explanation = ExplanationEngine()
        self._knowledge = KnowledgeRetriever()
        self._predictor = PredictiveRiskEngine()
        self._dispatcher = ActionDispatcher(on_workflow_case_outcome=self._record_case_feedback)
        self._signals: list[dict] = []
        self._decisions: list[dict] = []
        self._explanations: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # DB persistence helpers (fire-and-forget; degrade gracefully)
    # ------------------------------------------------------------------

    def _check_duplicate_signal(
        self,
        *,
        tenant_id: int,
        dedup_key: str,
        window_seconds: int = 60,
    ) -> uuid.UUID | None:
        """Return existing signal_id if an identical signal was received within the window; None otherwise."""
        from sqlalchemy import text as sa_text  # local import to avoid circular

        engine = _get_shared_engine()
        if engine is None:
            return None
        try:
            session_factory = make_session_factory(engine)
            with session_factory() as session:
                row = session.execute(
                    sa_text(
                        "SELECT signal_id FROM app_brain_signals"
                        " WHERE tenant_id = :tid AND dedup_key = :key"
                        f"   AND created_at > NOW() - INTERVAL '{window_seconds} seconds'"
                        " LIMIT 1"
                    ).bindparams(tid=tenant_id, key=dedup_key)
                ).fetchone()
                return uuid.UUID(str(row[0])) if row else None
        except Exception:  # noqa: BLE001
            return None

    def _try_persist_signal_to_db(
        self,
        *,
        signal_id: uuid.UUID,
        signal: dict,
        tenant_id: int,
        event_type: str,
        signal_class: str,
        dedup_key: str | None = None,
    ) -> None:
        """Write a row to app_brain_signals; silently skip if DB is unavailable."""
        from app.modules.brain_core.models import BrainSignalModel  # local to avoid circular import

        engine = _get_shared_engine()
        if engine is None:
            return
        session_factory = make_session_factory(engine)
        with session_factory() as session:
            try:
                row = BrainSignalModel(
                    signal_id=signal_id,
                    tenant_id=tenant_id,
                    correlation_id=_coerce_uuid(signal.get("correlation_id")),
                    event_type=event_type,
                    signal_class=signal_class,
                    source_module=str(signal.get("source_module") or event_type.split(".")[0]),
                    source_entity_type=str(signal.get("source_entity_type") or ""),
                    source_entity_id=str(signal.get("source_entity_id") or ""),
                    subject_student_id=signal.get("student_id") or signal.get("subject_student_id") or None,
                    subject_faculty_id=signal.get("subject_faculty_id") or None,
                    subject_course_id=signal.get("subject_course_id") or None,
                    payload=dict(signal.get("payload") or {}),
                    status="received",
                    dedup_key=dedup_key,
                )
                session.add(row)
                session.commit()
            except Exception:  # noqa: BLE001
                logger.warning("brain_core_signal_persist_failed", exc_info=True)
                session.rollback()

    # Priorities and types that warrant an immediate in-app notification.
    _NOTIFIABLE_PRIORITIES: frozenset[str] = frozenset({"critical", "high"})
    _NOTIFIABLE_DECISION_TYPES: frozenset[str] = frozenset({"risk", "preventive", "compliance"})

    def _ensure_intervention_action_for_intervention_decisions(
        self,
        *,
        decision_type: str,
        action_plan: list[dict],
        signal: dict,
        requires_approval: bool,
    ) -> list[dict]:
        """Enforce intervention side-effect contract for intervention decisions.

        If reasoning marks a decision as "intervention", we ensure the action plan
        contains create_intervention_case so the dispatcher can persist a real case.
        """
        if str(decision_type).lower() != "intervention":
            return action_plan

        has_intervention_action = any(
            str(item.get("name") or "") == "create_intervention_case"
            for item in action_plan
        )
        if has_intervention_action:
            return action_plan

        payload = dict(signal.get("payload") or {})
        subject = dict(signal.get("subject") or {})
        merged_payload = {
            **payload,
            "student_id": payload.get("student_id") or subject.get("student_id") or signal.get("student_id"),
            "event_type": str(signal.get("event_type") or ""),
            "source_entity_type": str(signal.get("source_entity_type") or ""),
            "source_entity_id": str(signal.get("source_entity_id") or ""),
        }
        return [
            *action_plan,
            {
                "name": "create_intervention_case",
                "action_type": "workflow_task",
                "requires_approval": bool(requires_approval),
                "payload": merged_payload,
            },
        ]

    def _emit_decision_notification(self, *, decision: dict, signal: dict) -> dict | None:
        """Create an in-app notification for high/critical Brain decisions.

        Returns the notification row on success, None if skipped or on error.
        """
        priority = str(decision.get("priority") or "").lower()
        decision_type = str(decision.get("decision_type") or "").lower()
        tenant_id = int(decision.get("tenant_id") or 0)

        if priority not in self._NOTIFIABLE_PRIORITIES:
            return None
        if decision_type not in self._NOTIFIABLE_DECISION_TYPES:
            return None
        if tenant_id <= 0:
            return None

        situation_type = str(decision.get("situation_type") or "unknown")
        subject = f"Brain Decision [{priority.upper()}]: {situation_type.replace('_', ' ').title()}"

        recipient = (
            str(signal.get("recipient") or "").strip()
            or str(signal.get("supervisor_contact") or "").strip()
            or f"tenant:{tenant_id}:admin"
        )

        payload: dict = {
            "decision_id": str(decision.get("decision_id") or ""),
            "decision_type": decision_type,
            "situation_type": situation_type,
            "priority": priority,
            "recommended_actions": list(decision.get("recommended_actions") or []),
            "source_event_type": str(signal.get("event_type") or ""),
        }

        try:
            from app.platform.repository.notification_repository import NotificationRepository  # local to avoid circular

            repo = NotificationRepository()
            result = repo.dispatch(
                tenant_id=tenant_id,
                channel="in_app",
                target=recipient,
                subject=subject,
                payload=payload,
            )
            self._observability.increment("decision_notifications_emitted_total")
            logger.info(
                "brain_core_decision_notification_emitted",
                extra={
                    "tenant_id": tenant_id,
                    "decision_id": str(decision.get("decision_id") or ""),
                    "priority": priority,
                    "notification_id": result.get("id"),
                },
            )
            return result
        except Exception:  # noqa: BLE001
            logger.warning("brain_core_decision_notification_failed", exc_info=True)
            return None

    def _try_persist_decision_to_db(
        self,
        *,
        signal_id: uuid.UUID,
        decision: dict,
    ) -> None:
        """Write a row to app_brain_decisions; silently skip if DB is unavailable."""
        from app.modules.brain_core.models import BrainDecisionModel  # local to avoid circular import

        engine = _get_shared_engine()
        if engine is None:
            return
        session_factory = make_session_factory(engine)
        with session_factory() as session:
            try:
                row = BrainDecisionModel(
                    decision_id=_coerce_uuid(decision["decision_id"]),
                    tenant_id=int(decision["tenant_id"]),
                    signal_id=signal_id,
                    correlation_id=_coerce_uuid(decision.get("correlation_id")),
                    decision_type=str(decision["decision_type"]),
                    situation_type=str(decision["situation_type"]),
                    priority=str(decision["priority"]),
                    status=str(decision["status"]),
                    confidence_score=float(decision.get("confidence_score") or 0.0),
                    severity_score=float(decision.get("severity_score") or 0.0),
                    urgency_score=float(decision.get("urgency_score") or 0.0),
                    requires_approval=bool(decision.get("requires_approval", False)),
                    policy_snapshot={},
                )
                session.add(row)
                session.commit()
            except Exception:  # noqa: BLE001
                logger.warning("brain_core_decision_persist_failed", exc_info=True)
                session.rollback()

    def process_signal(self, signal: dict) -> dict:
        started = time.perf_counter()
        self._observability.increment("signals_received_total")

        event_type = str(signal.get("event_type") or "")
        if not SignalRegistry.is_supported(event_type):
            self._observability.increment("signals_ignored_total")
            return {
                "status": "ignored",
                "reason": "unsupported_event_type",
                "event_type": event_type,
            }

        tenant_id = int(signal.get("tenant_id") or 0)
        if tenant_id <= 0:
            self._observability.increment("signals_rejected_total")
            return {"status": "rejected", "reason": "missing_tenant_context"}

        source_entity_type = str(signal.get("source_entity_type") or "")
        source_entity_id = str(signal.get("source_entity_id") or "")
        dedup_key = _compute_dedup_key(event_type, tenant_id, source_entity_type, source_entity_id)
        existing_id = self._check_duplicate_signal(tenant_id=tenant_id, dedup_key=dedup_key)
        if existing_id is not None:
            self._observability.increment("signals_deduplicated_total")
            return {
                "status": "deduplicated",
                "reason": "duplicate_signal_within_window",
                "original_signal_id": str(existing_id),
            }

        signal_id = uuid4()
        signal.setdefault("signal_id", str(signal_id))
        self._signals.append(signal)

        context_started = time.perf_counter()
        context = self._context_builder.build_context(signal)
        self._observability.record_latency_ms("context_build_latency_ms", (time.perf_counter() - context_started) * 1000.0)
        classification = self._classifier.classify(signal, context)
        self._try_persist_signal_to_db(
            signal_id=signal_id,
            signal=signal,
            tenant_id=tenant_id,
            event_type=event_type,
            signal_class=str(classification.get("situation_type") or "unknown"),
            dedup_key=dedup_key,
        )
        knowledge = self._knowledge.retrieve(signal=signal, classification=classification)
        context["knowledge"] = knowledge
        policy_profile = self._policy_resolver.get_profile(tenant_id)
        reasoning = self._reasoning.decide(
            classification,
            context,
            knowledge=knowledge,
            enable_ai_reasoning=bool(policy_profile.enable_ai_reasoning),
        )

        decision_id = str(uuid4())
        scenario = SignalRegistry.signals[event_type]["scenario"]
        action_plan = self._planner.build_plan(
            decision_scenario=scenario,
            reasoning=reasoning,
            signal=signal,
        )
        action_plan = self._ensure_intervention_action_for_intervention_decisions(
            decision_type=str(reasoning.get("decision_type") or ""),
            action_plan=action_plan,
            signal=signal,
            requires_approval=bool(reasoning.get("requires_approval", False)),
        )
        policy_validation = self._policy_guard.validate(
            tenant_id=tenant_id,
            decision_type=reasoning["decision_type"],
            priority=reasoning["priority"],
            profile=policy_profile,
        )

        decision_status = "approval_pending" if policy_validation.requires_approval else "dispatched"
        dispatch_results: list[dict] = []
        if policy_validation.approved and not policy_validation.requires_approval:
            dispatch_results = self._dispatcher.dispatch(
                tenant_id=tenant_id,
                decision_id=decision_id,
                actions=action_plan,
            )
            has_dispatch_failure = any(
                str(item.get("status")) in {"failed", "escalated"}
                for item in dispatch_results
            )
            if has_dispatch_failure:
                self._observability.increment("action_dispatch_failure_total")
                record_brain_action_dispatched(tenant_id, "failure")
            else:
                self._observability.increment("action_dispatch_success_total")
                record_brain_action_dispatched(tenant_id, "success")
        elif policy_validation.requires_approval:
            self._observability.increment("decisions_requiring_approval_total")
        else:
            self._observability.increment("action_dispatch_failure_total")
            record_brain_action_dispatched(tenant_id, "failure")

        explanation = self._explanation.build(
            signal=signal,
            context=context,
            classification=classification,
            reasoning=reasoning,
            knowledge=knowledge,
            policy_reason=policy_validation.reason,
            approval_role=policy_validation.approval_role,
        )

        decision = {
            "decision_id": decision_id,
            "tenant_id": tenant_id,
            "correlation_id": signal.get("correlation_id") or str(uuid4()),
            "decision_type": reasoning["decision_type"],
            "situation_type": classification["situation_type"],
            "priority": reasoning["priority"],
            "status": decision_status,
            "recommended_actions": reasoning["recommended_actions"],
            "requires_approval": bool(reasoning["requires_approval"] or policy_validation.requires_approval),
            "confidence_score": reasoning["confidence_score"],
            "severity_score": reasoning["severity_score"],
            "urgency_score": reasoning["urgency_score"],
            "approval_role": policy_validation.approval_role,
            "policy_reason": policy_validation.reason,
            "action_plan": action_plan,
            "dispatch_results": dispatch_results,
            "explanation": explanation,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ai_reasoning_enabled": bool(reasoning.get("ai_reasoning_enabled")),
            "ai_reasoning_trace": list(reasoning.get("ai_reasoning_trace") or []),
        }
        self._decisions.append(decision)
        self._try_persist_decision_to_db(signal_id=signal_id, decision=decision)
        self._emit_decision_notification(decision=decision, signal=signal)
        self._explanations[decision_id] = explanation
        self._observability.increment("decisions_created_total")
        self._observability.increment(f"decisions_by_type_{reasoning['decision_type']}_total")
        self._observability.increment(f"decisions_by_priority_{reasoning['priority']}_total")
        record_brain_signal_emitted(tenant_id)
        record_brain_decision_made(tenant_id, reasoning["decision_type"])
        self._observability.record_trace(
            tenant_id=tenant_id,
            correlation_id=str(decision["correlation_id"]),
            signal_id=str(signal.get("signal_id") or ""),
            decision_id=decision_id,
        )
        self._observability.record_latency_ms("reasoning_latency_ms", (time.perf_counter() - started) * 1000.0)

        logger.info(
            "brain_core_decision_created",
            extra={
                "tenant_id": tenant_id,
                "correlation_id": decision["correlation_id"],
                "signal_id": signal.get("signal_id"),
                "decision_id": decision_id,
                "priority": decision["priority"],
                "status": decision["status"],
            },
        )

        return {
            "status": "processed",
            "signal": signal,
            "context": context,
            "classification": classification,
            "decision": decision,
            "action_plan": action_plan,
            "dispatch_results": dispatch_results,
        }

    def get_decision(self, decision_id: str) -> dict | None:
        for decision in self._decisions:
            if decision.get("decision_id") == decision_id:
                return decision
        return None

    def simulate_what_if(
        self,
        *,
        signal: dict,
        forecast_horizon_days: int = 30,
        simulation_label: str | None = None,
        policy_override: dict | None = None,
    ) -> dict:
        event_type = str(signal.get("event_type") or "")
        if not SignalRegistry.is_supported(event_type):
            return {
                "status": "ignored",
                "reason": "unsupported_event_type",
                "event_type": event_type,
            }

        tenant_id = int(signal.get("tenant_id") or 0)
        if tenant_id <= 0:
            return {"status": "rejected", "reason": "missing_tenant_context"}

        context = self._context_builder.build_context(signal)
        classification = self._classifier.classify(signal, context)
        knowledge = self._knowledge.retrieve(signal=signal, classification=classification)
        context["knowledge"] = knowledge
        if policy_override:
            profile = TenantPolicyProfile(
                tenant_id=tenant_id,
                autonomy_level=max(0, min(4, int(policy_override.get("autonomy_level", 2)))),
                require_approval_for_critical=bool(policy_override.get("require_approval_for_critical", True)),
                default_approval_role=str(policy_override.get("default_approval_role") or "dean_office"),
                enable_ai_reasoning=bool(policy_override.get("enable_ai_reasoning", False)),
            )
        else:
            profile = self._policy_resolver.get_profile(tenant_id)

        reasoning = self._reasoning.decide(
            classification,
            context,
            knowledge=knowledge,
            enable_ai_reasoning=bool(profile.enable_ai_reasoning),
        )
        scenario = SignalRegistry.signals[event_type]["scenario"]
        action_plan = self._planner.build_plan(
            decision_scenario=scenario,
            reasoning=reasoning,
            signal=signal,
        )
        policy_validation = self._policy_guard.validate(
            tenant_id=tenant_id,
            decision_type=reasoning["decision_type"],
            priority=reasoning["priority"],
            profile=profile,
        )
        explanation = self._explanation.build(
            signal=signal,
            context=context,
            classification=classification,
            reasoning=reasoning,
            knowledge=knowledge,
            policy_reason=policy_validation.reason,
            approval_role=policy_validation.approval_role,
        )
        explanation["summary"] = f"What-if simulation: {explanation['summary']}"
        explanation["expected_outcome"] = (
            f"Forecast over {forecast_horizon_days} day(s); no actions dispatched, preview only."
        )

        decision = {
            "decision_id": str(uuid4()),
            "tenant_id": tenant_id,
            "correlation_id": signal.get("correlation_id") or str(uuid4()),
            "decision_type": reasoning["decision_type"],
            "situation_type": classification["situation_type"],
            "priority": reasoning["priority"],
            "status": "simulated",
            "recommended_actions": reasoning["recommended_actions"],
            "requires_approval": bool(reasoning["requires_approval"] or policy_validation.requires_approval),
            "confidence_score": reasoning["confidence_score"],
            "severity_score": reasoning["severity_score"],
            "urgency_score": reasoning["urgency_score"],
            "approval_role": policy_validation.approval_role,
            "policy_reason": policy_validation.reason,
            "action_plan": action_plan,
            "dispatch_results": [],
            "explanation": explanation,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ai_reasoning_enabled": bool(reasoning.get("ai_reasoning_enabled")),
            "ai_reasoning_trace": list(reasoning.get("ai_reasoning_trace") or []),
        }
        forecast = {
            "horizon_days": max(1, int(forecast_horizon_days)),
            "dispatchable_now": bool(policy_validation.approved and not policy_validation.requires_approval),
            "approval_required": bool(policy_validation.requires_approval),
            "expected_action_count": len(action_plan),
            "projected_priority": reasoning["priority"],
            "simulation_label": simulation_label,
        }
        self._observability.increment("what_if_simulations_total")
        return {
            "status": "simulated",
            "signal": signal,
            "context": context,
            "classification": classification,
            "decision": decision,
            "action_plan": action_plan,
            "dispatch_results": [],
            "forecast": forecast,
        }

    def approve_decision(self, decision_id: str, *, actor: str = "system") -> dict:
        decision = self.get_decision(decision_id)
        if decision is None:
            return {"status": "not_found", "decision_id": decision_id}

        if decision.get("status") != "approval_pending":
            return {
                "status": "ignored",
                "decision_id": decision_id,
                "reason": "decision_not_pending_approval",
            }

        dispatch_results = self._dispatcher.dispatch(
            tenant_id=int(decision["tenant_id"]),
            decision_id=decision_id,
            actions=list(decision.get("action_plan") or []),
        )
        self._observability.increment("action_dispatch_success_total")
        decision["status"] = "dispatched"
        decision["approved_by"] = actor
        decision["approved_at"] = datetime.now(timezone.utc).isoformat()
        decision["dispatch_results"] = dispatch_results

        return {
            "status": "approved",
            "decision": decision,
            "dispatch_results": dispatch_results,
        }

    def reprocess_signal(self, signal_id: str, *, actor: str = "system") -> dict:
        signal = next((s for s in self._signals if s.get("signal_id") == signal_id), None)
        if signal is None:
            return {"status": "not_found", "signal_id": signal_id}
        logger.info("brain_core.reprocess_signal signal_id=%s actor=%s", signal_id, actor)
        result = self.process_signal(dict(signal))
        result["reprocessed_by"] = actor
        result["original_signal_id"] = signal_id
        return result

    def cancel_decision(self, decision_id: str, *, actor: str = "system", reason: str = "cancelled_by_operator") -> dict:
        decision = self.get_decision(decision_id)
        if decision is None:
            return {"status": "not_found", "decision_id": decision_id}

        if decision.get("status") in {"completed", "cancelled"}:
            return {
                "status": "ignored",
                "decision_id": decision_id,
                "reason": "decision_already_closed",
            }

        decision["status"] = "cancelled"
        decision["cancelled_by"] = actor
        decision["cancelled_at"] = datetime.now(timezone.utc).isoformat()
        decision["cancel_reason"] = reason
        return {"status": "cancelled", "decision": decision}

    def list_signals(self) -> list[dict]:
        return list(self._signals)

    def list_decisions(self) -> list[dict]:
        return list(self._decisions)

    def dispatch_snapshot(self) -> dict:
        return self._dispatcher.snapshot()

    def get_explanation(self, decision_id: str) -> dict | None:
        return self._explanations.get(decision_id)

    def record_outcome(self, decision_id: str, *, payload: dict, actor: str = "system") -> dict:
        decision = self.get_decision(decision_id)
        if decision is None:
            return {"status": "not_found", "decision_id": decision_id}

        outcome = self._outcome_tracker.record(
            decision_id=decision_id,
            tenant_id=int(decision["tenant_id"]),
            payload=payload,
        )
        observation = self._quality_tracker.record(decision=decision, outcome=outcome)
        policy_tuning = self.policy_tuning_suggestion(int(decision["tenant_id"]))
        self._observability.increment("outcome_recorded_total")
        if outcome.get("effectiveness") == "negative":
            self._observability.increment("false_positive_total")
        decision["status"] = "completed"
        decision["completed_by"] = actor
        decision["outcome_id"] = outcome["outcome_id"]

        return {
            "status": "recorded",
            "decision": decision,
            "outcome": outcome,
            "observation": observation,
            "policy_tuning": policy_tuning,
        }

    def record_dispatch_outcome(self, case_id: str, *, payload: dict, actor: str = "system") -> dict:
        result = self._dispatcher.record_workflow_case_outcome(
            case_id=case_id,
            payload=payload,
            actor=actor,
        )
        if result.get("status") == "not_found":
            return {"status": "not_found", "case_id": case_id}
        return result

    def _record_case_feedback(self, case: dict, payload: dict, actor: str) -> dict:
        decision_id = str(case.get("decision_id") or "").strip()
        if not decision_id:
            return {
                "status": "invalid_dispatch_item",
                "case_id": str(case.get("case_id") or ""),
                "reason": "missing_decision_id",
                "item": case,
            }

        return self.record_outcome(decision_id, payload=payload, actor=actor)

    def list_outcomes(self) -> list[dict]:
        return self._outcome_tracker.list_outcomes()

    def learning_metrics(self) -> dict:
        return self._quality_tracker.metrics()

    def policy_profile(self, tenant_id: int) -> dict:
        return self._policy_resolver.profile_dict(tenant_id)

    def update_policy_profile(
        self,
        tenant_id: int,
        *,
        autonomy_level: int,
        require_approval_for_critical: bool,
        default_approval_role: str,
        enable_ai_reasoning: bool,
        actor: str = "admin@brain",
    ) -> dict:
        profile = self._policy_resolver.set_profile_values(
            tenant_id=tenant_id,
            autonomy_level=autonomy_level,
            require_approval_for_critical=require_approval_for_critical,
            default_approval_role=default_approval_role,
            enable_ai_reasoning=enable_ai_reasoning,
        )
        logger.info(
            "brain_core.policy_updated tenant_id=%s autonomy_level=%s ai_reasoning=%s actor=%s",
            tenant_id,
            autonomy_level,
            enable_ai_reasoning,
            actor,
        )
        return {
            "status": "updated",
            "updated_by": actor,
            "tenant_id": profile.tenant_id,
            "profile": {
                "tenant_id": profile.tenant_id,
                "autonomy_level": profile.autonomy_level,
                "require_approval_for_critical": profile.require_approval_for_critical,
                "default_approval_role": profile.default_approval_role,
                "enable_ai_reasoning": profile.enable_ai_reasoning,
            },
        }

    def policy_tuning_suggestion(self, tenant_id: int) -> dict:
        profile = self._policy_resolver.get_profile(tenant_id)
        metrics = self._quality_tracker.metrics_for_tenant(tenant_id)
        return self._policy_tuning.suggest(profile=profile, metrics=metrics)

    def apply_policy_tuning(self, tenant_id: int, *, actor: str = "system") -> dict:
        suggestion = self.policy_tuning_suggestion(tenant_id)
        suggested = suggestion["suggested_profile"]
        profile = self._policy_resolver.set_profile_values(
            tenant_id=tenant_id,
            autonomy_level=int(suggested["autonomy_level"]),
            require_approval_for_critical=bool(suggested["require_approval_for_critical"]),
            default_approval_role=str(suggested["default_approval_role"]),
            enable_ai_reasoning=bool(suggested.get("enable_ai_reasoning", False)),
        )
        return {
            "status": "applied",
            "applied_by": actor,
            "tenant_id": tenant_id,
            "changed": bool(suggestion.get("changed")),
            "reason": suggestion.get("reason"),
            "profile": {
                "tenant_id": profile.tenant_id,
                "autonomy_level": profile.autonomy_level,
                "require_approval_for_critical": profile.require_approval_for_critical,
                "default_approval_role": profile.default_approval_role,
                "enable_ai_reasoning": profile.enable_ai_reasoning,
            },
        }

    def observability_metrics(self) -> dict:
        return self._observability.snapshot_metrics()

    def observability_traces(self, limit: int = 100) -> list[dict]:
        return self._observability.snapshot_traces(limit=limit)

    # ------------------------------------------------------------------
    # Blocker #12: startup policy seeding
    # ------------------------------------------------------------------

    def seed_default_policies(
        self,
        tenant_ids: list[int],
        *,
        autonomy_level: int = 3,
        require_approval_for_critical: bool = True,
        default_approval_role: str = "dean_office",
        enable_ai_reasoning: bool = False,
    ) -> dict:
        """Seed sensible default policy profiles for a list of tenants.

        Skips tenants whose profiles have already been explicitly configured so
        that a hot-restart does not overwrite operator-tuned settings.

        Returns a summary dict for observability.
        """
        seeded: list[int] = []
        skipped: list[int] = []
        for tid in tenant_ids:
            existing = self._policy_resolver.get_profile(tid)
            # Only seed if the profile is still the programmatic default
            # (i.e. the operator has not explicitly updated it).
            if self._policy_resolver.is_default(tid):
                self._policy_resolver.set_profile_values(
                    tenant_id=tid,
                    autonomy_level=autonomy_level,
                    require_approval_for_critical=require_approval_for_critical,
                    default_approval_role=default_approval_role,
                    enable_ai_reasoning=enable_ai_reasoning,
                )
                logger.info(
                    "brain_core.policy_seeded tenant_id=%s autonomy_level=%s",
                    tid,
                    autonomy_level,
                )
                seeded.append(tid)
            else:
                skipped.append(tid)
                _ = existing  # referenced to satisfy linters
        return {"seeded": seeded, "skipped": skipped}

    # ------------------------------------------------------------------
    # Blocker #13: module action callback registration
    # ------------------------------------------------------------------

    def register_module_action_handler(
        self,
        action_name: str,
        handler: "Callable[[int, str, dict], dict]",
    ) -> None:
        """Register a module-level callback for a Brain Core action name.

        The *handler* is called after the in-memory workflow sink with the
        signature ``(tenant_id: int, decision_id: str, payload: dict) -> dict``.
        This wires Brain Core decisions back into real module write-paths,
        closing the Brain → Module action feedback loop.
        """
        self._dispatcher.register_module_handler(action_name, handler)
        logger.info("brain_core.module_handler_registered action_name=%s", action_name)

    # ------------------------------------------------------------------
    # Phase XVI — Predictive Intelligence
    # ------------------------------------------------------------------

    def predict_risk(
        self,
        *,
        event_type: str,
        tenant_id: int,
        entity_id: str,
        history: list[dict],
        horizon_days: int = 7,
    ) -> dict:
        """Predict future risk level from historical signal scores."""
        return self._predictor.predict_risk(
            event_type=event_type,
            tenant_id=tenant_id,
            entity_id=entity_id,
            history=history,
            horizon_days=horizon_days,
        )

    def detect_anomalies(
        self,
        *,
        tenant_id: int,
        metric_name: str,
        values: list[float],
        entity_ids: list[str] | None = None,
        z_threshold: float = 2.0,
    ) -> dict:
        return self._anomaly_detector.detect(
            tenant_id=tenant_id,
            metric_name=metric_name,
            values=values,
            entity_ids=entity_ids,
            z_threshold=z_threshold,
        )

    def proactive_recommendations(self, tenant_id: int) -> dict:
        profile = self._policy_resolver.get_profile(tenant_id)
        tenant_signals = [signal for signal in self._signals if int(signal.get("tenant_id") or 0) == tenant_id]
        tenant_decisions = [decision for decision in self._decisions if int(decision.get("tenant_id") or 0) == tenant_id]

        recommendations: list[dict] = []
        attendance_count = sum(1 for signal in tenant_signals if signal.get("event_type") == "academic.attendance_risk.detected")
        workload_count = sum(1 for signal in tenant_signals if signal.get("event_type") == "faculty.workload_overload.detected")
        critical_decisions = sum(1 for decision in tenant_decisions if decision.get("priority") == "critical")

        if attendance_count >= 2:
            recommendations.append(
                {
                    "recommendation_type": "student_retention_playbook",
                    "priority": "high",
                    "trigger": "attendance_risk_cluster",
                    "signals_considered": attendance_count,
                    "recommended_actions": [
                        "launch_outreach_campaign",
                        "pre_open_advising_slots",
                    ],
                    "rationale": "Repeated attendance risk signals suggest a proactive student retention intervention before escalation.",
                }
            )

        if workload_count >= 2:
            recommendations.append(
                {
                    "recommendation_type": "faculty_capacity_rebalance",
                    "priority": "high",
                    "trigger": "faculty_overload_cluster",
                    "signals_considered": workload_count,
                    "recommended_actions": [
                        "review_teaching_load",
                        "protect_office_hours_capacity",
                    ],
                    "rationale": "Multiple workload overload signals indicate a need for proactive staffing or schedule rebalance.",
                }
            )

        if critical_decisions >= 2:
            recommendations.append(
                {
                    "recommendation_type": "executive_review",
                    "priority": "critical",
                    "trigger": "critical_decision_density",
                    "signals_considered": critical_decisions,
                    "recommended_actions": ["schedule_executive_review"],
                    "rationale": "Critical decisions are accumulating for this tenant and warrant operator review before further automation.",
                }
            )

        llm_summary = None
        if recommendations and profile.enable_ai_reasoning:
            llm_summary = llm_bridge.generate_explanation(
                event_type="brain.proactive_recommendations.generated",
                situation_type="proactive_recommendations",
                severity=recommendations[0]["priority"],
                urgency=recommendations[0]["priority"],
                factors=[item["trigger"] for item in recommendations],
                actions=[action for item in recommendations for action in item["recommended_actions"]],
                context_summary=f"tenant_id={tenant_id}; signals={len(tenant_signals)}; decisions={len(tenant_decisions)}",
            )

        return {
            "tenant_id": tenant_id,
            "total": len(recommendations),
            "items": recommendations,
            "ai_reasoning_enabled": bool(profile.enable_ai_reasoning),
            "llm_summary": llm_summary,
        }

    def get_kpi_dashboard(self, tenant_id: int) -> dict:
        """XVI4 — Executive Brain KPI Dashboard for a single tenant."""
        from app.modules.brain_core.reporting.kpi_dashboard import brain_kpi_dashboard

        outcomes = self._outcome_tracker.list_outcomes()
        return brain_kpi_dashboard.generate(
            tenant_id=tenant_id,
            signals=self._signals,
            decisions=self._decisions,
            outcomes=outcomes,
        )

    # ------------------------------------------------------------------
    # Phase XVII — Adaptive Learning & Optimization
    # ------------------------------------------------------------------

    def evaluate_learning(self, tenant_id: int) -> dict:
        """XVII3 — Evaluate the learning state for a tenant.

        Returns detailed metrics about outcome effectiveness and whether the
        policy tuning engine has enough data to make meaningful adjustments.
        """
        from datetime import datetime, timezone

        metrics = self._quality_tracker.metrics_for_tenant(tenant_id)
        total_decisions = int(metrics.get("total_outcomes") or 0)
        positive = int(metrics.get("positive") or 0)
        negative = int(metrics.get("negative") or 0)
        neutral = int(metrics.get("neutral") or 0)
        positive_rate = float(metrics.get("positive_rate") or 0.0)
        negative_rate = float(metrics.get("negative_rate") or 0.0)

        # Count raw outcomes for this tenant
        outcomes = self._outcome_tracker.list_outcomes()
        tenant_outcomes = [o for o in outcomes if int(o.get("tenant_id") or 0) == tenant_id]
        tenant_decisions = [d for d in self._decisions if int(d.get("tenant_id") or 0) == tenant_id]

        effectiveness_score = positive_rate * (1.0 - negative_rate)
        policy_drift_detected = (negative_rate >= 0.5 and total_decisions >= 4) or (
            positive_rate >= 0.8 and total_decisions >= 5
        )
        learning_ready = total_decisions >= 4 or len(tenant_outcomes) >= 4

        return {
            "tenant_id": tenant_id,
            "total_decisions": len(tenant_decisions),
            "total_outcomes": len(tenant_outcomes),
            "positive_outcomes": positive,
            "negative_outcomes": negative,
            "neutral_outcomes": neutral,
            "effectiveness_score": round(effectiveness_score, 4),
            "policy_drift_detected": policy_drift_detected,
            "learning_ready": learning_ready,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

    def optimize(self, tenant_id: int, domain_signals: list[dict]) -> dict:
        """XVII4 — Brain Optimization Engine: resource allocation recommendations."""
        from app.modules.brain_core.reasoning.optimizer import BrainOptimizer
        optimizer = BrainOptimizer()
        return optimizer.optimize(tenant_id=tenant_id, domain_signals=domain_signals)


brain_core_service = BrainCoreService()
