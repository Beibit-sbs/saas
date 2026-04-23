"""Phase XII-XII4: Model Evaluation service."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from app.modules.model_evaluation.schemas import (
    EvalMetricSchema,
    EvalRunCreateSchema,
    EvalRunReadSchema,
    EvalRunSubmitResultSchema,
    LeaderboardEntrySchema,
)

_RUNS: dict[int, list[dict[str, Any]]] = {}  # tenant_id → eval runs


def _tenant_store(tenant_id: int) -> list[dict[str, Any]]:
    return _RUNS.setdefault(tenant_id, [])


def _gen_run_id(tenant_id: int, model_name: str, ts: str) -> str:
    return hashlib.sha256(f"{tenant_id}:{model_name}:{ts}".encode()).hexdigest()[:16]


def create_eval_run(
    *,
    tenant_id: int,
    actor_id: str,
    payload: EvalRunCreateSchema,
) -> EvalRunReadSchema:
    ts = datetime.now(timezone.utc).isoformat()
    run_id = _gen_run_id(tenant_id, payload.model_name, ts)
    record: dict[str, Any] = {
        "run_id": run_id,
        "tenant_id": tenant_id,
        "model_name": payload.model_name,
        "eval_set_name": payload.eval_set_name,
        "metric_names": payload.metric_names,
        "status": "pending",
        "metrics": [],
        "notes": payload.notes,
        "created_by": actor_id,
        "created_at": ts,
        "completed_at": None,
    }
    _tenant_store(tenant_id).append(record)
    return _to_read(record)


def list_eval_runs(*, tenant_id: int) -> list[EvalRunReadSchema]:
    return [_to_read(r) for r in _tenant_store(tenant_id)]


def submit_results(
    *,
    tenant_id: int,
    run_id: str,
    payload: EvalRunSubmitResultSchema,
) -> EvalRunReadSchema | None:
    for record in _tenant_store(tenant_id):
        if record["run_id"] == run_id:
            record["metrics"] = [m.model_dump() for m in payload.metrics]
            record["status"] = "completed"
            record["completed_at"] = datetime.now(timezone.utc).isoformat()
            return _to_read(record)
    return None


def get_leaderboard(*, tenant_id: int, eval_set_name: str | None = None) -> list[LeaderboardEntrySchema]:
    store = _tenant_store(tenant_id)
    completed = [r for r in store if r["status"] == "completed"]
    if eval_set_name:
        completed = [r for r in completed if r["eval_set_name"] == eval_set_name]

    entries: list[LeaderboardEntrySchema] = []
    for record in completed:
        metrics = record.get("metrics", [])
        if not metrics:
            continue
        primary = metrics[0]
        entries.append(
            LeaderboardEntrySchema(
                rank=0,
                model_name=record["model_name"],
                eval_set_name=record["eval_set_name"],
                primary_metric=primary["metric_name"],
                primary_score=primary["value"],
                run_id=record["run_id"],
                completed_at=record.get("completed_at"),
            )
        )

    entries.sort(key=lambda e: e.primary_score, reverse=True)
    for i, entry in enumerate(entries, 1):
        entry.rank = i
    return entries


def _to_read(record: dict[str, Any]) -> EvalRunReadSchema:
    return EvalRunReadSchema(
        run_id=record["run_id"],
        model_name=record["model_name"],
        eval_set_name=record["eval_set_name"],
        status=record["status"],
        metrics=[EvalMetricSchema(**m) for m in record.get("metrics", [])],
        notes=record.get("notes"),
        created_by=record["created_by"],
        created_at=record["created_at"],
        completed_at=record.get("completed_at"),
    )
