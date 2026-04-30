"""Phase XII-XII4: Model Evaluation service — module-level in-memory store."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from threading import Lock

from app.modules.model_evaluation.schemas import (
    EvalMetricSchema,
    EvalRunCreateSchema,
    EvalRunReadSchema,
    EvalRunSubmitResultSchema,
    LeaderboardEntrySchema,
)

# Module-level store — NOT cleared by clear_university_state()
_store: dict[str, dict] = {}  # run_id -> record
_store_lock = Lock()


def _gen_run_id(tenant_id: int, model_name: str, ts: str) -> str:
    return hashlib.sha256(f"{tenant_id}:{model_name}:{ts}".encode()).hexdigest()[:16]


def _row_to_read(row: dict) -> EvalRunReadSchema:
    metrics_raw = row.get("metrics") or []
    return EvalRunReadSchema(
        run_id=str(row["run_id"]),
        model_name=str(row["model_name"]),
        eval_set_name=str(row["eval_set_name"]),
        status=str(row.get("status", "pending")),
        metrics=[EvalMetricSchema(**m) for m in metrics_raw],
        notes=row.get("notes"),
        created_by=str(row.get("created_by", "")),
        created_at=str(row.get("created_at", "")),
        completed_at=row.get("completed_at"),
    )


def create_eval_run(
    *,
    tenant_id: int,
    actor_id: str,
    payload: EvalRunCreateSchema,
) -> EvalRunReadSchema:
    ts = datetime.now(timezone.utc).isoformat()
    run_id = _gen_run_id(tenant_id, payload.model_name, ts)
    record = {
        "run_id": run_id,
        "tenant_id": tenant_id,
        "model_name": payload.model_name,
        "eval_set_name": payload.eval_set_name,
        "metric_names": list(payload.metric_names or []),
        "status": "pending",
        "metrics": [],
        "notes": payload.notes,
        "created_by": actor_id,
        "created_at": ts,
        "completed_at": None,
    }
    with _store_lock:
        _store[run_id] = record
    return _row_to_read(record)


def list_eval_runs(*, tenant_id: int) -> list[EvalRunReadSchema]:
    with _store_lock:
        rows = [r for r in _store.values() if r.get("tenant_id") == tenant_id]
    return [_row_to_read(r) for r in rows]


def submit_results(
    *,
    tenant_id: int,
    run_id: str,
    payload: EvalRunSubmitResultSchema,
) -> EvalRunReadSchema | None:
    with _store_lock:
        existing = _store.get(run_id)
        if existing is None or existing.get("tenant_id") != tenant_id:
            return None
        existing["metrics"] = [m.model_dump() for m in payload.metrics]
        existing["status"] = "completed"
        existing["completed_at"] = datetime.now(timezone.utc).isoformat()
        updated = dict(existing)
    return _row_to_read(updated)


def get_leaderboard(*, tenant_id: int, eval_set_name: str | None = None) -> list[LeaderboardEntrySchema]:
    with _store_lock:
        rows = [r for r in _store.values() if r.get("tenant_id") == tenant_id]
    completed = [r for r in rows if str(r.get("status")) == "completed"]
    if eval_set_name:
        completed = [r for r in completed if str(r.get("eval_set_name")) == eval_set_name]

    entries: list[LeaderboardEntrySchema] = []
    for row in completed:
        metrics = row.get("metrics") or []
        if not metrics:
            continue
        primary = metrics[0]
        entries.append(
            LeaderboardEntrySchema(
                rank=0,
                model_name=str(row["model_name"]),
                eval_set_name=str(row["eval_set_name"]),
                primary_metric=primary["metric_name"],
                primary_score=primary["value"],
                run_id=str(row["run_id"]),
                completed_at=row.get("completed_at"),
            )
        )

    entries.sort(key=lambda e: e.primary_score, reverse=True)
    for i, entry in enumerate(entries, 1):
        entry.rank = i
    return entries
