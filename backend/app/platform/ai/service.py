from __future__ import annotations

from typing import Any

from app.platform.ai.query_types import AiCopilotQueryType
from app.platform.ai.repository import AiCopilotRepository
from app.platform.ai import retrieval
from app.platform.ai.recommendations.service import AiRecommendationService
from app.platform.uow import UnitOfWork


_SHARED_AI_COPILOT_REPOSITORY = AiCopilotRepository()
_VALID_ADMIN_ROLES = {"platform_admin", "institution_admin", "academic_admin"}


def _normalize_admin_role(raw: object) -> str:
    role = str(raw or "").strip().lower()
    if role in _VALID_ADMIN_ROLES:
        return role
    return "institution_admin"


class AiCopilotService:
    def __init__(
        self,
        repository: AiCopilotRepository | None = None,
        recommendation_service: AiRecommendationService | None = None,
    ) -> None:
        self._repository = repository or _SHARED_AI_COPILOT_REPOSITORY
        self._recommendation_service = recommendation_service or AiRecommendationService()

    def clear_ai_state(self) -> None:
        self._repository.clear_state()
        self._recommendation_service.clear_state()

    def classify_question(self, question: str) -> str:
        q = str(question or "").strip().lower()

        if not q:
            return AiCopilotQueryType.UNSUPPORTED.value
        if "student skills" in q or "skills profile" in q or "навыки студента" in q or "студент дағд" in q:
            return AiCopilotQueryType.STUDENT_SKILLS.value
        if ("missing skills" in q and "program" in q) or ("не хватает навыков" in q and "программ" in q):
            return AiCopilotQueryType.MISSING_SKILLS.value
        if (
            "recommended courses" in q
            or "recommend courses" in q
            or "рекоменду" in q and "курс" in q
            or "ұсын" in q and "курс" in q
        ):
            return AiCopilotQueryType.RECOMMENDED_COURSES.value
        if (
            "faculty context" in q
            or "faculty profile" in q
            or "advisor profile" in q
            or "teacher profile" in q
            or "контекст преподавателя" in q
            or "профиль преподавателя" in q
            or "контекст куратора" in q
            or "оқытушы контекст" in q
            or "мұғалім профил" in q
            or "faculty " in q
            or "advisor " in q
            or "teacher " in q
            or "преподавател" in q
            or "куратор " in q
            or "оқытушы " in q
            or "мұғалім " in q
        ):
            return AiCopilotQueryType.FACULTY_CONTEXT.value
        if (
            "student context" in q
            or "student profile" in q
            or "student " in q
            or "контекст студента" in q
            or "профиль студента" in q
            or "студент " in q
            or "оқушы " in q
        ) and not (
            "риск отчислен" in q
            or "на грани отчислен" in q
            or "expulsion risk" in q
            or "dropout risk" in q
            or "academic risk" in q
        ):
            return AiCopilotQueryType.STUDENT_CONTEXT.value
        if "kpi" in q or "summary" in q or "сводк" in q or "қорытынды" in q:
            return AiCopilotQueryType.KPI_OVERVIEW.value
        if "how many students" in q or "currently have" in q or "сколько студентов" in q or "қанша студент" in q:
            return AiCopilotQueryType.KPI_OVERVIEW.value
        if (
            "how many enrollments" in q
            or "enrollments were created" in q
            or "сколько зачислен" in q
            or "қанша тіркел" in q
        ):
            return AiCopilotQueryType.KPI_OVERVIEW.value
        if "how many grades" in q or "grades were submitted" in q or "сколько оцен" in q or "қанша баға" in q:
            return AiCopilotQueryType.KPI_OVERVIEW.value
        if ("automation" in q and ("failing" in q or "failed" in q)) or ("автоматизац" in q and "ошиб" in q):
            return AiCopilotQueryType.AUTOMATION_HEALTH.value
        if (
            "academic risk" in q
            or "at academic risk" in q
            or "академическ" in q and "риск" in q
            or "риск отчислен" in q
            or "на грани отчислен" in q
            or "expulsion risk" in q
            or "dropout risk" in q
        ):
            return AiCopilotQueryType.ACADEMIC_RISK.value
        if (
            "failed jobs" in q
            or "notifications failing" in q
            or "platform health" in q
            or "ошибки платформ" in q
            or "платформа" in q and "здоров" in q
        ):
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
        admin_role = self.resolve_admin_role(context=context)
        prompt_pack = self.build_prompt_pack(admin_role=admin_role, tenant_id=int(tenant_id), query_type=query_type)
        tenant_policy = self.build_tenant_policy_binding(admin_role=admin_role, tenant_id=int(tenant_id))
        audit_taxonomy = self.build_audit_taxonomy(query_type=query_type)

        with UnitOfWork() as uow:
            answer = self._build_answer(
                tenant_id=int(tenant_id),
                question=q,
                query_type=query_type,
                context=context,
                uow=uow,
            )
            answer["query_type"] = query_type
            answer["admin_prompt_pack"] = prompt_pack
            answer["tenant_policy_binding"] = tenant_policy
            answer["audit_taxonomy"] = audit_taxonomy
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

    def resolve_admin_role(self, *, context: dict[str, Any] | None) -> str:
        if isinstance(context, dict):
            return _normalize_admin_role(context.get("admin_role"))
        return "institution_admin"

    def build_prompt_pack(self, *, admin_role: str, tenant_id: int, query_type: str) -> dict[str, Any]:
        role = _normalize_admin_role(admin_role)
        prompt_key = f"admin_copilot.{role}.v1"
        if role == "platform_admin":
            scope = "cross_tenant_ops"
        elif role == "academic_admin":
            scope = "academic_scope"
        else:
            scope = "single_tenant_ops"
        return {
            "prompt_key": prompt_key,
            "admin_role": role,
            "tenant_id": int(tenant_id),
            "query_type": str(query_type),
            "scope": scope,
        }

    def build_tenant_policy_binding(self, *, admin_role: str, tenant_id: int) -> dict[str, Any]:
        role = _normalize_admin_role(admin_role)
        return {
            "binding_mode": "strict",
            "bound_tenant_id": int(tenant_id),
            "cross_tenant_allowed": role == "platform_admin",
            "admin_role": role,
        }

    def build_audit_taxonomy(self, *, query_type: str) -> dict[str, str]:
        qtype = str(query_type or AiCopilotQueryType.UNSUPPORTED.value)
        return {
            "domain": "platform_core.ai.copilot",
            "action": f"platform_core.ai.copilot.ask.{qtype}",
            "query_type": qtype,
        }

    def audit_action_for_query_type(self, query_type: str) -> str:
        return self.build_audit_taxonomy(query_type=query_type)["action"]

    def audit_action_for_question(self, question: str) -> str:
        query_type = self.classify_question(question)
        return self.audit_action_for_query_type(query_type)

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
                    "recommendations": [],
                }
            data = retrieval.retrieve_student_context(tenant_id=tenant_id, student_id=student_id, uow=uow)
        elif query_type == AiCopilotQueryType.FACULTY_CONTEXT.value:
            faculty_id = retrieval.extract_faculty_id(question, context)
            if not faculty_id:
                return {
                    "question": question,
                    "summary": "Faculty id is required for faculty context queries.",
                    "insights": [],
                    "sources": [],
                    "warnings": ["missing_faculty_id"],
                    "recommendations": [],
                }
            data = retrieval.retrieve_faculty_context(tenant_id=tenant_id, faculty_id=faculty_id, uow=uow)
        elif query_type == AiCopilotQueryType.STUDENT_SKILLS.value:
            data = retrieval.retrieve_student_skills_profile(
                tenant_id=tenant_id,
                question=question,
                context=context,
                uow=uow,
            )
        elif query_type == AiCopilotQueryType.MISSING_SKILLS.value:
            data = retrieval.retrieve_missing_skills_for_program(
                tenant_id=tenant_id,
                question=question,
                context=context,
                uow=uow,
            )
        elif query_type == AiCopilotQueryType.RECOMMENDED_COURSES.value:
            data = retrieval.retrieve_recommended_courses(
                tenant_id=tenant_id,
                question=question,
                context=context,
                uow=uow,
            )
        else:
            return {
                "question": question,
                "summary": "This question type is not supported yet.",
                "insights": [],
                "sources": [],
                "warnings": ["unsupported_query_type"],
                "recommendations": [],
            }

        recommendations, created_case_id = self._recommendation_service.generate_recommendations(
            tenant_id=tenant_id,
            actor_id="system",
            question=question,
            query_type=query_type,
            retrieved_context=dict(data),
            uow=uow,
        )

        return {
            "question": question,
            "summary": str(data.get("summary") or "No answer generated."),
            "insights": list(data.get("insights") or []),
            "sources": list(data.get("sources") or []),
            "warnings": list(data.get("warnings") or []),
            "recommendations": [r.model_dump() for r in recommendations],
            "created_intervention_case_id": created_case_id,
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


def audit_action_for_question(question: str) -> str:
    return copilot_service.audit_action_for_question(question)


def clear_ai_state() -> None:
    copilot_service.clear_ai_state()
