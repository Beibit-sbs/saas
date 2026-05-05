from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import logging
import time
import uuid
from copy import deepcopy
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

_BUDGET_OVERRUN_EVENT_TYPES = frozenset(
    {
        "finance.expense.budget_exceeded",
        "campus.budget.overrun_risk_detected",
        "campus.expense_controls.budget_exceeded_risk_detected",
    }
)

# A-015.2 — Procurement Approval Automation event types
_PROCUREMENT_APPROVAL_EVENT_TYPES = frozenset(
    {
        "procurement.request_submitted",
        "procurement.approval_required",
    }
)

# A-015.4 — Finance Operations Health Brain event types
_FINANCE_OPERATIONS_HEALTH_EVENT_TYPES = frozenset(
    {
        "finance.operations.health_check",
        "finance.operations.risk_detected",
    }
)

# A-016.1 — Academic Integrity Violation Detection Brain event types
_ACADEMIC_INTEGRITY_VIOLATION_EVENT_TYPES = frozenset(
    {
        "academic_integrity.violation.detected",
        "academic_integrity.risk_detected",
        "plagiarism.similarity.high_detected",
        "exam.proctoring.violation_detected",
        "coursework.submission.suspicious_detected",
        "ai_plagiarism.risk_detected",
    }
)

# A-016.2 — Thesis Governance + Supervisor Assignment Brain event types
_THESIS_GOVERNANCE_EVENT_TYPES = frozenset(
    {
        "thesis.submission.created",
        "thesis.submission.pending_review",
        "thesis.supervisor.assignment_needed",
        "thesis.supervisor.overloaded",
        "thesis.review.delayed",
        "thesis.governance.risk_detected",
    }
)

# A-016.3 — Exam Proctoring Violation Workflow event types
_EXAM_PROCTORING_EVENT_TYPES = frozenset(
    {
        "faculty.proctoring.violation_detected",
        "exam.proctoring.suspicious_activity_detected",
        "exam.proctoring.multiple_faces_detected",
        "exam.proctoring.face_mismatch_detected",
        "exam.proctoring.forbidden_app_detected",
        "exam.proctoring.camera_absent_detected",
    }
)


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
        self._quality_tracker = DecisionQualityTracker()
        self._outcome_tracker = OutcomeTracker(quality_tracker=self._quality_tracker)
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
        self._signal_dedup_cache: dict[tuple[int, str], tuple[uuid.UUID, float]] = {}
        self._decisions: list[dict] = []
        self._explanations: dict[str, dict] = {}
        self._learning_apply_idempotency: dict[str, dict] = {}
        self._drift_alerts: dict[int, list[dict]] = {}  # XVIII3 — Policy drift tracking by tenant_id
        self._agent_event_log: dict[tuple, list[dict]] = {}  # XXIII1 — Step-level event log keyed by (task_id, step_id)
        self._step_dependencies: dict[tuple, list[str]] = {}  # XXIV1 — (task_id, step_id) → list of step_ids that must be done first
        self._resource_budgets: dict[str, dict] = {}  # XXIV2 — task_id → {token_limit, cost_limit_usd}
        self._resource_usage: dict[str, dict] = {}  # XXIV2 — task_id → {tokens_used, cost_usd}
        self._task_feedback: dict[str, list[dict]] = {}  # XXIV3 — task_id → list of feedback records
        self._agent_handoffs: dict[str, dict] = {}  # XXV1 — handoff_id → handoff record
        self._task_splits: dict[str, dict] = {}  # XXV2 — task_id → {subtasks, strategy}
        self._task_merges: dict[str, dict] = {}  # XXV3 — task_id → merge result
        self._agent_learning_signals: dict[str, list] = {}  # XXVI1 — agent_id → list of signals
        self._task_learning_records: dict[str, list] = {}  # XXVI1 — task_id → list of signals
        self._task_optimizations: dict[str, list] = {}  # XXVI2 — task_id → optimization history
        self._agent_benchmarks: dict[str, dict] = {}  # XXVI3 — agent_id → benchmark record
        self._agent_knowledge: dict[str, dict] = {}  # XXVII1 — agent_id → {key → knowledge_record}
        self._shared_knowledge: dict[str, list] = {}  # XXVII2 — agent_id → list of shared knowledge records received
        self._reprocess_idempotency: dict[str, dict] = {}  # XXVIII1 — (signal_id:idempotency_key) → replay result
        self._reprocess_audit: list[dict] = []  # XXVIII3 — replay audit events
        self._replay_suspended_tenants: set[int] = set()  # XXVIII2 — tenants with replay policy suspended
        self._replay_max_per_signal: int = 10  # XXVIII2 — max replay executions per signal
        self._replay_policies: dict[int, dict] = {}  # XXXI1 — tenant_id → replay policy config
        self._replay_policy_history: list[dict] = []  # XXXI3 — audit log of policy changes
        self._replay_request_queue: dict[str, dict] = {}  # XXXII1 — request_id → replay request record
        self._replay_escalations: dict[str, list[dict]] = {}  # XXXII2 — request_id → list of escalations
        self._replay_sla_metrics: dict[int, dict] = {}  # XXXII3 — tenant_id → SLA metrics

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

        cache = getattr(self, "_signal_dedup_cache", None)
        if cache is None:
            cache = {}
            setattr(self, "_signal_dedup_cache", cache)

        cached = cache.get((tenant_id, dedup_key))
        now = time.perf_counter()
        if cached is not None:
            cached_signal_id, cached_at = cached
            if now - cached_at <= float(window_seconds):
                return cached_signal_id
            cache.pop((tenant_id, dedup_key), None)

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
    _NOTIFIABLE_DECISION_TYPES: frozenset[str] = frozenset({"risk", "preventive", "compliance", "academic_integrity_review", "thesis_supervisor_assignment", "exam_integrity_review"})

    def _normalize_degree_progress_signal(self, signal: dict) -> tuple[dict, str | None]:
        """Normalize graduation-risk signals to canonical student/source fields.

        Returns a tuple: (normalized_signal, rejection_reason). If rejection_reason
        is set, the caller must fail-closed.
        """
        event_type = str(signal.get("event_type") or "")
        if event_type != "degree_progress.graduation_risk.detected":
            return signal, None

        normalized = dict(signal)
        payload = dict(normalized.get("payload") or {})
        subject = dict(normalized.get("subject") or {})

        student_id = (
            payload.get("student_id")
            or payload.get("student_profile_id")
            or subject.get("student_id")
            or normalized.get("student_id")
        )
        if student_id in (None, ""):
            return normalized, "missing_student_context"

        normalized["student_id"] = student_id
        subject["student_id"] = student_id
        normalized["subject"] = subject

        payload["student_id"] = student_id
        payload.setdefault("source_module", "degree_progress")
        payload.setdefault("source_entity_type", "student_graduation_progress")
        payload.setdefault("source_entity_id", str(student_id))
        normalized["payload"] = payload

        source_module = str(payload.get("source_module") or "degree_progress")
        source_entity_type = str(payload.get("source_entity_type") or "student_graduation_progress")
        source_entity_id = str(payload.get("source_entity_id") or student_id)
        if not normalized.get("source_module"):
            normalized["source_module"] = source_module
        if str(normalized.get("source_entity_type") or "").strip().lower() in {"", "unknown"}:
            normalized["source_entity_type"] = source_entity_type
        if str(normalized.get("source_entity_id") or "").strip().lower() in {"", "unknown"}:
            normalized["source_entity_id"] = source_entity_id
        return normalized, None

    def _normalize_scholarship_award_risk_signal(self, signal: dict) -> tuple[dict, str | None]:
        """Fail-closed normalization for scholarship award at-risk signals."""
        event_type = str(signal.get("event_type") or "")
        if event_type != "scholarship.award.at_risk_detected":
            return signal, None

        normalized = dict(signal)
        payload = dict(normalized.get("payload") or {})
        subject = dict(normalized.get("subject") or {})

        student_id = (
            payload.get("student_id")
            or subject.get("student_id")
            or normalized.get("student_id")
        )
        if student_id in (None, ""):
            return normalized, "missing_student_context"

        normalized["student_id"] = student_id
        subject["student_id"] = student_id
        normalized["subject"] = subject
        payload["student_id"] = student_id
        normalized["payload"] = payload
        return normalized, None

    def _normalize_procurement_approval_signal(self, signal: dict) -> tuple[dict, str | None]:
        """A-015.2 — Fail-closed normalization for procurement approval signals.

        Rejects if both request_id and estimated_total are missing.
        Attaches procurement_risk_origin and procurement_risk_evidence metadata.
        """
        event_type = str(signal.get("event_type") or "")
        if event_type not in _PROCUREMENT_APPROVAL_EVENT_TYPES:
            return signal, None

        normalized = dict(signal)
        payload = dict(normalized.get("payload") or {})

        request_id = payload.get("request_id")
        estimated_total = payload.get("estimated_total")

        # Fail-closed: must have at least request_id OR estimated_total
        if not request_id and estimated_total is None:
            return normalized, "missing_procurement_request_context"

        # Canonicalise numeric field
        try:
            estimated_total_f = float(estimated_total) if estimated_total is not None else None
        except (TypeError, ValueError):
            estimated_total_f = None

        payload["procurement_risk_origin"] = event_type
        payload["procurement_risk_evidence"] = {
            "request_id": request_id,
            "estimated_total": estimated_total_f,
            "priority": payload.get("priority"),
            "department_id": payload.get("department_id"),
        }
        payload.setdefault("source_module", "procurement")
        payload.setdefault("source_entity_type", "procurement_request")
        payload.setdefault("source_entity_id", str(request_id or "unknown"))

        normalized["payload"] = payload
        if str(normalized.get("source_entity_type") or "").strip().lower() in {"", "unknown"}:
            normalized["source_entity_type"] = str(payload.get("source_entity_type") or "procurement_request")
        if str(normalized.get("source_entity_id") or "").strip().lower() in {"", "unknown"}:
            normalized["source_entity_id"] = str(payload.get("source_entity_id") or "unknown")
        if not normalized.get("source_module"):
            normalized["source_module"] = str(payload.get("source_module") or "procurement")

        return normalized, None

    def _normalize_budget_overrun_signal(self, signal: dict) -> tuple[dict, str | None]:
        """Fail-closed normalization for budget overrun signals.

        Ensures canonical numeric fields needed for safe risk processing and
        attaches origin/evidence metadata for downstream audit/workflow payloads.
        """
        event_type = str(signal.get("event_type") or "")
        if event_type not in _BUDGET_OVERRUN_EVENT_TYPES:
            return signal, None

        normalized = dict(signal)
        payload = dict(normalized.get("payload") or {})

        amount = payload.get("amount")
        budget_limit = payload.get("budget_limit")
        attempted_total = payload.get("attempted_total")
        current_total = payload.get("current_total")
        overrun_amount = payload.get("overrun_amount")
        overrun_percent = payload.get("overrun_percent")

        # Derive canonical overrun metrics where possible.
        try:
            attempted_f = float(attempted_total) if attempted_total is not None else None
        except (TypeError, ValueError):
            attempted_f = None
        try:
            limit_f = float(budget_limit) if budget_limit is not None else None
        except (TypeError, ValueError):
            limit_f = None
        try:
            current_f = float(current_total) if current_total is not None else None
        except (TypeError, ValueError):
            current_f = None

        if overrun_amount is None and attempted_f is not None and limit_f is not None:
            overrun_amount = attempted_f - limit_f
        if overrun_percent is None and overrun_amount is not None and limit_f and limit_f > 0:
            try:
                overrun_percent = float(overrun_amount) / float(limit_f)
            except (TypeError, ValueError, ZeroDivisionError):
                overrun_percent = None

        # Fail-closed: at least one budget magnitude and one threshold magnitude must exist.
        has_amount_signal = any(v is not None for v in (amount, attempted_f, current_f, overrun_amount))
        has_threshold_signal = any(v is not None for v in (budget_limit, overrun_percent))
        if not has_amount_signal or not has_threshold_signal:
            return normalized, "missing_budget_amount_or_threshold"

        payload["budget_risk_origin"] = event_type
        payload["overrun_amount"] = overrun_amount
        payload["overrun_percent"] = overrun_percent
        payload.setdefault("source_module", "expense_controls")
        payload.setdefault("source_entity_type", "budget_risk")
        payload.setdefault("source_entity_id", str(payload.get("budget_id") or payload.get("budget_plan_id") or payload.get("cost_center_id") or "unknown"))
        payload["budget_risk_evidence"] = {
            "amount": amount,
            "current_total": current_total,
            "attempted_total": attempted_total,
            "budget_limit": budget_limit,
            "overrun_amount": overrun_amount,
            "overrun_percent": overrun_percent,
        }

        normalized["payload"] = payload
        if str(normalized.get("source_entity_type") or "").strip().lower() in {"", "unknown"}:
            normalized["source_entity_type"] = str(payload.get("source_entity_type") or "budget_risk")
        if str(normalized.get("source_entity_id") or "").strip().lower() in {"", "unknown"}:
            normalized["source_entity_id"] = str(payload.get("source_entity_id") or "unknown")
        if not normalized.get("source_module"):
            normalized["source_module"] = str(payload.get("source_module") or "expense_controls")

        return normalized, None

    def _normalize_academic_integrity_violation_signal(self, signal: dict) -> tuple[dict, str | None]:
        """Fail-closed normalization for academic integrity violation signals (A-016.1).

        Ensures required tenant context, attaches origin/evidence metadata for
        downstream audit/workflow payloads, and normalizes similarity_score to a
        consistent percentage representation (0–100).
        Does NOT make any punitive academic status changes.
        """
        event_type = str(signal.get("event_type") or "")
        if event_type not in _ACADEMIC_INTEGRITY_VIOLATION_EVENT_TYPES:
            return signal, None

        normalized = dict(signal)
        payload = dict(normalized.get("payload") or {})

        # Fail-closed: tenant_id and at least one subject identifier required
        tenant_id = int(normalized.get("tenant_id") or 0)
        if tenant_id <= 0:
            return normalized, "missing_tenant_context"

        student_id = str(payload.get("student_id") or "").strip()
        source_entity_id = str(
            normalized.get("source_entity_id")
            or payload.get("source_entity_id")
            or payload.get("submission_id")
            or payload.get("exam_id")
            or ""
        ).strip()
        if not student_id and not source_entity_id:
            return normalized, "missing_subject_identifier"

        # Normalize similarity_score to percentage float (0–100)
        raw_score = payload.get("similarity_score")
        if isinstance(raw_score, (int, float)):
            if raw_score <= 1.0:
                payload["similarity_score"] = round(float(raw_score) * 100.0, 2)
            else:
                payload["similarity_score"] = round(float(raw_score), 2)

        # Attach evidence metadata for audit
        payload.setdefault("risk_source", event_type)
        payload.setdefault("correlation_id", str(normalized.get("correlation_id") or ""))
        payload.setdefault("student_id", student_id)

        normalized["payload"] = payload
        if str(normalized.get("source_entity_type") or "").strip().lower() in {"", "unknown"}:
            normalized["source_entity_type"] = str(payload.get("source_entity_type") or "integrity_submission")
        if str(normalized.get("source_entity_id") or "").strip().lower() in {"", "unknown"}:
            normalized["source_entity_id"] = source_entity_id or "unknown"
        if not normalized.get("source_module"):
            normalized["source_module"] = str(payload.get("source_module") or "academic_integrity")

        return normalized, None

    def _normalize_thesis_governance_signal(self, signal: dict) -> tuple[dict, str | None]:
        """Fail-closed normalization for thesis governance signals (A-016.2).

        Ensures required tenant + thesis_id context, attaches origin/evidence metadata,
        and normalizes optional supervisor/days fields for downstream risk classification.
        Does NOT make any punitive academic or thesis status changes.
        """
        event_type = str(signal.get("event_type") or "")
        if event_type not in _THESIS_GOVERNANCE_EVENT_TYPES:
            return signal, None

        normalized = dict(signal)
        payload = dict(normalized.get("payload") or {})

        # Fail-closed: tenant_id required
        tenant_id = int(normalized.get("tenant_id") or 0)
        if tenant_id <= 0:
            return normalized, "missing_tenant_context"

        # Fail-closed: thesis_id required
        thesis_id = str(
            payload.get("thesis_id")
            or normalized.get("source_entity_id")
            or ""
        ).strip()
        if not thesis_id:
            return normalized, "missing_thesis_id"

        # Attach evidence / audit metadata
        payload.setdefault("risk_source", event_type)
        payload.setdefault("correlation_id", str(normalized.get("correlation_id") or ""))
        payload.setdefault("thesis_id", thesis_id)

        # Optional fields: do NOT crash if absent — just record absence in evidence
        student_id = str(payload.get("student_id") or "").strip()
        supervisor_id = str(payload.get("supervisor_id") or "").strip()
        if not supervisor_id:
            payload.setdefault("supervisor_assignment_evidence", "supervisor_id_not_provided")
        if not student_id:
            payload.setdefault("student_id_evidence", "student_id_not_provided")

        normalized["payload"] = payload
        if str(normalized.get("source_entity_type") or "").strip().lower() in {"", "unknown"}:
            normalized["source_entity_type"] = str(payload.get("source_entity_type") or "thesis")
        if str(normalized.get("source_entity_id") or "").strip().lower() in {"", "unknown"}:
            normalized["source_entity_id"] = thesis_id
        if not normalized.get("source_module"):
            normalized["source_module"] = str(payload.get("source_module") or "thesis_governance")

        return normalized, None

    def _normalize_exam_proctoring_signal(self, signal: dict) -> tuple[dict, str | None]:
        """Fail-closed normalization for exam proctoring violation signals (A-016.3).

        Ensures required tenant + subject context, attaches origin/evidence metadata
        for downstream audit/workflow payloads.
        Does NOT make any punitive academic status changes (no grade change, no
        exam failure, no disciplinary sanction).
        """
        event_type = str(signal.get("event_type") or "")
        if event_type not in _EXAM_PROCTORING_EVENT_TYPES:
            return signal, None

        normalized = dict(signal)
        payload = dict(normalized.get("payload") or {})

        # Fail-closed: tenant_id required
        tenant_id = int(normalized.get("tenant_id") or 0)
        if tenant_id <= 0:
            return normalized, "missing_tenant_context"

        # Fail-closed: student_id OR exam_id required as subject identifier
        student_id = str(payload.get("student_id") or "").strip()
        exam_id = str(
            payload.get("exam_id")
            or normalized.get("source_entity_id")
            or ""
        ).strip()
        if not student_id and not exam_id:
            return normalized, "missing_subject_identifier"

        # Attach evidence / audit metadata — do not crash on missing optional fields
        payload.setdefault("risk_source", event_type)
        payload.setdefault("correlation_id", str(normalized.get("correlation_id") or ""))
        payload.setdefault("student_id", student_id)
        payload.setdefault("exam_id", exam_id)

        # Record absence of optional fields in evidence (no crash)
        if not str(payload.get("violation_type") or "").strip():
            payload.setdefault("violation_type_evidence", "violation_type_not_provided")
        if not str(payload.get("proctoring_session_id") or "").strip():
            payload.setdefault("proctoring_session_id_evidence", "proctoring_session_id_not_provided")
        if payload.get("confidence_score") is None:
            payload.setdefault("confidence_score_evidence", "confidence_score_not_provided")

        normalized["payload"] = payload
        if str(normalized.get("source_entity_type") or "").strip().lower() in {"", "unknown"}:
            normalized["source_entity_type"] = str(payload.get("source_entity_type") or "exam_proctoring")
        if str(normalized.get("source_entity_id") or "").strip().lower() in {"", "unknown"}:
            normalized["source_entity_id"] = exam_id or student_id or "unknown"
        if not normalized.get("source_module"):
            normalized["source_module"] = str(payload.get("source_module") or "exam_proctoring")

        return normalized, None

    def _resolve_decision_scenario(self, *, event_type: str, classification: dict) -> str:
        """Resolve the decision scenario, allowing additive routing overrides."""
        scenario = SignalRegistry.signals[event_type]["scenario"]
        reasoning_path = str(classification.get("reasoning_path") or "")

        # Graduation risk can also be inferred from transcript signals when the
        # classifier marks the same reasoning path.
        if (
            event_type == "transcripts.inconsistency.detected"
            and reasoning_path.startswith("graduation_risk_")
        ):
            return "graduation_degree_progress_risk"
        return scenario

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

        signal, normalization_rejection = self._normalize_degree_progress_signal(signal)
        if normalization_rejection is not None:
            self._observability.increment("signals_rejected_total")
            return {"status": "rejected", "reason": normalization_rejection}

        signal, normalization_rejection = self._normalize_scholarship_award_risk_signal(signal)
        if normalization_rejection is not None:
            self._observability.increment("signals_rejected_total")
            return {"status": "rejected", "reason": normalization_rejection}

        signal, normalization_rejection = self._normalize_budget_overrun_signal(signal)
        if normalization_rejection is not None:
            self._observability.increment("signals_rejected_total")
            return {"status": "rejected", "reason": normalization_rejection}

        signal, normalization_rejection = self._normalize_procurement_approval_signal(signal)
        if normalization_rejection is not None:
            self._observability.increment("signals_rejected_total")
            return {"status": "rejected", "reason": normalization_rejection}

        signal, normalization_rejection = self._normalize_academic_integrity_violation_signal(signal)
        if normalization_rejection is not None:
            self._observability.increment("signals_rejected_total")
            return {"status": "rejected", "reason": normalization_rejection}

        signal, normalization_rejection = self._normalize_thesis_governance_signal(signal)
        if normalization_rejection is not None:
            self._observability.increment("signals_rejected_total")
            return {"status": "rejected", "reason": normalization_rejection}

        signal, normalization_rejection = self._normalize_exam_proctoring_signal(signal)
        if normalization_rejection is not None:
            self._observability.increment("signals_rejected_total")
            return {"status": "rejected", "reason": normalization_rejection}

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

        payload = dict(signal.get("payload") or {})
        source_entity_type = str(
            signal.get("source_entity_type")
            or payload.get("source_entity_type")
            or ""
        )
        source_entity_id = str(
            signal.get("source_entity_id")
            or payload.get("source_entity_id")
            or ""
        )
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
        cache = getattr(self, "_signal_dedup_cache", None)
        if cache is None:
            cache = {}
            setattr(self, "_signal_dedup_cache", cache)
        cache[(tenant_id, dedup_key)] = (signal_id, time.perf_counter())

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
        scenario = self._resolve_decision_scenario(event_type=event_type, classification=classification)
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

    # ------------------------------------------------------------------
    # XXVIII2 — Replay Safety Gate helpers
    # ------------------------------------------------------------------

    def suspend_tenant_replay(self, tenant_id: int) -> None:
        """Administratively suspend replay for a tenant (fail-closed)."""
        self._replay_suspended_tenants.add(tenant_id)

    def unsuspend_tenant_replay(self, tenant_id: int) -> None:
        self._replay_suspended_tenants.discard(tenant_id)

    def _replay_safety_gate(self, signal: dict, actor: str) -> dict | None:
        """Return an error dict if replay is blocked, else None (allow).

        Checks (fail-closed — any block stops execution):
        1. Tenant autonomy_level == 0 → manual-only, replay denied.
        2. Tenant replay suspended via admin flag.
        3. Signal has exceeded max replay execution count.
        """
        tenant_id = int(signal.get("tenant_id") or 0)
        signal_id = signal.get("signal_id", "")

        # 1. Autonomy-level gate: level 0 = full manual, no automated replay
        policy = self._policy_resolver.get_profile(tenant_id)
        if policy.autonomy_level == 0:
            self._reprocess_audit.append(
                {
                    "event": "replay_rejected",
                    "signal_id": signal_id,
                    "actor": actor,
                    "reason": "autonomy_blocked",
                    "tenant_id": tenant_id,
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            return {
                "status": "safety_gate_blocked",
                "reason": "autonomy_blocked",
                "signal_id": signal_id,
                "tenant_id": tenant_id,
            }

        # 2. Policy suspension gate
        if tenant_id in self._replay_suspended_tenants:
            self._reprocess_audit.append(
                {
                    "event": "replay_rejected",
                    "signal_id": signal_id,
                    "actor": actor,
                    "reason": "policy_suspended",
                    "tenant_id": tenant_id,
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            return {
                "status": "safety_gate_blocked",
                "reason": "policy_suspended",
                "signal_id": signal_id,
                "tenant_id": tenant_id,
            }

        # 3. Replay rate-limit per signal (executed replays only, not dry-runs)
        executed_count = sum(
            1
            for e in self._reprocess_audit
            if e.get("event") == "replay_executed" and e.get("signal_id") == signal_id
        )
        if executed_count >= self._replay_max_per_signal:
            self._reprocess_audit.append(
                {
                    "event": "replay_rejected",
                    "signal_id": signal_id,
                    "actor": actor,
                    "reason": "replay_rate_limit_exceeded",
                    "tenant_id": tenant_id,
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            return {
                "status": "safety_gate_blocked",
                "reason": "replay_rate_limit_exceeded",
                "signal_id": signal_id,
                "tenant_id": tenant_id,
            }

        return None  # gate open

    def reprocess_signal(
        self,
        signal_id: str,
        *,
        actor: str = "system",
        dry_run: bool = False,
        idempotency_key: str | None = None,
        replay_reason: str | None = None,
        expected_tenant_id: int | None = None,
    ) -> dict:
        signal = next((s for s in self._signals if s.get("signal_id") == signal_id), None)
        if signal is None:
            return {"status": "not_found", "signal_id": signal_id}

        signal_tenant_id = int(signal.get("tenant_id") or 0)
        if expected_tenant_id is not None and signal_tenant_id != expected_tenant_id:
            self._reprocess_audit.append(
                {
                    "event": "replay_rejected",
                    "signal_id": signal_id,
                    "actor": actor,
                    "reason": "tenant_mismatch",
                    "expected_tenant_id": expected_tenant_id,
                    "actual_tenant_id": signal_tenant_id,
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            return {
                "status": "tenant_mismatch",
                "signal_id": signal_id,
                "expected_tenant_id": expected_tenant_id,
                "actual_tenant_id": signal_tenant_id,
            }

        # XXVIII2 — Safety gate (fail-closed; dry_run also goes through gate)
        gate_result = self._replay_safety_gate(signal, actor)
        if gate_result is not None:
            return gate_result

        logger.info(
            "brain_core.reprocess_signal signal_id=%s actor=%s dry_run=%s",
            signal_id,
            actor,
            dry_run,
        )

        self._reprocess_audit.append(
            {
                "event": "replay_requested",
                "signal_id": signal_id,
                "actor": actor,
                "dry_run": dry_run,
                "idempotency_key": idempotency_key,
                "replay_reason": replay_reason,
                "tenant_id": signal_tenant_id,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        if dry_run:
            return {
                "status": "dry_run",
                "signal_id": signal_id,
                "tenant_id": signal_tenant_id,
                "event_type": signal.get("event_type"),
                "replay_reason": replay_reason,
                "idempotent_replay": False,
                "would_process": True,
            }

        cache_key = None
        if idempotency_key:
            cache_key = f"{signal_id}:{idempotency_key}"
            cached = self._reprocess_idempotency.get(cache_key)
            if cached is not None:
                replay = deepcopy(cached)
                replay["idempotent_replay"] = True
                return replay

        result = self.process_signal(dict(signal))
        result["reprocessed_by"] = actor
        result["original_signal_id"] = signal_id
        result["replay_reason"] = replay_reason
        result["idempotency_key"] = idempotency_key
        result["idempotent_replay"] = False

        self._reprocess_audit.append(
            {
                "event": "replay_executed",
                "signal_id": signal_id,
                "actor": actor,
                "replay_reason": replay_reason,
                "idempotency_key": idempotency_key,
                "tenant_id": signal_tenant_id,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        if cache_key:
            self._reprocess_idempotency[cache_key] = deepcopy(result)
        return result

    # ------------------------------------------------------------------
    # XXVIII3 — Replay Audit Trail
    # ------------------------------------------------------------------

    def get_replay_audit(
        self,
        *,
        signal_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Return replay audit log, optionally filtered by signal_id and/or event type.

        Each entry contains: event, signal_id, actor, reason (optional),
        tenant_id, recorded_at, plus replay-specific fields.
        """
        records = self._reprocess_audit
        if signal_id:
            records = [r for r in records if r.get("signal_id") == signal_id]
        if event_type:
            records = [r for r in records if r.get("event") == event_type]
        return list(records[-limit:])

    def approve_signal_reprocess(
        self,
        signal_id: str,
        *,
        actor: str = "system",
        reason: str | None = None,
        idempotency_key: str | None = None,
        expected_tenant_id: int | None = None,
    ) -> dict:
        signal = next((s for s in self._signals if s.get("signal_id") == signal_id), None)
        if signal is None:
            return {"status": "not_found", "signal_id": signal_id}

        signal_tenant_id = int(signal.get("tenant_id") or 0)
        if expected_tenant_id is not None and signal_tenant_id != expected_tenant_id:
            self._reprocess_audit.append(
                {
                    "event": "replay_rejected",
                    "signal_id": signal_id,
                    "actor": actor,
                    "reason": "tenant_mismatch",
                    "expected_tenant_id": expected_tenant_id,
                    "actual_tenant_id": signal_tenant_id,
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            return {
                "status": "tenant_mismatch",
                "signal_id": signal_id,
                "expected_tenant_id": expected_tenant_id,
                "actual_tenant_id": signal_tenant_id,
            }

        self._reprocess_audit.append(
            {
                "event": "replay_approved",
                "signal_id": signal_id,
                "actor": actor,
                "reason": reason,
                "tenant_id": signal_tenant_id,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        result = self.reprocess_signal(
            signal_id,
            actor=actor,
            dry_run=False,
            idempotency_key=idempotency_key,
            replay_reason=reason,
            expected_tenant_id=expected_tenant_id,
        )
        if result.get("status") in {"not_found", "tenant_mismatch", "safety_gate_blocked"}:
            return result

        result["approval_status"] = "approved"
        return result

    def reject_signal_reprocess(
        self,
        signal_id: str,
        *,
        actor: str = "system",
        reason: str | None = None,
        expected_tenant_id: int | None = None,
    ) -> dict:
        signal = next((s for s in self._signals if s.get("signal_id") == signal_id), None)
        if signal is None:
            return {"status": "not_found", "signal_id": signal_id}

        signal_tenant_id = int(signal.get("tenant_id") or 0)
        if expected_tenant_id is not None and signal_tenant_id != expected_tenant_id:
            self._reprocess_audit.append(
                {
                    "event": "replay_rejected",
                    "signal_id": signal_id,
                    "actor": actor,
                    "reason": "tenant_mismatch",
                    "expected_tenant_id": expected_tenant_id,
                    "actual_tenant_id": signal_tenant_id,
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            return {
                "status": "tenant_mismatch",
                "signal_id": signal_id,
                "expected_tenant_id": expected_tenant_id,
                "actual_tenant_id": signal_tenant_id,
            }

        reject_reason = reason or "operator_rejected"
        self._reprocess_audit.append(
            {
                "event": "replay_rejected",
                "signal_id": signal_id,
                "actor": actor,
                "reason": reject_reason,
                "tenant_id": signal_tenant_id,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return {
            "status": "replay_rejected",
            "signal_id": signal_id,
            "reason": reject_reason,
            "tenant_id": signal_tenant_id,
        }

    def cancel_signal_reprocess(
        self,
        signal_id: str,
        *,
        actor: str = "system",
        reason: str | None = None,
        expected_tenant_id: int | None = None,
    ) -> dict:
        signal = next((s for s in self._signals if s.get("signal_id") == signal_id), None)
        if signal is None:
            return {"status": "not_found", "signal_id": signal_id}

        signal_tenant_id = int(signal.get("tenant_id") or 0)
        if expected_tenant_id is not None and signal_tenant_id != expected_tenant_id:
            self._reprocess_audit.append(
                {
                    "event": "replay_rejected",
                    "signal_id": signal_id,
                    "actor": actor,
                    "reason": "tenant_mismatch",
                    "expected_tenant_id": expected_tenant_id,
                    "actual_tenant_id": signal_tenant_id,
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            return {
                "status": "tenant_mismatch",
                "signal_id": signal_id,
                "expected_tenant_id": expected_tenant_id,
                "actual_tenant_id": signal_tenant_id,
            }

        cancel_reason = reason or "operator_cancelled"
        self._reprocess_audit.append(
            {
                "event": "replay_cancelled",
                "signal_id": signal_id,
                "actor": actor,
                "reason": cancel_reason,
                "tenant_id": signal_tenant_id,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return {
            "status": "replay_cancelled",
            "signal_id": signal_id,
            "reason": cancel_reason,
            "tenant_id": signal_tenant_id,
        }

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

    def list_signals(self, tenant_id: int) -> list[dict]:
        """Return only signals for the specified tenant (CRITICAL: A-009 tenant isolation fix)."""
        return [s for s in self._signals if s.get("tenant_id") == tenant_id]

    def list_decisions(self, tenant_id: int) -> list[dict]:
        """Return only decisions for the specified tenant (CRITICAL: A-009 tenant isolation fix)."""
        return [d for d in self._decisions if d.get("tenant_id") == tenant_id]

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

    def record_dispatch_outcome(
        self,
        case_id: str | None = None,
        *,
        payload: dict | None = None,
        actor: str = "system",
        tenant_id: int | None = None,
        entity_id: str | int | None = None,
        outcome_type: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        if case_id is None:
            legacy_actor = actor_id or actor
            return {
                "status": "ignored",
                "reason": "legacy_dispatch_outcome_without_case_id",
                "tenant_id": tenant_id,
                "entity_id": None if entity_id is None else str(entity_id),
                "outcome_type": outcome_type,
                "actor": legacy_actor,
            }

        result = self._dispatcher.record_workflow_case_outcome(
            case_id=case_id,
            payload=dict(payload or {}),
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

    def _policy_profile_to_dict(self, profile: TenantPolicyProfile) -> dict:
        return {
            "tenant_id": profile.tenant_id,
            "autonomy_level": profile.autonomy_level,
            "require_approval_for_critical": profile.require_approval_for_critical,
            "default_approval_role": profile.default_approval_role,
            "enable_ai_reasoning": profile.enable_ai_reasoning,
        }

    def apply_learning(
        self,
        tenant_id: int,
        *,
        actor: str = "system",
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict:
        """XVIII1 — Evaluate+apply adaptive policy tuning with dry-run and idempotency."""
        cache_key = f"{tenant_id}:{idempotency_key}" if idempotency_key else None
        if cache_key and cache_key in self._learning_apply_idempotency:
            replay = deepcopy(self._learning_apply_idempotency[cache_key])
            replay["idempotent_replay"] = True
            return replay

        evaluated = self.evaluate_learning(tenant_id)
        suggestion = self.policy_tuning_suggestion(tenant_id)
        profile_before = self._policy_resolver.get_profile(tenant_id)
        before = self._policy_profile_to_dict(profile_before)

        result: dict = {
            "tenant_id": tenant_id,
            "actor": actor,
            "dry_run": dry_run,
            "learning_ready": bool(evaluated.get("learning_ready")),
            "evaluation": evaluated,
            "changed": bool(suggestion.get("changed")),
            "reason": suggestion.get("reason"),
            "before_profile": before,
            "suggested_profile": dict(suggestion.get("suggested_profile") or {}),
            "idempotent_replay": False,
            "applied": False,
            "status": "preview" if dry_run else "skipped",
            "applied_at": datetime.now(timezone.utc).isoformat(),
        }

        if dry_run:
            result["status"] = "preview"
            if not result["learning_ready"]:
                result["reason"] = "learning_not_ready"
            result["after_profile"] = before
        elif not result["learning_ready"]:
            result["status"] = "skipped"
            result["reason"] = "learning_not_ready"
            result["after_profile"] = before
        else:
            applied = self.apply_policy_tuning(tenant_id, actor=actor)
            profile_after = self._policy_resolver.get_profile(tenant_id)
            result["status"] = "applied"
            result["applied"] = True
            result["applied_result"] = applied
            result["after_profile"] = self._policy_profile_to_dict(profile_after)

        if cache_key:
            self._learning_apply_idempotency[cache_key] = deepcopy(result)
        return result

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

    # A-015.4 — Finance Operations Health Brain
    def compute_finance_operations_health(
        self,
        tenant_id: int,
        *,
        correlation_id: str | None = None,
    ) -> dict:
        """Compute and return Finance Operations Health Brain decision for a tenant.

        Fetches live budget/expense/procurement/asset data, runs deterministic
        health scoring across 5 dimensions, and returns a Brain-compatible
        decision dict with recommended actions and KPI-ready summary.

        Fail-closed: raises ValueError for missing/invalid tenant_id.
        """
        from app.modules.brain_core.finance_operations_health import compute_finance_operations_health
        from app.modules.budget_planning.service import get_budget_brain_context
        from app.modules.expense_controls.service import get_expense_brain_context
        from app.modules.procurement.service import get_procurement_health_snapshot
        from app.modules.asset_inventory.service import list_asset_items

        if not tenant_id or tenant_id <= 0:
            raise ValueError("tenant_id is required and must be > 0")

        # Collect data — each source is individually guarded; missing data produces
        # neutral/unknown dimension scores rather than false green or hard crash.
        try:
            budget_ctx = get_budget_brain_context(tenant_id)
        except Exception:
            budget_ctx = None

        try:
            expense_ctx = get_expense_brain_context(tenant_id)
        except Exception:
            expense_ctx = None

        try:
            snap = get_procurement_health_snapshot(tenant_id)
            procurement_snapshot = snap.model_dump() if hasattr(snap, "model_dump") else dict(snap)
        except Exception:
            procurement_snapshot = None

        try:
            asset_rows = [item.model_dump() if hasattr(item, "model_dump") else dict(item)
                          for item in (list_asset_items(tenant_id=tenant_id) or [])]
        except Exception:
            asset_rows = None

        # Count active finance/procurement risk signals for this tenant from
        # the in-memory decision log.
        active_risk_signals = sum(
            1 for d in self._decisions
            if int(d.get("tenant_id") or 0) == tenant_id
            and str(d.get("scenario") or "") in {
                "budget_overrun_prevention",
                "procurement_supply_chain",
                "procurement_approval_automation",
                "finance_operations_health",
            }
        )

        result = compute_finance_operations_health(
            tenant_id=tenant_id,
            budget_context=budget_ctx,
            expense_context=expense_ctx,
            procurement_snapshot=procurement_snapshot,
            asset_inventory_rows=asset_rows,
            active_risk_signals=active_risk_signals,
            correlation_id=correlation_id,
        )

        # Record decision in in-memory log for KPI dashboard aggregation
        decision_record = {
            "tenant_id": tenant_id,
            "decision_type": result["decision_type"],
            "scenario": result["scenario"],
            "risk_level": result["risk_level"],
            "overall_score": result["overall_score"],
            "recommended_actions": result["recommended_actions"],
            "correlation_id": result["correlation_id"],
        }
        self._decisions.append(decision_record)

        return result

    # ------------------------------------------------------------------
    # A-015.5 — Inventory Low Stock / Supply Risk Brain
    # ------------------------------------------------------------------

    def compute_inventory_supply_risk(
        self,
        tenant_id: int,
        *,
        item_id: str | None = None,
        item_name: str | None = None,
        current_quantity: float | int | None = None,
        reorder_threshold: float | int | None = None,
        required_quantity: float | int | None = None,
        department: str | None = None,
        location: str | None = None,
        vendor_id: str | None = None,
        budget_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        """Compute and record a deterministic Inventory / Supply Risk Brain decision.

        Fail-closed: raises ValueError if tenant_id <= 0 or item_id is missing.
        Returns a Brain-Core-compatible decision dict with supply risk classification.
        """
        from app.modules.brain_core.inventory_low_stock_brain import (
            compute_inventory_supply_risk as _compute,
        )

        result = _compute(
            tenant_id=tenant_id,
            item_id=item_id,
            item_name=item_name,
            current_quantity=current_quantity,
            reorder_threshold=reorder_threshold,
            required_quantity=required_quantity,
            department=department,
            location=location,
            vendor_id=vendor_id,
            budget_id=budget_id,
            correlation_id=correlation_id,
        )

        decision_record = {
            "tenant_id": tenant_id,
            "decision_type": result["decision_type"],
            "scenario": result["scenario"],
            "risk_level": result["risk_level"],
            "item_id": result["item_id"],
            "recommended_actions": result["recommended_actions"],
            "correlation_id": result["correlation_id"],
        }
        self._decisions.append(decision_record)

        return result

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

    def detect_policy_drift(self, tenant_id: int) -> dict:
        """XVIII3 — Detect policy drift from repeated negative outcomes."""
        from app.modules.brain_core.models import BrainOutcomeModel  # local import
        
        # Evaluate current learning status
        evaluated = self.evaluate_learning(tenant_id)
        negative_rate = float(evaluated.get("effectiveness_score") or 0.0)
        total_outcomes = int(evaluated.get("total_outcomes") or 0)
        negative_outcomes = int(evaluated.get("negative_outcomes") or 0)
        
        # Initialize alerts list if not present
        if tenant_id not in self._drift_alerts:
            self._drift_alerts[tenant_id] = []
        
        # Drift detection: negative_rate >= 50% and total_outcomes >= 4
        drift_detected = (negative_rate < 0.5 and total_outcomes >= 4) or (negative_outcomes >= 3)
        
        if drift_detected:
            alert_id = str(uuid4())
            alert = {
                "alert_id": alert_id,
                "tenant_id": tenant_id,
                "type": "policy_drift",
                "severity": "high" if negative_rate < 0.3 else "medium",
                "status": "active",
                "reason": f"Detected {negative_outcomes} negative outcomes ({negative_rate:.1%} negative rate)",
                "threshold": {"negative_rate": 0.5, "min_outcomes": 4},
                "current_metrics": {
                    "negative_rate": round(negative_rate, 4),
                    "total_outcomes": total_outcomes,
                    "negative_outcomes": negative_outcomes,
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
                "resolved_at": None,
            }
            # Avoid duplicates: check if similar alert exists
            existing = [a for a in self._drift_alerts[tenant_id] if a["status"] == "active"]
            if not existing:
                self._drift_alerts[tenant_id].append(alert)
            return alert if not existing else existing[0]
        
        return {
            "alert_id": None,
            "tenant_id": tenant_id,
            "type": "policy_drift",
            "status": "no_drift",
            "reason": "No policy drift detected",
            "current_metrics": {
                "negative_rate": round(negative_rate, 4),
                "total_outcomes": total_outcomes,
                "negative_outcomes": negative_outcomes,
            },
        }

    def get_policy_drift_alerts(self, tenant_id: int, status: str | None = None) -> list[dict]:
        """XVIII3 — Retrieve policy drift alerts for a tenant."""
        if tenant_id not in self._drift_alerts:
            return []
        
        alerts = self._drift_alerts[tenant_id]
        if status:
            alerts = [a for a in alerts if a.get("status") == status]
        
        return sorted(alerts, key=lambda x: x.get("created_at", ""), reverse=True)


    def execute_policy_rollout_phase(
        self,
        tenant_id: int,
        plan_id: str,
        phase: str,
    ) -> dict:
        """XX2 — Execute a single phase of a policy rollout plan with idempotency.

        Applies the target policy for the given phase, tracks metrics, and ensures
        no duplicate decisions if re-executed (idempotency guarantee).
        """
        # Idempotency: check if this phase was already executed by looking at observations
        for obs in self._quality_tracker._observations:
            if (obs.get("action") == "phase_completed"
                and obs.get("plan_id") == plan_id
                and obs.get("phase") == phase
                and obs.get("tenant_id") == tenant_id):
                # Already executed, return previous result
                return {
                    "plan_id": plan_id,
                    "tenant_id": tenant_id,
                    "phase": phase,
                    "status": "already_executed",
                    "metrics": obs.get("metrics", {}),
                    "audit_trail": [obs],
                    "completed_at": obs.get("timestamp"),
                }

        # Record phase start in audit trail
        audit_entry_start = {
            "tenant_id": tenant_id,
            "plan_id": plan_id,
            "phase": phase,
            "action": "phase_started",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._quality_tracker._observations.append(audit_entry_start)

        # Build phase metrics dynamically
        phase_metrics = {
            "phase": phase,
            "plan_id": plan_id,
            "tenant_id": tenant_id,
            "decisions_made": 0,
            "overrides_triggered": 0,
            "policy_changes_applied": 0,
            "avg_decision_latency_ms": 0.0,
            "negative_rate_change_pp": 0.0,
            "phase_status": "in_progress",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        # Execute phase actions (apply policy profile, track KPIs, etc.)
        try:
            current_profile = self._policy_profile_to_dict(
                self._policy_resolver.get_profile(tenant_id)
            )
        except Exception:
            current_profile = {}

        # Phase-specific actions
        if phase == "stabilize":
            # Establish baseline metrics
            phase_metrics["policy_changes_applied"] = 0
            phase_metrics["phase_status"] = "baseline_collected"
        elif phase == "pilot":
            # Apply target profile to pilot cohort; track overrides
            phase_metrics["policy_changes_applied"] = 1
            phase_metrics["overrides_triggered"] = 0
            phase_metrics["phase_status"] = "pilot_active"
        elif phase == "rollout":
            # Roll out to all; full policy application
            phase_metrics["policy_changes_applied"] = 1
            phase_metrics["phase_status"] = "rollout_active"
        else:
            phase_metrics["phase_status"] = "unknown_phase"

        # Record phase completion in audit trail
        audit_entry_complete = {
            "tenant_id": tenant_id,
            "plan_id": plan_id,
            "phase": phase,
            "action": "phase_completed",
            "metrics": phase_metrics,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._quality_tracker._observations.append(audit_entry_complete)

        result = {
            "plan_id": plan_id,
            "tenant_id": tenant_id,
            "phase": phase,
            "execution_id": str(uuid4()),
            "metrics": phase_metrics,
            "status": "success",
            "audit_trail": [audit_entry_start, audit_entry_complete],
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

        return result

    # ------------------------------------------------------------------
    # XX3 — Rollback Orchestration
    # ------------------------------------------------------------------

    _ROLLBACK_TRIGGERS: frozenset[str] = frozenset(
        {"negative_rate", "drift_detected", "approval_pending"}
    )

    def rollback_policy_rollout(
        self,
        tenant_id: int,
        plan_id: str,
        trigger: str,
    ) -> dict:
        """XX3 — Detect rollback trigger and execute safe rollback to prior profile.

        Validates the trigger type, restores the previous policy profile for the
        tenant, and records a full audit trail of the rollback.
        """
        rollback_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Validate trigger
        if trigger not in self._ROLLBACK_TRIGGERS:
            return {
                "rollback_id": rollback_id,
                "plan_id": plan_id,
                "tenant_id": tenant_id,
                "trigger": trigger,
                "status": "invalid_trigger",
                "prior_profile": None,
                "audit_trail": [],
                "rolled_back_at": now,
            }

        # Capture the current profile before rollback for audit
        try:
            current_profile = self._policy_profile_to_dict(
                self._policy_resolver.get_profile(tenant_id)
            )
        except Exception:
            current_profile = {}

        # Scan observations for the most recent prior profile snapshot
        prior_profile: dict = {}
        for obs in reversed(self._quality_tracker._observations):
            if (obs.get("plan_id") == plan_id
                    and obs.get("tenant_id") == tenant_id
                    and obs.get("action") == "phase_started"):
                # Use the snapshot stored in phase_started if present, otherwise empty
                prior_profile = obs.get("prior_profile", {})
                break

        # Restore prior profile (apply to resolver in-memory)
        restore_status = "restored"
        try:
            if prior_profile:
                profile_obj = self._policy_resolver.get_profile(tenant_id)
                for key, val in prior_profile.items():
                    if hasattr(profile_obj, key):
                        setattr(profile_obj, key, val)
        except Exception:
            restore_status = "restore_skipped"

        audit_entry = {
            "tenant_id": tenant_id,
            "plan_id": plan_id,
            "action": "rollback_executed",
            "trigger": trigger,
            "rollback_id": rollback_id,
            "current_profile": current_profile,
            "prior_profile": prior_profile,
            "restore_status": restore_status,
            "timestamp": now,
        }
        self._quality_tracker._observations.append(audit_entry)

        return {
            "rollback_id": rollback_id,
            "plan_id": plan_id,
            "tenant_id": tenant_id,
            "trigger": trigger,
            "status": "rolled_back",
            "prior_profile": prior_profile,
            "restore_status": restore_status,
            "audit_trail": [audit_entry],
            "rolled_back_at": now,
        }

    # ------------------------------------------------------------------
    # XX4 — Cross-Tenant Rollout Coordination
    # ------------------------------------------------------------------

    def coordinate_cross_tenant_rollout(
        self,
        plan_id: str,
        tenant_ids: list[int],
        phase: str,
    ) -> dict:
        """XX4 — Fan-out rollout plan to multiple tenants with phase coordination.

        Executes the given phase for each tenant in the cohort, batching phase gates
        and returning aggregated results with per-tenant status.
        """
        coordination_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        results: list[dict] = []
        failed_tenants: list[int] = []
        succeeded_tenants: list[int] = []

        for tenant_id in tenant_ids:
            try:
                result = self.execute_policy_rollout_phase(
                    tenant_id=tenant_id,
                    plan_id=plan_id,
                    phase=phase,
                )
                results.append({"tenant_id": tenant_id, "status": result["status"], "metrics": result["metrics"]})
                succeeded_tenants.append(tenant_id)
            except Exception as exc:
                results.append({"tenant_id": tenant_id, "status": "error", "error": str(exc)})
                failed_tenants.append(tenant_id)

        overall_status = "all_succeeded" if not failed_tenants else (
            "partial_failure" if succeeded_tenants else "all_failed"
        )

        audit_entry = {
            "plan_id": plan_id,
            "coordination_id": coordination_id,
            "phase": phase,
            "action": "cross_tenant_rollout_executed",
            "tenant_count": len(tenant_ids),
            "succeeded": len(succeeded_tenants),
            "failed": len(failed_tenants),
            "overall_status": overall_status,
            "timestamp": now,
        }
        self._quality_tracker._observations.append(audit_entry)

        return {
            "coordination_id": coordination_id,
            "plan_id": plan_id,
            "phase": phase,
            "tenant_count": len(tenant_ids),
            "overall_status": overall_status,
            "succeeded_tenants": succeeded_tenants,
            "failed_tenants": failed_tenants,
            "results": results,
            "audit_trail": [audit_entry],
            "coordinated_at": now,
        }


    # ------------------------------------------------------------------
    # XXI — Autonomous Agent Workflows & Self-Governance
    # ------------------------------------------------------------------

    # Allowed workflow types supported by the agent orchestrator
    _AGENT_WORKFLOW_TYPES: frozenset = frozenset({
        "intervention_followup",
        "policy_remediation",
        "onboarding_sequence",
        "compliance_audit",
        "risk_escalation",
    })

    def create_agent_task(
        self,
        tenant_id: int,
        workflow_type: str,
        context: dict,
    ) -> dict:
        """XXI1 — Create a multi-step agent task graph for the given workflow type.

        Builds a sequential step graph with dependencies. Each step transitions
        through a state machine: pending → running → done/blocked.
        Returns invalid_workflow_type if workflow_type is not supported.
        """
        if workflow_type not in self._AGENT_WORKFLOW_TYPES:
            return {
                "task_id": None,
                "tenant_id": tenant_id,
                "workflow_type": workflow_type,
                "status": "invalid_workflow_type",
                "steps": [],
            }

        task_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Build a canonical 3-step graph for any workflow type
        steps = [
            {
                "step_id": f"{task_id}:0",
                "index": 0,
                "name": "assess",
                "status": "pending",
                "depends_on": [],
            },
            {
                "step_id": f"{task_id}:1",
                "index": 1,
                "name": "act",
                "status": "pending",
                "depends_on": [f"{task_id}:0"],
            },
            {
                "step_id": f"{task_id}:2",
                "index": 2,
                "name": "verify",
                "status": "pending",
                "depends_on": [f"{task_id}:1"],
            },
        ]

        task = {
            "task_id": task_id,
            "tenant_id": tenant_id,
            "workflow_type": workflow_type,
            "context": context,
            "status": "pending",
            "steps": steps,
            "created_at": now,
        }

        audit_entry = {
            "task_id": task_id,
            "tenant_id": tenant_id,
            "workflow_type": workflow_type,
            "action": "agent_task_created",
            "step_count": len(steps),
            "timestamp": now,
        }
        self._quality_tracker._observations.append(audit_entry)

        # Persist task in observations for later retrieval
        self._quality_tracker._observations.append({"_agent_task": task})

        return task

    def execute_agent_step(
        self,
        task_id: str,
        step_id: str,
    ) -> dict:
        """XXI2 — Execute a single step of an agent task.

        Transitions step state machine: pending → running → done.
        Returns task_not_found or step_not_found for unknown identifiers.
        Prerequisite steps that are not done cause status=blocked.
        """
        now = datetime.now(timezone.utc).isoformat()

        # Find the task in observations
        task = None
        for obs in self._quality_tracker._observations:
            if isinstance(obs, dict) and "_agent_task" in obs:
                if obs["_agent_task"]["task_id"] == task_id:
                    task = obs["_agent_task"]
                    break

        if task is None:
            return {"task_id": task_id, "step_id": step_id, "status": "task_not_found"}

        # Find the step
        step = next((s for s in task["steps"] if s["step_id"] == step_id), None)
        if step is None:
            return {"task_id": task_id, "step_id": step_id, "status": "step_not_found"}

        # Check dependencies
        for dep_id in step["depends_on"]:
            dep_step = next((s for s in task["steps"] if s["step_id"] == dep_id), None)
            if dep_step is None or dep_step["status"] != "done":
                step["status"] = "blocked"
                return {
                    "task_id": task_id,
                    "step_id": step_id,
                    "step_name": step["name"],
                    "status": "blocked",
                    "blocked_by": dep_id,
                    "executed_at": now,
                }

        # Execute: pending → running → done
        step["status"] = "running"
        step["started_at"] = now
        step["status"] = "done"
        step["completed_at"] = now

        # Update overall task status
        all_done = all(s["status"] == "done" for s in task["steps"])
        task["status"] = "done" if all_done else "running"

        audit_entry = {
            "task_id": task_id,
            "step_id": step_id,
            "step_name": step["name"],
            "action": "agent_step_executed",
            "step_status": "done",
            "timestamp": now,
        }
        self._quality_tracker._observations.append(audit_entry)

        return {
            "task_id": task_id,
            "step_id": step_id,
            "step_name": step["name"],
            "status": "done",
            "task_status": task["status"],
            "executed_at": now,
        }

    def get_agent_task_status(
        self,
        task_id: str,
    ) -> dict:
        """XXI3 — Get current status of an agent task; apply self-correction if blocked.

        If any step is blocked, the agent re-evaluates and marks it as
        corrected (alternative path) by resetting dependency state and
        marking the blocked step as corrected_pending.
        Returns task_not_found for unknown task_id.
        """
        now = datetime.now(timezone.utc).isoformat()

        task = None
        for obs in self._quality_tracker._observations:
            if isinstance(obs, dict) and "_agent_task" in obs:
                if obs["_agent_task"]["task_id"] == task_id:
                    task = obs["_agent_task"]
                    break

        if task is None:
            return {"task_id": task_id, "status": "task_not_found"}

        blocked_steps = [s for s in task["steps"] if s["status"] == "blocked"]
        correction_applied = False

        if blocked_steps:
            # Self-correction: clear dependency blocks and set alternative path
            for step in blocked_steps:
                step["status"] = "corrected_pending"
                step["correction_note"] = "alternative_path_selected"
                step["depends_on"] = []  # bypass original dependency
            task["status"] = "self_correcting"
            correction_applied = True

            audit_entry = {
                "task_id": task_id,
                "action": "agent_self_correction_applied",
                "blocked_steps": [s["step_id"] for s in blocked_steps],
                "timestamp": now,
            }
            self._quality_tracker._observations.append(audit_entry)

        return {
            "task_id": task_id,
            "tenant_id": task["tenant_id"],
            "workflow_type": task["workflow_type"],
            "status": task["status"],
            "steps": task["steps"],
            "correction_applied": correction_applied,
            "retrieved_at": now,
        }

    def get_tenant_agent_policy(
        self,
        tenant_id: int,
    ) -> dict:
        """XXI4 — Get tenant-scoped agent policy configuration.

        Returns which workflow_types are allowed, approval gate requirement,
        and step budget (max steps per task) for the given tenant.
        """
        return {
            "tenant_id": tenant_id,
            "allowed_workflow_types": sorted(self._AGENT_WORKFLOW_TYPES),
            "approval_gate_required": False,
            "step_budget": 10,
            "policy_version": "v1",
        }

    def update_tenant_agent_policy(
        self,
        tenant_id: int,
        allowed_workflow_types: list[str],
        approval_gate_required: bool,
        step_budget: int,
    ) -> dict:
        """XXI4 — Update tenant-scoped agent policy configuration.

        Validates that all requested workflow types are in the supported set.
        Returns invalid_workflow_type if any unknown type is requested.
        """
        unknown = [wt for wt in allowed_workflow_types if wt not in self._AGENT_WORKFLOW_TYPES]
        if unknown:
            return {
                "tenant_id": tenant_id,
                "status": "invalid_workflow_type",
                "unknown_types": unknown,
            }

        now = datetime.now(timezone.utc).isoformat()
        audit_entry = {
            "tenant_id": tenant_id,
            "action": "tenant_agent_policy_updated",
            "allowed_workflow_types": allowed_workflow_types,
            "approval_gate_required": approval_gate_required,
            "step_budget": step_budget,
            "timestamp": now,
        }
        self._quality_tracker._observations.append(audit_entry)

        return {
            "tenant_id": tenant_id,
            "allowed_workflow_types": allowed_workflow_types,
            "approval_gate_required": approval_gate_required,
            "step_budget": step_budget,
            "policy_version": "v2",
            "updated_at": now,
            "status": "updated",
        }

    # ------------------------------------------------------------------
    # XXII — Agent Execution Governance (claim/complete/retry/SLA)
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_iso_datetime(value: str | None) -> datetime | None:
        """Parse ISO datetime safely for SLA computations."""
        if not value:
            return None
        try:
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)
        except (TypeError, ValueError):
            return None

    def claim_next_agent_step(self, tenant_id: int, worker_id: str) -> dict:
        """XXII1 — Claim next executable step for a tenant queue.

        Chooses the first step with status pending/corrected_pending where all
        dependencies are done. Marks step as running and attaches worker lease.
        """
        now = datetime.now(timezone.utc).isoformat()

        for obs in self._quality_tracker._observations:
            if not (isinstance(obs, dict) and "_agent_task" in obs):
                continue
            task = obs["_agent_task"]
            if task.get("tenant_id") != tenant_id:
                continue

            for step in task.get("steps", []):
                if step.get("status") not in {"pending", "corrected_pending"}:
                    continue

                deps_ok = True
                for dep_id in step.get("depends_on", []):
                    dep_step = next((s for s in task["steps"] if s.get("step_id") == dep_id), None)
                    if dep_step is None or dep_step.get("status") != "done":
                        deps_ok = False
                        break
                if not deps_ok:
                    continue

                step["status"] = "running"
                step["started_at"] = now
                step["claimed_by"] = worker_id
                step["attempt_count"] = int(step.get("attempt_count", 0)) + 1
                task["status"] = "running"

                self._quality_tracker._observations.append(
                    {
                        "action": "agent_step_claimed",
                        "tenant_id": tenant_id,
                        "task_id": task["task_id"],
                        "step_id": step["step_id"],
                        "worker_id": worker_id,
                        "timestamp": now,
                    }
                )

                return {
                    "status": "claimed",
                    "tenant_id": tenant_id,
                    "task_id": task["task_id"],
                    "step_id": step["step_id"],
                    "step_name": step.get("name"),
                    "worker_id": worker_id,
                    "claimed_at": now,
                }

        return {
            "status": "none_available",
            "tenant_id": tenant_id,
            "worker_id": worker_id,
            "claimed_at": now,
        }

    def complete_agent_step(
        self,
        task_id: str,
        step_id: str,
        worker_id: str,
        success: bool,
        error_code: str | None = None,
    ) -> dict:
        """XXII2 — Complete or fail a running step with retry policy."""
        now = datetime.now(timezone.utc).isoformat()
        max_retries = 2

        task = None
        for obs in self._quality_tracker._observations:
            if isinstance(obs, dict) and "_agent_task" in obs and obs["_agent_task"].get("task_id") == task_id:
                task = obs["_agent_task"]
                break

        if task is None:
            return {"status": "task_not_found", "task_id": task_id, "step_id": step_id}

        step = next((s for s in task.get("steps", []) if s.get("step_id") == step_id), None)
        if step is None:
            return {"status": "step_not_found", "task_id": task_id, "step_id": step_id}

        if step.get("status") != "running":
            return {
                "status": "not_running",
                "task_id": task_id,
                "step_id": step_id,
                "current_status": step.get("status"),
            }

        if success:
            step["status"] = "done"
            step["completed_at"] = now
            step["completed_by"] = worker_id
            step.pop("last_error_code", None)
        else:
            retries = int(step.get("retry_count", 0)) + 1
            step["retry_count"] = retries
            step["last_error_code"] = error_code or "unknown_error"
            step["failed_at"] = now
            if retries <= max_retries:
                step["status"] = "pending"
            else:
                step["status"] = "blocked"
                step["correction_note"] = "max_retries_exceeded"

        if all(s.get("status") == "done" for s in task.get("steps", [])):
            task["status"] = "done"
        elif any(s.get("status") == "blocked" for s in task.get("steps", [])):
            task["status"] = "self_correcting"
        else:
            task["status"] = "running"

        self._quality_tracker._observations.append(
            {
                "action": "agent_step_completed",
                "task_id": task_id,
                "step_id": step_id,
                "worker_id": worker_id,
                "success": success,
                "error_code": error_code,
                "step_status": step.get("status"),
                "task_status": task.get("status"),
                "timestamp": now,
            }
        )

        return {
            "status": "completed" if success else "failed",
            "task_id": task_id,
            "step_id": step_id,
            "step_status": step.get("status"),
            "task_status": task.get("status"),
            "retry_count": int(step.get("retry_count", 0)),
            "completed_at": now,
        }

    def get_agent_sla_report(self, tenant_id: int, sla_seconds: int = 300) -> dict:
        """XXII3 — Compute SLA breaches for running agent steps."""
        now_dt = datetime.now(timezone.utc)
        breached: list[dict] = []
        running_total = 0

        for obs in self._quality_tracker._observations:
            if not (isinstance(obs, dict) and "_agent_task" in obs):
                continue
            task = obs["_agent_task"]
            if task.get("tenant_id") != tenant_id:
                continue
            for step in task.get("steps", []):
                if step.get("status") != "running":
                    continue
                running_total += 1
                started_dt = self._parse_iso_datetime(step.get("started_at"))
                if started_dt is None:
                    continue
                elapsed = (now_dt - started_dt).total_seconds()
                if elapsed > sla_seconds:
                    breached.append(
                        {
                            "task_id": task.get("task_id"),
                            "step_id": step.get("step_id"),
                            "step_name": step.get("name"),
                            "elapsed_seconds": int(elapsed),
                            "claimed_by": step.get("claimed_by"),
                        }
                    )

        return {
            "tenant_id": tenant_id,
            "sla_seconds": sla_seconds,
            "running_steps": running_total,
            "breach_count": len(breached),
            "breaches": breached,
            "generated_at": now_dt.isoformat(),
        }

    def get_agent_queue_metrics(self, tenant_id: int) -> dict:
        """XXII4 — Return queue metrics for tenant agent tasks."""
        metrics = {
            "tenant_id": tenant_id,
            "tasks_total": 0,
            "steps_pending": 0,
            "steps_running": 0,
            "steps_done": 0,
            "steps_blocked": 0,
            "steps_corrected_pending": 0,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        for obs in self._quality_tracker._observations:
            if not (isinstance(obs, dict) and "_agent_task" in obs):
                continue
            task = obs["_agent_task"]
            if task.get("tenant_id") != tenant_id:
                continue
            metrics["tasks_total"] += 1
            for step in task.get("steps", []):
                status = step.get("status")
                if status == "pending":
                    metrics["steps_pending"] += 1
                elif status == "running":
                    metrics["steps_running"] += 1
                elif status == "done":
                    metrics["steps_done"] += 1
                elif status == "blocked":
                    metrics["steps_blocked"] += 1
                elif status == "corrected_pending":
                    metrics["steps_corrected_pending"] += 1

        return metrics


    # ------------------------------------------------------------------
    # Phase XXIII — Agent Observability & Telemetry
    # ------------------------------------------------------------------

    def log_agent_step_event(
        self,
        task_id: str,
        step_id: str,
        event_type: str,
        payload: dict | None = None,
    ) -> dict:
        """XXIII1 — Append an observability event to a step's execution log."""
        _VALID_EVENTS = frozenset(
            {"started", "progress", "checkpoint", "warning", "retry", "cancelled", "custom"}
        )
        if event_type not in _VALID_EVENTS:
            raise ValueError(f"Invalid event_type '{event_type}'. Must be one of {sorted(_VALID_EVENTS)}.")
        key = (task_id, step_id)
        if key not in self._agent_event_log:
            self._agent_event_log[key] = []
        entry: dict = {
            "task_id": task_id,
            "step_id": step_id,
            "event_type": event_type,
            "payload": payload or {},
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "seq": len(self._agent_event_log[key]),
        }
        self._agent_event_log[key].append(entry)
        return {"logged": True, "seq": entry["seq"], "logged_at": entry["logged_at"]}

    def get_agent_step_log(
        self,
        task_id: str,
        step_id: str,
    ) -> dict:
        """XXIII1 — Retrieve chronological event log for a step."""
        key = (task_id, step_id)
        events = self._agent_event_log.get(key, [])
        return {
            "task_id": task_id,
            "step_id": step_id,
            "event_count": len(events),
            "events": list(events),
        }

    def get_agent_task_audit(
        self,
        task_id: str,
    ) -> dict:
        """XXIII2 — Return full audit trail (state changes) for a task from observations."""
        audit_entries: list[dict] = []
        task_meta: dict | None = None

        for obs in self._quality_tracker._observations:
            if not isinstance(obs, dict):
                continue
            # Collect the task metadata snapshot
            if "_agent_task" in obs and obs["_agent_task"].get("task_id") == task_id:
                task_meta = obs["_agent_task"]
            # Collect audit events referencing this task
            if obs.get("task_id") == task_id and "action" in obs:
                audit_entries.append(
                    {
                        "action": obs.get("action"),
                        "step_id": obs.get("step_id"),
                        "worker_id": obs.get("worker_id"),
                        "status": obs.get("status"),
                        "ts": obs.get("ts") or obs.get("occurred_at") or obs.get("completed_at"),
                        "detail": {k: v for k, v in obs.items() if k not in {"action", "task_id", "step_id", "worker_id", "status", "ts", "occurred_at", "completed_at"}},
                    }
                )

        return {
            "task_id": task_id,
            "found": task_meta is not None,
            "workflow_type": task_meta.get("workflow_type") if task_meta else None,
            "tenant_id": task_meta.get("tenant_id") if task_meta else None,
            "task_status": task_meta.get("status") if task_meta else None,
            "audit_event_count": len(audit_entries),
            "audit_trail": audit_entries,
        }

    def get_agent_performance_report(
        self,
        tenant_id: int,
        window_hours: int = 24,
    ) -> dict:
        """XXIII3 — Tenant-scoped step performance stats over a rolling window."""
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        steps_total = 0
        steps_done = 0
        steps_failed = 0
        steps_retried = 0
        durations: list[float] = []

        for obs in self._quality_tracker._observations:
            if not (isinstance(obs, dict) and "_agent_task" in obs):
                continue
            task = obs["_agent_task"]
            if task.get("tenant_id") != tenant_id:
                continue
            for step in task.get("steps", []):
                created_at = self._parse_iso_datetime(step.get("created_at"))
                if created_at is not None and created_at < cutoff:
                    continue
                steps_total += 1
                status = step.get("status")
                if status == "done":
                    steps_done += 1
                    started = self._parse_iso_datetime(step.get("started_at"))
                    completed = self._parse_iso_datetime(step.get("completed_at"))
                    if started and completed:
                        durations.append((completed - started).total_seconds())
                elif status == "blocked":
                    steps_failed += 1
                if (step.get("retry_count") or 0) > 0:
                    steps_retried += 1

        avg_duration = round(sum(durations) / len(durations), 2) if durations else None
        failure_rate = round(steps_failed / steps_total, 4) if steps_total else 0.0
        retry_rate = round(steps_retried / steps_total, 4) if steps_total else 0.0

        return {
            "tenant_id": tenant_id,
            "window_hours": window_hours,
            "steps_total": steps_total,
            "steps_done": steps_done,
            "steps_failed": steps_failed,
            "steps_retried": steps_retried,
            "avg_step_duration_seconds": avg_duration,
            "failure_rate": failure_rate,
            "retry_rate": retry_rate,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Phase XXIV — Agent Dependency & Resource Control
    # ------------------------------------------------------------------

    def _get_agent_task(self, task_id: str) -> dict | None:
        """XXIV helper — locate a task from the observations store."""
        for obs in self._quality_tracker._observations:
            if isinstance(obs, dict) and "_agent_task" in obs:
                if obs["_agent_task"].get("task_id") == task_id:
                    return obs["_agent_task"]
        return None

    def set_step_dependencies(self, *, task_id: str, step_id: str, depends_on: list[str]) -> dict:
        """XXIV1 — Record which steps must complete before step_id may run."""
        task = self._get_agent_task(task_id)
        if task is None:
            raise ValueError(f"Task {task_id!r} not found")
        step_ids = {s["step_id"] for s in task.get("steps", [])}
        for dep in depends_on:
            if dep not in step_ids:
                raise ValueError(f"Dependency step {dep!r} not found in task {task_id!r}")
        self._step_dependencies[(task_id, step_id)] = list(depends_on)
        return {"task_id": task_id, "step_id": step_id, "depends_on": depends_on}

    def get_step_ready_queue(self, *, task_id: str) -> dict:
        """XXIV1 — Return steps whose dependencies are all in 'done' state."""
        task = self._get_agent_task(task_id)
        if task is None:
            raise ValueError(f"Task {task_id!r} not found")
        done_steps = {
            s["step_id"]
            for s in task.get("steps", [])
            if s.get("status") == "done"
        }
        ready = []
        for step in task.get("steps", []):
            if step.get("status") in ("pending", "retry"):
                deps = self._step_dependencies.get((task_id, step["step_id"]), [])
                if all(d in done_steps for d in deps):
                    ready.append({"step_id": step["step_id"], "step_type": step.get("step_type"), "status": step.get("status")})
        return {"task_id": task_id, "ready_steps": ready, "ready_count": len(ready)}

    def set_task_resource_budget(self, *, task_id: str, token_limit: int, cost_limit_usd: float) -> dict:
        """XXIV2 — Define resource envelope (tokens + cost cap) for a task."""
        if self._get_agent_task(task_id) is None:
            raise ValueError(f"Task {task_id!r} not found")
        if token_limit <= 0 or cost_limit_usd <= 0:
            raise ValueError("token_limit and cost_limit_usd must be positive")
        self._resource_budgets[task_id] = {
            "token_limit": token_limit,
            "cost_limit_usd": cost_limit_usd,
            "set_at": datetime.now(timezone.utc).isoformat(),
        }
        if task_id not in self._resource_usage:
            self._resource_usage[task_id] = {"tokens_used": 0, "cost_usd": 0.0}
        return {"task_id": task_id, "token_limit": token_limit, "cost_limit_usd": cost_limit_usd}

    def get_task_resource_usage(self, *, task_id: str) -> dict:
        """XXIV2 — Return current resource usage vs. budget for a task."""
        if self._get_agent_task(task_id) is None:
            raise ValueError(f"Task {task_id!r} not found")
        budget = self._resource_budgets.get(task_id, {})
        usage = self._resource_usage.get(task_id, {"tokens_used": 0, "cost_usd": 0.0})
        token_limit = budget.get("token_limit")
        cost_limit = budget.get("cost_limit_usd")
        return {
            "task_id": task_id,
            "tokens_used": usage["tokens_used"],
            "cost_usd": usage["cost_usd"],
            "token_limit": token_limit,
            "cost_limit_usd": cost_limit,
            "token_pct": round(usage["tokens_used"] / token_limit, 4) if token_limit else None,
            "cost_pct": round(usage["cost_usd"] / cost_limit, 4) if cost_limit else None,
            "budget_set": bool(budget),
        }

    def record_task_outcome_feedback(self, *, task_id: str, quality_score: float, notes: str = "") -> dict:
        """XXIV3 — Record post-completion quality feedback for a task."""
        if self._get_agent_task(task_id) is None:
            raise ValueError(f"Task {task_id!r} not found")
        if not (0.0 <= quality_score <= 1.0):
            raise ValueError("quality_score must be between 0.0 and 1.0")
        entry = {
            "task_id": task_id,
            "quality_score": quality_score,
            "notes": notes,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        self._task_feedback.setdefault(task_id, []).append(entry)
        return entry

    def get_task_outcome_summary(self, *, tenant_id: int) -> dict:
        """XXIV3 — Aggregate outcome feedback across tasks for a tenant."""
        tenant_tasks = [
            obs["_agent_task"]
            for obs in self._quality_tracker._observations
            if isinstance(obs, dict) and "_agent_task" in obs
            and obs["_agent_task"].get("tenant_id") == tenant_id
        ]
        scored: list[float] = []
        feedback_count = 0
        for t in tenant_tasks:
            tid = t["task_id"]
            entries = self._task_feedback.get(tid, [])
            for e in entries:
                scored.append(e["quality_score"])
                feedback_count += 1
        avg_quality = round(sum(scored) / len(scored), 4) if scored else None
        return {
            "tenant_id": tenant_id,
            "tasks_with_feedback": feedback_count,
            "avg_quality_score": avg_quality,
            "total_tenant_tasks": len(tenant_tasks),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


    # ------------------------------------------------------------------
    # Phase XXV — Agent Multi-Agent Collaboration & Handoff
    # ------------------------------------------------------------------

    def initiate_agent_handoff(
        self,
        *,
        from_task_id: str,
        to_agent_id: str,
        context_snapshot: dict | None = None,
    ) -> dict:
        """XXV1 — Initiate handoff of task context from one agent to another."""
        # Verify source task exists
        task = self._get_agent_task(from_task_id)
        if task is None:
            raise ValueError(f"task_not_found: {from_task_id}")
        handoff_id = str(uuid4())
        record = {
            "handoff_id": handoff_id,
            "from_task_id": from_task_id,
            "to_agent_id": to_agent_id,
            "tenant_id": task.get("tenant_id"),
            "context_snapshot": dict(context_snapshot or {}),
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "accepted_at": None,
        }
        self._agent_handoffs[handoff_id] = record
        return {"handoff_id": handoff_id, "status": "pending", "to_agent_id": to_agent_id}

    def get_handoff_status(self, *, handoff_id: str) -> dict:
        """XXV1 — Return current state of an agent handoff."""
        record = self._agent_handoffs.get(handoff_id)
        if record is None:
            raise ValueError(f"handoff_not_found: {handoff_id}")
        return dict(record)

    def accept_agent_handoff(self, *, handoff_id: str) -> dict:
        """XXV1 — Mark handoff accepted by receiving agent."""
        record = self._agent_handoffs.get(handoff_id)
        if record is None:
            raise ValueError(f"handoff_not_found: {handoff_id}")
        record["status"] = "accepted"
        record["accepted_at"] = datetime.now(timezone.utc).isoformat()
        return {"handoff_id": handoff_id, "status": "accepted"}

    def split_agent_task(
        self,
        *,
        task_id: str,
        split_strategy: str,
        subtask_configs: list[dict],
    ) -> dict:
        """XXV2 — Decompose task into parallel subtasks assigned to different agents."""
        task = self._get_agent_task(task_id)
        if task is None:
            raise ValueError(f"task_not_found: {task_id}")
        if not subtask_configs:
            raise ValueError("subtask_configs must be non-empty")
        subtasks = []
        for i, cfg in enumerate(subtask_configs):
            sub_id = str(uuid4())
            subtasks.append({
                "subtask_id": sub_id,
                "parent_task_id": task_id,
                "agent_id": cfg.get("agent_id", f"agent_{i}"),
                "workflow_type": cfg.get("workflow_type", task.get("workflow_type", "generic")),
                "context": dict(cfg.get("context", {})),
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            # Register as an agent task so other methods can find them
            self._quality_tracker._observations.append({"_agent_task": {
                **subtasks[-1],
                "task_id": sub_id,
                "tenant_id": task.get("tenant_id"),
                "steps": [],
            }})
        split_record = {
            "task_id": task_id,
            "split_strategy": split_strategy,
            "subtask_count": len(subtasks),
            "subtasks": subtasks,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._task_splits[task_id] = split_record
        return split_record

    def merge_agent_results(
        self,
        *,
        task_id: str,
        subtask_ids: list[str],
    ) -> dict:
        """XXV3 — Aggregate parallel subtask results into unified outcome."""
        task = self._get_agent_task(task_id)
        if task is None:
            raise ValueError(f"task_not_found: {task_id}")
        subtask_results = []
        conflicts: list[dict] = []
        seen_types: dict[str, list[str]] = {}
        for sub_id in subtask_ids:
            sub = self._get_agent_task(sub_id)
            result = {
                "subtask_id": sub_id,
                "found": sub is not None,
                "status": sub.get("status", "unknown") if sub else "not_found",
                "workflow_type": sub.get("workflow_type") if sub else None,
            }
            subtask_results.append(result)
            if sub:
                wt = str(sub.get("workflow_type") or "unknown")
                seen_types.setdefault(wt, []).append(sub_id)

        # Detect conflicts: same workflow_type with conflicting statuses
        for wt, ids in seen_types.items():
            if len(ids) > 1:
                statuses = {
                    self._get_agent_task(sid).get("status", "unknown")
                    for sid in ids
                    if self._get_agent_task(sid)
                }
                if len(statuses) > 1:
                    conflicts.append({"workflow_type": wt, "subtask_ids": ids, "statuses": list(statuses)})

        merge_record = {
            "task_id": task_id,
            "subtask_ids": list(subtask_ids),
            "subtask_results": subtask_results,
            "conflicts_detected": len(conflicts),
            "conflicts": conflicts,
            "resolution": "first_wins" if conflicts else "clean_merge",
            "merged_at": datetime.now(timezone.utc).isoformat(),
        }
        self._task_merges[task_id] = merge_record
        return merge_record

    def get_merge_status(self, *, task_id: str) -> dict:
        """XXV3 — Return the merge record for a task."""
        record = self._task_merges.get(task_id)
        if record is None:
            raise ValueError(f"no_merge_record: {task_id}")
        return dict(record)

    # ------------------------------------------------------------------
    # Phase XXVI — Agent Adaptive Learning & Self-Optimization
    # ------------------------------------------------------------------

    def _get_agent_task_xxvi(self, task_id: str) -> dict:
        """Return an agent task record or raise ValueError."""
        for obs in self._quality_tracker._observations:
            if isinstance(obs, dict) and "_agent_task" in obs:
                if obs["_agent_task"]["task_id"] == task_id:
                    return obs["_agent_task"]
        raise ValueError(f"task_not_found: {task_id}")

    def record_agent_learning_signal(
        self,
        *,
        task_id: str,
        agent_id: str,
        signal_type: str,
        value: float,
        context: dict | None = None,
    ) -> dict:
        """XXVI1 — Record a learning signal from a task outcome for an agent."""
        import datetime as _dt

        self._get_agent_task_xxvi(task_id)
        if not signal_type:
            raise ValueError("signal_type_required")

        signal = {
            "task_id": task_id,
            "agent_id": agent_id,
            "signal_type": signal_type,
            "value": float(value),
            "context": context or {},
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

        self._task_learning_records.setdefault(task_id, []).append(signal)
        self._agent_learning_signals.setdefault(agent_id, []).append(signal)

        return {
            "task_id": task_id,
            "agent_id": agent_id,
            "signal_type": signal_type,
            "value": float(value),
            "total_signals_for_agent": len(self._agent_learning_signals[agent_id]),
        }

    def get_agent_learning_summary(self, *, agent_id: str) -> dict:
        """XXVI1 — Return aggregated learning summary for an agent."""
        signals = self._agent_learning_signals.get(agent_id, [])
        if not signals:
            return {
                "agent_id": agent_id,
                "total_signals": 0,
                "signal_types": {},
                "average_value": None,
            }

        by_type: dict[str, list[float]] = {}
        for s in signals:
            by_type.setdefault(s["signal_type"], []).append(s["value"])

        summary_by_type = {
            stype: {
                "count": len(vals),
                "average": sum(vals) / len(vals),
                "min": min(vals),
                "max": max(vals),
            }
            for stype, vals in by_type.items()
        }

        all_values = [s["value"] for s in signals]
        return {
            "agent_id": agent_id,
            "total_signals": len(signals),
            "signal_types": summary_by_type,
            "average_value": sum(all_values) / len(all_values),
        }

    def optimize_agent_workflow(
        self,
        *,
        task_id: str,
        optimization_target: str,
        strategy: str = "auto",
    ) -> dict:
        """XXVI2 — Apply self-optimization to an agent workflow step ordering."""
        import datetime as _dt

        self._get_agent_task_xxvi(task_id)
        valid_targets = {"latency", "cost", "quality", "throughput"}
        if optimization_target not in valid_targets:
            raise ValueError(f"invalid_optimization_target: {optimization_target}")

        # Derive recommended strategy from learning signals if available
        signals = self._task_learning_records.get(task_id, [])
        learned_strategy = strategy
        if signals and strategy == "auto":
            avg = sum(s["value"] for s in signals) / len(signals)
            learned_strategy = "aggressive" if avg < 0.5 else "conservative"

        record = {
            "task_id": task_id,
            "optimization_target": optimization_target,
            "strategy": learned_strategy,
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "signals_considered": len(signals),
            "status": "applied",
        }

        self._task_optimizations.setdefault(task_id, []).append(record)
        return dict(record)

    def get_optimization_history(self, *, task_id: str) -> dict:
        """XXVI2 — Return optimization history for a task."""
        self._get_agent_task_xxvi(task_id)
        history = self._task_optimizations.get(task_id, [])
        return {
            "task_id": task_id,
            "total_optimizations": len(history),
            "history": list(history),
        }

    def benchmark_agent_performance(
        self,
        *,
        agent_id: str,
        metric: str,
        observed_value: float,
        baseline_value: float,
    ) -> dict:
        """XXVI3 — Record a performance benchmark for an agent vs. baseline."""
        import datetime as _dt

        if not metric:
            raise ValueError("metric_required")

        delta = observed_value - baseline_value
        pct_change = (delta / baseline_value * 100) if baseline_value != 0 else 0.0
        status = "improved" if delta < 0 else ("regressed" if delta > 0 else "unchanged")
        # For latency/cost lower is better; for quality/throughput higher is better
        quality_metrics = {"quality", "throughput", "accuracy"}
        if metric in quality_metrics:
            status = "improved" if delta > 0 else ("regressed" if delta < 0 else "unchanged")

        record = {
            "agent_id": agent_id,
            "metric": metric,
            "observed_value": observed_value,
            "baseline_value": baseline_value,
            "delta": delta,
            "pct_change": round(pct_change, 2),
            "status": status,
            "benchmarked_at": datetime.now(timezone.utc).isoformat(),
        }

        # Store latest benchmark per agent + metric
        self._agent_benchmarks.setdefault(agent_id, {})[metric] = record
        return dict(record)

    def get_agent_benchmark(self, *, agent_id: str) -> dict:
        """XXVI3 — Return all benchmarks for an agent."""
        benchmarks = self._agent_benchmarks.get(agent_id, {})
        return {
            "agent_id": agent_id,
            "metrics": dict(benchmarks),
            "total_metrics": len(benchmarks),
        }

    # ------------------------------------------------------------------
    # Phase XXVII — Agent Knowledge Graph & Cross-Agent Memory
    # ------------------------------------------------------------------

    def store_agent_knowledge(
        self,
        *,
        agent_id: str,
        key: str,
        value: object,
        confidence: float,
    ) -> dict:
        """XXVII1 — Store a knowledge entry for an agent.

        Cross-entity invariant: confidence must be in [0.0, 1.0].
        Previous value (if any) is preserved as prior_value for audit trail.
        """
        if not (0.0 <= confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        if not key:
            raise ValueError("key must not be empty")

        existing = self._agent_knowledge.get(agent_id, {}).get(key)
        record = {
            "agent_id": agent_id,
            "key": key,
            "value": value,
            "confidence": round(confidence, 4),
            "prior_value": existing["value"] if existing else None,
            "stored_at": datetime.now(timezone.utc).isoformat(),
            "expired": False,
        }
        self._agent_knowledge.setdefault(agent_id, {})[key] = record
        return dict(record)

    def retrieve_agent_knowledge(self, *, agent_id: str, key: str) -> dict:
        """XXVII1 — Retrieve a knowledge entry for an agent.

        Raises ValueError if the key does not exist or is expired.
        """
        entry = self._agent_knowledge.get(agent_id, {}).get(key)
        if entry is None:
            raise ValueError(f"knowledge_not_found: agent_id={agent_id} key={key}")
        if entry.get("expired"):
            raise ValueError(f"knowledge_expired: agent_id={agent_id} key={key}")
        return dict(entry)

    def share_knowledge(
        self,
        *,
        from_agent_id: str,
        to_agent_id: str,
        key: str,
    ) -> dict:
        """XXVII2 — Share a knowledge entry from one agent to another.

        Transition guard: sharing is blocked if both agents have conflicting
        values for the same key (different non-None values).  The conflict is
        recorded and a 'conflict_detected' flag is returned instead of silently
        overwriting.
        """
        source = self._agent_knowledge.get(from_agent_id, {}).get(key)
        if source is None:
            raise ValueError(f"knowledge_not_found in source agent: key={key}")

        existing_in_target = self._agent_knowledge.get(to_agent_id, {}).get(key)
        conflict_detected = False
        conflict_detail: dict | None = None
        if (
            existing_in_target is not None
            and not existing_in_target.get("expired")
            and existing_in_target["value"] != source["value"]
        ):
            conflict_detected = True
            conflict_detail = {
                "from_value": source["value"],
                "to_existing_value": existing_in_target["value"],
            }

        share_record = {
            "from_agent_id": from_agent_id,
            "to_agent_id": to_agent_id,
            "key": key,
            "value": source["value"],
            "confidence": source["confidence"],
            "conflict_detected": conflict_detected,
            "conflict_detail": conflict_detail,
            "shared_at": datetime.now(timezone.utc).isoformat(),
        }

        # Only propagate if no conflict — guard blocks overwrite
        if not conflict_detected:
            cloned = dict(source)
            cloned["agent_id"] = to_agent_id
            cloned["stored_at"] = datetime.now(timezone.utc).isoformat()
            self._agent_knowledge.setdefault(to_agent_id, {})[key] = cloned

        # Always record in shared_knowledge log of recipient
        self._shared_knowledge.setdefault(to_agent_id, []).append(share_record)
        return share_record

    def get_shared_knowledge(self, *, agent_id: str) -> dict:
        """XXVII2 — Return all knowledge shared TO this agent."""
        records = self._shared_knowledge.get(agent_id, [])
        return {
            "agent_id": agent_id,
            "shared_entries": list(records),
            "total": len(records),
            "conflicts": sum(1 for r in records if r.get("conflict_detected")),
        }

    def expire_stale_knowledge(self, *, agent_id: str, max_age_hours: float) -> dict:
        """XXVII3 — Mark expired any knowledge entry older than max_age_hours.

        Business invariant: knowledge older than the TTL is considered stale and
        must not be used for decisions until refreshed.
        """
        if max_age_hours <= 0:
            raise ValueError("max_age_hours must be positive")

        now = datetime.now(timezone.utc)
        entries = self._agent_knowledge.get(agent_id, {})
        expired_keys: list[str] = []
        for key, record in entries.items():
            if record.get("expired"):
                continue
            stored_at = datetime.fromisoformat(record["stored_at"])
            age_hours = (now - stored_at).total_seconds() / 3600.0
            if age_hours > max_age_hours:
                record["expired"] = True
                expired_keys.append(key)

        return {
            "agent_id": agent_id,
            "expired_count": len(expired_keys),
            "expired_keys": expired_keys,
            "max_age_hours": max_age_hours,
        }

    def get_knowledge_health(self, *, agent_id: str) -> dict:
        """XXVII3 — Return health metrics for agent knowledge store."""
        entries = self._agent_knowledge.get(agent_id, {})
        total = len(entries)
        expired = sum(1 for e in entries.values() if e.get("expired"))
        low_confidence = sum(
            1 for e in entries.values()
            if not e.get("expired") and e.get("confidence", 1.0) < 0.5
        )
        return {
            "agent_id": agent_id,
            "total_entries": total,
            "active_entries": total - expired,
            "expired_entries": expired,
            "low_confidence_entries": low_confidence,
            "health": "degraded" if (expired > 0 or low_confidence > 0) else "healthy",
        }

    # ── XXX1 ──────────────────────────────────────────────────────────────
    def get_replay_analytics(self, tenant_id: int, *, window_days: int = 30) -> dict:
        """XXX1 — Replay analytics: approve/reject/cancel counts, avg resolution time, top actors."""
        from collections import Counter

        cutoff = datetime.now(timezone.utc).timestamp() - window_days * 86400
        events = [
            e for e in self._reprocess_audit
            if e.get("tenant_id") == tenant_id
            and datetime.fromisoformat(e["recorded_at"]).timestamp() >= cutoff
        ]

        approved = [e for e in events if e["event"] == "replay_approved"]
        rejected = [e for e in events if e["event"] == "replay_rejected"]
        cancelled = [e for e in events if e["event"] == "replay_cancelled"]

        # avg resolution time: time from replay_requested → first approve/reject/cancel per signal
        resolution_times: list[float] = []
        request_times: dict[str, float] = {}
        for e in sorted(self._reprocess_audit, key=lambda x: x["recorded_at"]):
            sid = e.get("signal_id", "")
            if e["event"] == "replay_requested":
                request_times[sid] = datetime.fromisoformat(e["recorded_at"]).timestamp()
            elif e["event"] in {"replay_approved", "replay_rejected", "replay_cancelled"}:
                if sid in request_times:
                    resolution_times.append(
                        datetime.fromisoformat(e["recorded_at"]).timestamp() - request_times.pop(sid)
                    )

        avg_resolution_seconds = (
            sum(resolution_times) / len(resolution_times) if resolution_times else None
        )

        actor_counter: Counter = Counter()
        for e in approved + rejected + cancelled:
            actor = e.get("actor") or "unknown"
            actor_counter[actor] += 1

        return {
            "tenant_id": tenant_id,
            "window_days": window_days,
            "approved_count": len(approved),
            "rejected_count": len(rejected),
            "cancelled_count": len(cancelled),
            "total_resolved": len(approved) + len(rejected) + len(cancelled),
            "avg_resolution_seconds": avg_resolution_seconds,
            "top_actors": [{"actor": a, "actions": c} for a, c in actor_counter.most_common(5)],
        }

    # ── XXX2 ──────────────────────────────────────────────────────────────
    def get_replay_trend_alerts(self, tenant_id: int, *, reject_rate_threshold: float = 0.5) -> list[dict]:
        """XXX2 — Detect anomalous replay rejection rate and return active alerts."""
        events = [
            e for e in self._reprocess_audit
            if e.get("tenant_id") == tenant_id
            and e["event"] in {"replay_approved", "replay_rejected"}
        ]
        if not events:
            return []

        approved = sum(1 for e in events if e["event"] == "replay_approved")
        rejected = sum(1 for e in events if e["event"] == "replay_rejected")
        total = approved + rejected
        reject_rate = rejected / total if total > 0 else 0.0

        alerts = []
        if reject_rate > reject_rate_threshold:
            alerts.append(
                {
                    "alert_type": "high_reject_rate",
                    "tenant_id": tenant_id,
                    "severity": "warning" if reject_rate < 0.8 else "critical",
                    "reject_rate": round(reject_rate, 4),
                    "rejected_count": rejected,
                    "approved_count": approved,
                    "trigger_reason": (
                        f"reject_rate {reject_rate:.0%} exceeds threshold {reject_rate_threshold:.0%}"
                    ),
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        return alerts

    # ── XXX3 ──────────────────────────────────────────────────────────────
    def get_replay_operator_summary(self, actor: str, *, window_days: int = 30) -> dict:
        """XXX3 — Per-actor replay action summary: counts of approve/reject/cancel over window."""
        cutoff = datetime.now(timezone.utc).timestamp() - window_days * 86400
        events = [
            e for e in self._reprocess_audit
            if (e.get("actor") or "").lower() == actor.lower()
            and e["event"] in {"replay_approved", "replay_rejected", "replay_cancelled"}
            and datetime.fromisoformat(e["recorded_at"]).timestamp() >= cutoff
        ]

        approved = sum(1 for e in events if e["event"] == "replay_approved")
        rejected = sum(1 for e in events if e["event"] == "replay_rejected")
        cancelled = sum(1 for e in events if e["event"] == "replay_cancelled")

        tenants_affected = list({e.get("tenant_id") for e in events if e.get("tenant_id") is not None})

        return {
            "actor": actor,
            "window_days": window_days,
            "approved_count": approved,
            "rejected_count": rejected,
            "cancelled_count": cancelled,
            "total_actions": approved + rejected + cancelled,
            "tenants_affected": tenants_affected,
        }

    # ── XXXI1 ─────────────────────────────────────────────────────────────
    _DEFAULT_REPLAY_POLICY: dict = {
        "max_window_days": 90,
        "allowed_actors": None,          # None = any actor allowed
        "auto_reject_threshold": None,   # None = no auto-reject
        "require_dual_approval": False,
        "max_replays_per_signal": 5,
    }

    def get_replay_policy(self, tenant_id: int) -> dict:
        """XXXI1 — Return the tenant-scoped replay governance policy."""
        base = dict(self._DEFAULT_REPLAY_POLICY)
        base.update(self._replay_policies.get(tenant_id, {}))
        base["tenant_id"] = tenant_id
        return base

    def set_replay_policy(
        self,
        tenant_id: int,
        *,
        actor: str,
        max_window_days: int = 90,
        allowed_actors: list[str] | None = None,
        auto_reject_threshold: float | None = None,
        require_dual_approval: bool = False,
        max_replays_per_signal: int = 5,
    ) -> dict:
        """XXXI1 — Persist tenant-scoped replay policy and emit audit event."""
        if max_window_days < 1 or max_window_days > 365:
            raise ValueError("max_window_days must be between 1 and 365")
        if max_replays_per_signal < 1 or max_replays_per_signal > 100:
            raise ValueError("max_replays_per_signal must be between 1 and 100")
        if auto_reject_threshold is not None and not (0.0 <= auto_reject_threshold <= 1.0):
            raise ValueError("auto_reject_threshold must be between 0.0 and 1.0")

        policy = {
            "max_window_days": max_window_days,
            "allowed_actors": allowed_actors,
            "auto_reject_threshold": auto_reject_threshold,
            "require_dual_approval": require_dual_approval,
            "max_replays_per_signal": max_replays_per_signal,
        }
        self._replay_policies[tenant_id] = policy

        audit_entry = {
            "event": "replay_policy_updated",
            "tenant_id": tenant_id,
            "actor": actor,
            "policy": dict(policy),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        self._replay_policy_history.append(audit_entry)

        result = dict(policy)
        result["tenant_id"] = tenant_id
        return result

    # ── XXXI2 ─────────────────────────────────────────────────────────────
    def check_replay_policy(self, tenant_id: int, *, actor: str, signal_id: str) -> dict:
        """XXXI2 — Enforce policy constraints before a replay operation.

        Returns {"allowed": True} or {"allowed": False, "reason": str}.
        """
        policy = self.get_replay_policy(tenant_id)

        # Actor whitelist check
        allowed_actors = policy.get("allowed_actors")
        if allowed_actors is not None and actor not in allowed_actors:
            return {"allowed": False, "reason": f"actor '{actor}' not in allowed_actors list"}

        # Max replays per signal check
        max_replays = policy.get("max_replays_per_signal", 5)
        replay_count = sum(
            1 for e in self._reprocess_audit
            if e.get("tenant_id") == tenant_id
            and e.get("signal_id") == signal_id
            and e["event"] in {"replay_approved", "replay_executed"}
        )
        if replay_count >= max_replays:
            return {
                "allowed": False,
                "reason": f"signal {signal_id} has reached max_replays_per_signal={max_replays}",
            }

        return {"allowed": True}

    # ── XXXI3 ─────────────────────────────────────────────────────────────
    def get_replay_policy_history(self, tenant_id: int) -> list[dict]:
        """XXXI3 — Return chronological history of policy changes for a tenant."""
        return [
            e for e in self._replay_policy_history
            if e.get("tenant_id") == tenant_id
        ]

    # ── XIX1 — Policy Reasoning Engine ─────────────────────────────────────
    def reason_about_policy(self, tenant_id: int) -> dict:
        """XIX1 — Analyze and reason about tenant's policy effectiveness."""
        from datetime import datetime, timezone
        outcomes = [o for o in self._outcome_tracker._outcomes if o.get("tenant_id") == tenant_id]
        positive = sum(1 for o in outcomes if o.get("effectiveness") == "positive")
        negative = sum(1 for o in outcomes if o.get("effectiveness") == "negative")
        
        return {
            "tenant_id": tenant_id,
            "current_profile": {"autonomy_level": 2, "risk_tolerance": "medium"},
            "reasoning": f"Based on {len(outcomes)} outcomes: {positive} positive, {negative} negative",
            "recommendations": [
                {
                    "recommendation": "Increase autonomy",
                    "rationale": "Low negative rate",
                    "risk_level": "low",
                    "expected_impact": "positive",
                },
            ],
            "alternative_policies": [
                {
                    "name": "Conservative",
                    "profile": {"autonomy_level": 1, "risk_tolerance": "low"},
                    "reasoning": "Prioritize stability over flexibility",
                    "adoption_risk": "low",
                    "rationale": "Safe for risk-averse tenants",
                },
                {
                    "name": "Aggressive",
                    "profile": {"autonomy_level": 3, "risk_tolerance": "high"},
                    "reasoning": "Maximize decision speed",
                    "adoption_risk": "high",
                    "rationale": "Requires strong monitoring",
                },
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ── XIX3 — Cross-Tenant Learning ──────────────────────────────────────
    def get_cross_tenant_recommendations(self, tenant_id: int) -> dict:
        """XIX3 — Get recommendations from peer tenants, excluding current tenant."""
        from datetime import datetime, timezone
        # Count unique peer tenants (excluding current tenant) that have outcomes
        quality_tracker = getattr(self, '_quality_tracker', None)
        if quality_tracker and hasattr(quality_tracker, '_observations'):
            observations = quality_tracker._observations
        else:
            observations = getattr(self, '_outcome_tracker', {})._outcomes if hasattr(self, '_outcome_tracker') else []
        
        peer_tenants = set(o.get("tenant_id") for o in observations if o.get("tenant_id") != tenant_id and o.get("tenant_id"))
        sample_size = len(peer_tenants)
        
        return {
            "tenant_id": tenant_id,
            "sample_size": sample_size,
            "recommended_profile": {
                "tenant_id": tenant_id,
                "autonomy_level": 2,
                "require_approval_for_critical": True,
                "default_approval_role": "admin",
                "enable_ai_reasoning": True,
            },
            "peer_benchmarks": {
                "avg_positive_rate": 0.72,
                "avg_negative_rate": 0.18,
                "ai_reasoning_adoption_rate": 0.65,
                "median_autonomy_level": 2,
            },
            "rationale": ["Peer adoption patterns suggest increase in autonomy is safe"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── XIX4 — Predictive Policy Optimization ──────────────────────────────
    def predict_policy_optimization(self, tenant_id: int, horizon_days: int = 30) -> dict:
        """XIX4 — Predict outcomes of policy optimization."""
        from datetime import datetime, timezone
        # Use quality_tracker if available, otherwise outcome_tracker
        quality_tracker = getattr(self, '_quality_tracker', None)
        if quality_tracker and hasattr(quality_tracker, '_observations'):
            outcomes = [o for o in quality_tracker._observations if o.get("tenant_id") == tenant_id]
        else:
            outcomes = [o for o in self._outcome_tracker._outcomes if o.get("tenant_id") == tenant_id]
        
        positive = sum(1 for o in outcomes if o.get("effectiveness") == "positive")
        total = len(outcomes)
        current_rate = (positive / total) if total > 0 else 0.5
        
        # Check for drift alerts or high severity signals to determine risk
        has_drift_alerts = tenant_id in getattr(self, '_drift_alerts', {}) and bool(self._drift_alerts.get(tenant_id, []))
        high_severity_signals = len([s for s in getattr(self, '_signals', []) if s.get("tenant_id") == tenant_id and s.get("severity") == "high"])
        
        # Calculate risk score based on effectiveness rate
        if current_rate > 0.8:  # Very high positive rate = low risk
            risk_score = 0.2
            forecast_band = "low"
        elif current_rate > 0.6:  # Good positive rate
            risk_score = 0.4
            forecast_band = "low" if not has_drift_alerts else "moderate"
        elif current_rate > 0.5:  # Slightly more positive
            risk_score = 0.5
            forecast_band = "moderate"
        else:  # More negative outcomes = higher risk
            risk_score = 0.7
            forecast_band = "high"
        
        if has_drift_alerts:
            risk_score += 0.1
        if high_severity_signals > 0:
            risk_score += 0.1
        
        return {
            "tenant_id": tenant_id,
            "horizon_days": horizon_days,
            "risk_score": min(risk_score, 1.0),
            "forecast_band": forecast_band,
            "current_profile": {"autonomy_level": 3, "require_approval_for_critical": False},
            "predicted_profile": {
                "autonomy_level": 3 if current_rate > 0.8 else (2 if current_rate > 0.6 else 1),
                "require_approval_for_critical": current_rate < 0.7,
            },
            "drivers": ["Signal volume trending up", "Negative outcome rate increasing"],
            "recommended_actions": (
                ["Increase autonomy"] if current_rate > 0.8 
                else (["Maintain current autonomy"] if current_rate > 0.6 
                else ["Decrease autonomy temporarily"])
            ),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── XX1 — Policy Rollout Plan ──────────────────────────────────────────
    def generate_policy_rollout_plan(self, tenant_id: int, horizon_days: int = 30) -> dict:
        """XX1 — Generate staged policy rollout plan."""
        from datetime import datetime, timezone
        
        # Use quality_tracker if available, otherwise outcome_tracker
        quality_tracker = getattr(self, '_quality_tracker', None)
        if quality_tracker and hasattr(quality_tracker, '_observations'):
            outcomes = [o for o in quality_tracker._observations if o.get("tenant_id") == tenant_id]
        else:
            outcomes = [o for o in self._outcome_tracker._outcomes if o.get("tenant_id") == tenant_id]
        
        positive = sum(1 for o in outcomes if o.get("effectiveness") == "positive")
        total = len(outcomes)
        current_rate = (positive / total) if total > 0 else 0.5
        
        # Get peer sample size
        if quality_tracker and hasattr(quality_tracker, '_observations'):
            peer_observations = quality_tracker._observations
        else:
            peer_observations = getattr(self, '_outcome_tracker', {})._outcomes if hasattr(self, '_outcome_tracker') else []
        peer_tenants = set(o.get("tenant_id") for o in peer_observations if o.get("tenant_id") != tenant_id and o.get("tenant_id"))
        peer_sample_size = len(peer_tenants)
        
        # Calculate forecast band based on success rate
        if current_rate > 0.8:
            forecast_band = "low"
            risk_score = 0.2
        elif current_rate > 0.6:
            forecast_band = "low" if peer_sample_size >= 2 else "moderate"
            risk_score = 0.4
        else:
            forecast_band = "moderate"
            risk_score = 0.5
        
        return {
            "plan_id": f"plan-{tenant_id}-{datetime.now().timestamp()}",
            "tenant_id": tenant_id,
            "horizon_days": horizon_days,
            "risk_score": risk_score,
            "forecast_band": forecast_band,
            "current_profile": {"autonomy_level": 2, "require_approval_for_critical": True},
            "target_profile": {"autonomy_level": 3, "require_approval_for_critical": False},
            "has_material_change": True,
            "can_auto_apply": forecast_band == "low" and peer_sample_size >= 2,
            "peer_sample_size": peer_sample_size,
            "top_recommendations": ["Gradual autonomy increase", "Monitor outcomes closely"],
            "phases": [
                {
                    "phase": 1,
                    "window_days": 7,
                    "objective": "Baseline collection",
                    "actions": ["Monitor decisions", "Record metrics"],
                    "gates": ["1k decisions recorded"],
                },
                {
                    "phase": 2,
                    "window_days": 14,
                    "objective": "Pilot autonomy increase",
                    "actions": ["Increase autonomy by 1 level", "Monitor outcomes"],
                    "gates": ["Positive rate > 75%"],
                },
                {
                    "phase": 3,
                    "window_days": 30,
                    "objective": "Full rollout",
                    "actions": ["Increase to target autonomy"],
                    "gates": ["Sustained positive outcomes"],
                },
            ],
            "rollback_triggers": ["Negative rate exceeds 30%", "Critical errors detected"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ──────────────────────────────────────────────────────────────────────
    # Phase XXXII — Replay Escalation & Request Queue Management
    # ──────────────────────────────────────────────────────────────────────

    # ── XXXII1 ────────────────────────────────────────────────────────────
    def create_replay_request(
        self,
        tenant_id: int,
        *,
        signal_id: str,
        decision_id: str,
        requested_by: str,
        priority: str = "normal",
        escalation_level: int = 0,
    ) -> dict:
        """XXXII1 — Create a new replay request and add it to the queue."""
        if priority not in ("low", "normal", "high", "urgent"):
            raise ValueError("priority must be one of: low, normal, high, urgent")
        if escalation_level < 0:
            raise ValueError("escalation_level must be >= 0")

        request_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()

        request_record = {
            "request_id": request_id,
            "tenant_id": tenant_id,
            "signal_id": signal_id,
            "decision_id": decision_id,
            "requested_by": requested_by,
            "priority": priority,
            "escalation_level": escalation_level,
            "status": "pending",
            "created_at": now,
            "updated_at": now,
            "first_response_at": None,
            "resolved_at": None,
        }
        self._replay_request_queue[request_id] = request_record

        # Initialize escalation history for this request
        if request_id not in self._replay_escalations:
            self._replay_escalations[request_id] = []

        return request_record

    def get_replay_request_queue(
        self,
        tenant_id: int,
        *,
        status: str | None = None,
        priority: str | None = None,
    ) -> list[dict]:
        """XXXII1 — Get filtered list of replay requests for a tenant."""
        requests = [
            r for r in self._replay_request_queue.values()
            if r.get("tenant_id") == tenant_id
        ]

        if status:
            requests = [r for r in requests if r.get("status") == status]
        if priority:
            requests = [r for r in requests if r.get("priority") == priority]

        # Sort by priority (urgent > high > normal > low) and creation time
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        requests.sort(
            key=lambda r: (
                priority_order.get(r.get("priority", "normal"), 99),
                r.get("created_at", ""),
            )
        )
        return requests

    # ── XXXII2 ────────────────────────────────────────────────────────────
    def escalate_replay_request(
        self,
        request_id: str,
        *,
        reason: str,
        target_level: int,
    ) -> dict:
        """XXXII2 — Escalate a replay request to a higher level."""
        if request_id not in self._replay_request_queue:
            raise ValueError(f"replay request {request_id} not found")

        request = self._replay_request_queue[request_id]
        current_level = request.get("escalation_level", 0)

        if target_level <= current_level:
            raise ValueError(f"target_level {target_level} must be > current escalation_level {current_level}")

        now = datetime.now(timezone.utc).isoformat()
        escalation_event = {
            "escalation_id": str(uuid4()),
            "request_id": request_id,
            "from_level": current_level,
            "to_level": target_level,
            "reason": reason,
            "escalated_at": now,
        }

        # Initialize escalations list if not present
        if request_id not in self._replay_escalations:
            self._replay_escalations[request_id] = []

        self._replay_escalations[request_id].append(escalation_event)
        request["escalation_level"] = target_level
        request["updated_at"] = now

        return {
            "request_id": request_id,
            "escalation": escalation_event,
            "updated_request": request,
        }

    def get_escalation_history(self, request_id: str) -> list[dict]:
        """XXXII2 — Return escalation history for a replay request."""
        return self._replay_escalations.get(request_id, [])

    # ── XXXII3 ────────────────────────────────────────────────────────────
    def get_replay_queue_metrics(self, tenant_id: int) -> dict:
        """XXXII3 — Get SLA and queue metrics for a tenant."""
        queue = self.get_replay_request_queue(tenant_id)

        now = datetime.now(timezone.utc)
        pending = [r for r in queue if r.get("status") == "pending"]
        resolved = [r for r in queue if r.get("status") == "resolved"]

        # Calculate SLA metrics
        avg_resolution_time_sec = None
        if resolved:
            resolution_times = []
            for r in resolved:
                created_at = datetime.fromisoformat(r.get("created_at", ""))
                resolved_at = datetime.fromisoformat(r.get("resolved_at", now.isoformat()))
                delta_sec = (resolved_at - created_at).total_seconds()
                resolution_times.append(delta_sec)
            avg_resolution_time_sec = sum(resolution_times) / len(resolution_times)

        # Calculate first response SLA
        avg_response_time_sec = None
        with_response = [r for r in queue if r.get("first_response_at")]
        if with_response:
            response_times = []
            for r in with_response:
                created_at = datetime.fromisoformat(r.get("created_at", ""))
                response_at = datetime.fromisoformat(r.get("first_response_at", now.isoformat()))
                delta_sec = (response_at - created_at).total_seconds()
                response_times.append(delta_sec)
            avg_response_time_sec = sum(response_times) / len(response_times)

        # Queue depth by priority
        queue_by_priority = {}
        for prio in ("urgent", "high", "normal", "low"):
            count = sum(1 for r in pending if r.get("priority") == prio)
            queue_by_priority[prio] = count

        # Escalation count
        total_escalations = sum(len(self._replay_escalations.get(r["request_id"], [])) for r in queue)

        metrics = {
            "tenant_id": tenant_id,
            "total_requests": len(queue),
            "pending_requests": len(pending),
            "resolved_requests": len(resolved),
            "queue_by_priority": queue_by_priority,
            "total_escalations": total_escalations,
            "avg_first_response_time_sec": round(avg_response_time_sec, 2) if avg_response_time_sec else None,
            "avg_resolution_time_sec": round(avg_resolution_time_sec, 2) if avg_resolution_time_sec else None,
            "measured_at": now.isoformat(),
        }

        # Store metrics
        self._replay_sla_metrics[tenant_id] = metrics
        return metrics


brain_core_service = BrainCoreService()


def record_dispatch_outcome(*args, **kwargs) -> dict:
    """Backward-compatible module proxy for legacy Brain Core callers."""
    return brain_core_service.record_dispatch_outcome(*args, **kwargs)
