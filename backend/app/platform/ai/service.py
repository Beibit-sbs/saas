from __future__ import annotations

from typing import Any

from app.platform.ai.query_types import AiCopilotQueryType
from app.platform.ai.repository import AiCopilotRepository
from app.platform.ai import retrieval
from app.platform.uow import UnitOfWork


_SHARED_AI_COPILOT_REPOSITORY = AiCopilotRepository()


class AiCopilotService:
    def __init__(self, repository: AiCopilotRepository | None = None) -> None:
        self._repository = repository or _SHARED_AI_COPILOT_REPOSITORY

    def clear_ai_state(self) -> None:
        self._repository.clear_state()

    def classify_question(self, question: str) -> str:
        q = str(question or "").strip().lower()

        if not q:
            return AiCopilotQueryType.UNSUPPORTED.value
        if "student context" in q or "student profile" in q or "student " in q:
            return AiCopilotQueryType.STUDENT_CONTEXT.value
        if "kpi" in q or "summary" in q:
            return AiCopilotQueryType.KPI_OVERVIEW.value
        if "how many students" in q or "currently have" in q:
            return AiCopilotQueryType.KPI_OVERVIEW.value
        if "how many enrollments" in q or "enrollments were created" in q:
            return AiCopilotQueryType.KPI_OVERVIEW.value
        if "how many grades" in q or "grades were submitted" in q:
            return AiCopilotQueryType.KPI_OVERVIEW.value
        if "automation" in q and ("failing" in q or "failed" in q):
            return AiCopilotQueryType.AUTOMATION_HEALTH.value
        if "academic risk" in q or "at academic risk" in q:
            return AiCopilotQueryType.ACADEMIC_RISK.value
        if "failed jobs" in q or "notifications failing" in q or "platform health" in q:
            return AiCopilotQueryType.PLATFORM_HEALTH.value

        return AiCopilotQueryType.UNSUPPORTED.value

    def answer_question(
        self,
        *,
        tenant_id: int,
        actor_id: str,
        question: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        q = str(question or "").strip()
        query_type = self.classify_question(q)

        with UnitOfWork() as uow:
            answer = self._build_answer(
                tenant_id=int(tenant_id),
                question=q,
                query_type=query_type,
                context=context,
                uow=uow,
            )
            self._repository.log_query(
                tenant_id=int(tenant_id),
                actor_id=str(actor_id or "unknown"),
                question=q,
                query_type=query_type,
                retrieved_sources_json=list(answer.get("sources") or []),
                answer_json=answer,
                conn=uow.conn,
            )

        return answer

    def list_logs(self, *, tenant_id: int, limit: int = 100) -> list[dict[str, Any]]:
        with UnitOfWork() as uow:
            return self._repository.list_queries_for_tenant(
                tenant_id=int(tenant_id),
                limit=limit,
                conn=uow.conn,
            )

    def _build_answer(
        self,
        *,
        tenant_id: int,
        question: str,
        query_type: str,
        context: dict[str, Any] | None,
        uow: UnitOfWork,
    ) -> dict[str, Any]:
        if query_type == AiCopilotQueryType.KPI_OVERVIEW.value:
            if "latest kpi summary" in question.lower():
                data = retrieval.retrieve_latest_kpi_summary(tenant_id=tenant_id, uow=uow)
            else:
                data = retrieval.retrieve_kpi_overview(tenant_id=tenant_id, question=question, uow=uow)
        elif query_type == AiCopilotQueryType.AUTOMATION_HEALTH.value:
            data = retrieval.retrieve_automation_health(tenant_id=tenant_id, uow=uow)
        elif query_type == AiCopilotQueryType.PLATFORM_HEALTH.value:
            data = retrieval.retrieve_platform_health(tenant_id=tenant_id, uow=uow)
        elif query_type == AiCopilotQueryType.ACADEMIC_RISK.value:
            data = retrieval.retrieve_academic_risk(tenant_id=tenant_id, uow=uow)
        elif query_type == AiCopilotQueryType.STUDENT_CONTEXT.value:
            student_id = retrieval.extract_student_id(question, context)
            if not student_id:
                return {
                    "question": question,
                    "summary": "Student id is required for student context queries.",
                    "insights": [],
                    "sources": [],
                    "warnings": ["missing_student_id"],
                }
            data = retrieval.retrieve_student_context(tenant_id=tenant_id, student_id=student_id, uow=uow)
        else:
            return {
                "question": question,
                "summary": "This question type is not supported yet.",
                "insights": [],
                "sources": [],
                "warnings": ["unsupported_query_type"],
            }

        return {
            "question": question,
            "summary": str(data.get("summary") or "No answer generated."),
            "insights": list(data.get("insights") or []),
            "sources": list(data.get("sources") or []),
            "warnings": list(data.get("warnings") or []),
        }


copilot_service = AiCopilotService()


def answer_question(
    *,
    tenant_id: int,
    actor_id: str,
    question: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return copilot_service.answer_question(
        tenant_id=tenant_id,
        actor_id=actor_id,
        question=question,
        context=context,
    )


def list_logs(*, tenant_id: int, limit: int = 100) -> list[dict[str, Any]]:
    return copilot_service.list_logs(tenant_id=tenant_id, limit=limit)


def clear_ai_state() -> None:
    copilot_service.clear_ai_state()
