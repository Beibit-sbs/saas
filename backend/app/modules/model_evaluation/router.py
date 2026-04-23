"""Phase XII-XII4: Model Evaluation router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.modules.model_evaluation.schemas import (
    EvalRunCreateSchema,
    EvalRunReadSchema,
    EvalRunSubmitResultSchema,
    LeaderboardEntrySchema,
)
from app.modules.model_evaluation.service import (
    create_eval_run,
    get_leaderboard,
    list_eval_runs,
    submit_results,
)
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/model-evaluation", tags=["model-evaluation"])


@router.get("/health")
def health_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("model_evaluation.read"))],
) -> dict[str, str]:
    return {"status": "ok", "module": "model_evaluation", "phase": "xii4"}


@router.post("/runs", response_model=EvalRunReadSchema, status_code=201)
def create_run_endpoint(
    payload: EvalRunCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("model_evaluation.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> EvalRunReadSchema:
    return create_eval_run(
        tenant_id=int(tenant["id"]),
        actor_id=actor,
        payload=payload,
    )


@router.get("/runs", response_model=list[EvalRunReadSchema])
def list_runs_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("model_evaluation.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> list[EvalRunReadSchema]:
    return list_eval_runs(tenant_id=int(tenant["id"]))


@router.post("/runs/{run_id}/results", response_model=EvalRunReadSchema)
def submit_results_endpoint(
    run_id: str,
    payload: EvalRunSubmitResultSchema,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("model_evaluation.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> EvalRunReadSchema:
    result = submit_results(
        tenant_id=int(tenant["id"]),
        run_id=run_id,
        payload=payload,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Eval run not found")
    return result


@router.get("/leaderboard", response_model=list[LeaderboardEntrySchema])
def leaderboard_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("model_evaluation.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    eval_set_name: str | None = None,
) -> list[LeaderboardEntrySchema]:
    return get_leaderboard(
        tenant_id=int(tenant["id"]),
        eval_set_name=eval_set_name,
    )
