from __future__ import annotations

from typing import Any

from app.platform.ai.recommendations.repository import AiRecommendationRepository
from app.platform.ai.recommendations.rule_catalog import evaluate_rules
from app.platform.ai.recommendations.schemas import CopilotRecommendationSchema
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
    ) -> list[CopilotRecommendationSchema]:
        """
        Evaluate deterministic rules against the retrieved context and log each
        resulting recommendation.  Returns the list of matching recommendations.
        """
        recommendations = evaluate_rules(retrieved_context)

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

        return recommendations


recommendation_service = AiRecommendationService()


def generate_recommendations(
    *,
    tenant_id: int,
    actor_id: str,
    question: str,
    query_type: str,
    retrieved_context: dict[str, Any],
    uow: UnitOfWork,
) -> list[CopilotRecommendationSchema]:
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
