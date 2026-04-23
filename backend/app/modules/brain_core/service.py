from __future__ import annotations

from datetime import datetime, timezone
import logging
import time
from uuid import uuid4

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
from app.modules.brain_core.reasoning.explanation import ExplanationEngine
from app.modules.brain_core.reasoning.engine import ReasoningEngine
from app.modules.brain_core.reasoning.knowledge_retriever import KnowledgeRetriever
from app.modules.brain_core.registry import SignalRegistry


logger = logging.getLogger(__name__)


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
        self._explanation = ExplanationEngine()
        self._knowledge = KnowledgeRetriever()
        self._dispatcher = ActionDispatcher(on_workflow_case_outcome=self._record_case_feedback)
        self._signals: list[dict] = []
        self._decisions: list[dict] = []
        self._explanations: dict[str, dict] = {}

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

        self._signals.append(signal)

        context_started = time.perf_counter()
        context = self._context_builder.build_context(signal)
        self._observability.record_latency_ms("context_build_latency_ms", (time.perf_counter() - context_started) * 1000.0)
        classification = self._classifier.classify(signal, context)
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
            else:
                self._observability.increment("action_dispatch_success_total")
        elif policy_validation.requires_approval:
            self._observability.increment("decisions_requiring_approval_total")
        else:
            self._observability.increment("action_dispatch_failure_total")

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
        self._explanations[decision_id] = explanation
        self._observability.increment("decisions_created_total")
        self._observability.increment(f"decisions_by_type_{reasoning['decision_type']}_total")
        self._observability.increment(f"decisions_by_priority_{reasoning['priority']}_total")
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


brain_core_service = BrainCoreService()
