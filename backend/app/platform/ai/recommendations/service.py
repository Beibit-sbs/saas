from __future__ import annotations

from typing import Any

from app.platform.ai.interventions_automation import maybe_create_academic_risk_intervention_case
from app.platform.ai.recommendations.repository import AiRecommendationRepository
from app.platform.ai.recommendations.rule_catalog import evaluate_rules
from app.platform.ai.recommendations.schemas import CopilotRecommendationSchema
from app.platform.ai.query_types import AiCopilotQueryType
from app.platform.uow import UnitOfWork


_SHARED_RECOMMENDATION_REPOSITORY = AiRecommendationRepository()


class AiRecommendationService:
    def __init__(self, repository: AiRecommendationRepository | None = None) -> None:
        self._repository = repository or _SHARED_RECOMMENDATION_REPOSITORY

    def clear_state(self) -> None:
        self._repository.clear_state()

    def generate_recommendations(
        self,
        *,
        tenant_id: int,
        actor_id: str,
        question: str,
        query_type: str,
        retrieved_context: dict[str, Any],
        uow: UnitOfWork,
    ) -> tuple[list[CopilotRecommendationSchema], int | None]:
        """
        Evaluate deterministic rules against the retrieved context and log each
        resulting recommendation.  Returns the list of matching recommendations
        and the created intervention case ID (if any).
        """
        recommendations = evaluate_rules(retrieved_context)
        created_case_id: int | None = None

        for rec in recommendations:
            self._repository.log_recommendation(
                tenant_id=tenant_id,
                actor_id=actor_id,
                question=question,
                recommendation_type=rec.recommendation_type,
                context_json=retrieved_context,
                recommendation_json=rec.model_dump(),
                conn=uow.conn,
            )

        if query_type == AiCopilotQueryType.ACADEMIC_RISK.value and any(
            rec.recommendation_type == "expulsion_risk_escalation" for rec in recommendations
        ):
            result = maybe_create_academic_risk_intervention_case(
                conn=uow.conn,
                tenant_id=tenant_id,
                question=question,
                retrieved_context=retrieved_context,
            )
            if result:
                created_case_id = result.get("case_id")

        return recommendations, created_case_id


recommendation_service = AiRecommendationService()


def generate_recommendations(
    *,
    tenant_id: int,
    actor_id: str,
    question: str,
    query_type: str,
    retrieved_context: dict[str, Any],
    uow: UnitOfWork,
) -> tuple[list[CopilotRecommendationSchema], int | None]:
    return recommendation_service.generate_recommendations(
        tenant_id=tenant_id,
        actor_id=actor_id,
        question=question,
        query_type=query_type,
        retrieved_context=retrieved_context,
        uow=uow,
    )


def clear_recommendation_state() -> None:
    recommendation_service.clear_state()
