from __future__ import annotations

from app.platform.education_graph import service as education_graph_service
from app.platform.events.schemas import OutboxEventRead
from app.platform.uow import UnitOfWork


class EducationGraphInferenceHandler:
    """Infer StudentSkill edges from domain events without bypassing service layer."""

    name = "education_graph_inference"

    def handle(self, event: OutboxEventRead, *, uow: UnitOfWork) -> dict[str, object]:
        result = education_graph_service.infer_from_event(event, uow=uow)
        return {
            "handler": self.name,
            **result,
        }
