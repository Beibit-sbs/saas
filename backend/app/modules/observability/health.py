from __future__ import annotations
from app.core.db import get_raw_conn

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime, timezone
from pathlib import Path
import os
import time
from typing import Any

from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import (
    get_ai_provider_status,
    get_ops_probe_timeout_seconds,
    get_ops_scheduler_stale_seconds,
    get_ops_worker_stale_seconds,
)
from app.modules.observability.alerts import observe_dependency_state
from app.modules.observability.metrics import set_db_connections_active, set_redis_latency
from app.platform.runtime_state import get_scheduler_last_run, get_worker_heartbeat
from app.platform.uow import UnitOfWork


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dependency_payload(*, name: str, healthy: bool, critical: bool, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "status": "up" if healthy else "down",
        "healthy": bool(healthy),
        "critical": bool(critical),
        "details": details or {},
    }


def live_payload() -> dict[str, Any]:
    return {
        "status": "ok",
        "live": True,
        "service": "api",
        "timestamp": _now_iso(),
    }


def _postgres_dependency(app: FastAPI) -> dict[str, Any]:
    session_factory = getattr(app.state, "admissions_session_factory", None)
    engine = getattr(app.state, "admissions_engine", None)
    if session_factory is None or engine is None:
        set_db_connections_active(None)
        dependency = _dependency_payload(
            name="postgresql",
            healthy=False,
            critical=True,
            details={"reason": "database engine not configured"},
        )
        observe_dependency_state(component="postgresql", healthy=False, details=dependency["details"])
        return dependency

    probe_timeout_seconds = get_ops_probe_timeout_seconds()

    def _probe_postgres() -> dict[str, Any]:
        with session_factory() as session:
            session.execute(text("SELECT 1"))
        checked_out = int(engine.pool.checkedout()) if hasattr(engine.pool, "checkedout") else None
        details: dict[str, Any] = {
            "pool_class": engine.pool.__class__.__name__,
            "pool_status": engine.pool.status() if hasattr(engine.pool, "status") else "unknown",
        }
        if checked_out is not None:
            details["checked_out"] = checked_out
        details["probe_timeout_seconds"] = probe_timeout_seconds
        if checked_out is not None:
            set_db_connections_active(checked_out)
        return details

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            details = executor.submit(_probe_postgres).result(timeout=probe_timeout_seconds)
        observe_dependency_state(component="postgresql", healthy=True, details=details)
        return _dependency_payload(name="postgresql", healthy=True, critical=True, details=details)
    except FutureTimeoutError:
        set_db_connections_active(None)
        details = {
            "reason": "postgres probe timeout",
            "probe_timeout_seconds": probe_timeout_seconds,
        }
        observe_dependency_state(component="postgresql", healthy=False, details=details)
        return _dependency_payload(name="postgresql", healthy=False, critical=True, details=details)
    except Exception as exc:
        set_db_connections_active(None)
        details = {"reason": str(exc), "probe_timeout_seconds": probe_timeout_seconds}
        observe_dependency_state(component="postgresql", healthy=False, details=details)
        return _dependency_payload(name="postgresql", healthy=False, critical=True, details=details)


def _migrations_dependency(app: FastAPI) -> dict[str, Any]:
    session_factory = getattr(app.state, "admissions_session_factory", None)
    if session_factory is None:
        return _dependency_payload(
            name="migrations",
            healthy=False,
            critical=True,
            details={"reason": "database session factory unavailable"},
        )

    probe_timeout_seconds = get_ops_probe_timeout_seconds()
    current_version = None
    expected_head = None
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        backend_root = Path(__file__).resolve().parents[3]
        alembic_cfg = Config(str(backend_root / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(backend_root / "alembic"))
        expected_head = ScriptDirectory.from_config(alembic_cfg).get_current_head()
    except Exception as exc:
        return _dependency_payload(
            name="migrations",
            healthy=False,
            critical=True,
            details={"reason": f"failed to resolve alembic head: {exc}"},
        )

    def _read_current_version() -> str | None:
        with session_factory() as session:
            return session.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar_one_or_none()

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            current_version = executor.submit(_read_current_version).result(timeout=probe_timeout_seconds)
    except FutureTimeoutError:
        return _dependency_payload(
            name="migrations",
            healthy=False,
            critical=True,
            details={
                "reason": "migrations probe timeout",
                "expected_head": expected_head,
                "probe_timeout_seconds": probe_timeout_seconds,
            },
        )
    except Exception as exc:
        return _dependency_payload(
            name="migrations",
            healthy=False,
            critical=True,
            details={"reason": f"failed to read alembic_version: {exc}", "expected_head": expected_head},
        )

    healthy = bool(current_version) and str(current_version) == str(expected_head)
    return _dependency_payload(
        name="migrations",
        healthy=healthy,
        critical=True,
        details={"current_version": current_version, "expected_head": expected_head},
    )


def _redis_dependency() -> dict[str, Any]:
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        set_redis_latency(None)
        details = {"reason": "REDIS_URL is not configured"}
        observe_dependency_state(component="redis", healthy=False, details=details)
        return _dependency_payload(name="redis", healthy=False, critical=True, details=details)

    try:
        import redis
    except Exception as exc:
        set_redis_latency(None)
        details = {"reason": f"redis client unavailable: {exc}"}
        observe_dependency_state(component="redis", healthy=False, details=details)
        return _dependency_payload(name="redis", healthy=False, critical=True, details=details)

    started = time.monotonic()
    try:
        client = redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=get_ops_probe_timeout_seconds(),
        )
        client.ping()
        latency_seconds = time.monotonic() - started
        set_redis_latency(latency_seconds)
        details = {"latency_ms": round(latency_seconds * 1000, 2)}
        observe_dependency_state(component="redis", healthy=True, details=details)
        return _dependency_payload(name="redis", healthy=True, critical=True, details=details)
    except Exception as exc:
        set_redis_latency(None)
        details = {"reason": str(exc)}
        observe_dependency_state(component="redis", healthy=False, details=details)
        return _dependency_payload(name="redis", healthy=False, critical=True, details=details)


def readiness_payload(app: FastAPI) -> dict[str, Any]:
    dependencies = {
        "postgresql": _postgres_dependency(app),
        "redis": _redis_dependency(),
        "migrations": _migrations_dependency(app),
    }
    for dependency in dependencies.values():
        observe_dependency_state(
            component=str(dependency.get("name", "unknown")),
            healthy=bool(dependency.get("healthy", False)),
            details=dict(dependency.get("details", {})),
        )
    pool_dependency = dependencies["postgresql"]
    dependencies["connection_pool"] = _dependency_payload(
        name="connection_pool",
        healthy=bool(pool_dependency["healthy"]),
        critical=True,
        details=dict(pool_dependency["details"]),
    )
    ready = all(bool(item["healthy"]) for item in dependencies.values() if bool(item["critical"]))
    return {
        "status": "ready" if ready else "not_ready",
        "ready": ready,
        "timestamp": _now_iso(),
        "dependencies": dependencies,
    }


def _parse_iso(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw))
    except Exception:
        return None


def _worker_dependency() -> dict[str, Any]:
    heartbeat = _parse_iso(get_worker_heartbeat())
    stale_seconds = get_ops_worker_stale_seconds()
    if heartbeat is None:
        return _dependency_payload(
            name="worker",
            healthy=False,
            critical=False,
            details={"reason": "worker heartbeat missing", "stale_seconds": stale_seconds},
        )
    age_seconds = max(0.0, (datetime.now(timezone.utc) - heartbeat).total_seconds())
    return _dependency_payload(
        name="worker",
        healthy=age_seconds <= stale_seconds,
        critical=False,
        details={"heartbeat_at": heartbeat.isoformat(), "age_seconds": round(age_seconds, 2), "stale_seconds": stale_seconds},
    )


def _scheduler_dependency() -> dict[str, Any]:
    scheduler_last_run = get_scheduler_last_run()
    heartbeat = _parse_iso((scheduler_last_run or {}).get("at") if isinstance(scheduler_last_run, dict) else None)
    stale_seconds = get_ops_scheduler_stale_seconds()
    if heartbeat is None:
        return _dependency_payload(
            name="scheduler",
            healthy=False,
            critical=False,
            details={"reason": "scheduler heartbeat missing", "stale_seconds": stale_seconds},
        )
    age_seconds = max(0.0, (datetime.now(timezone.utc) - heartbeat).total_seconds())
    return _dependency_payload(
        name="scheduler",
        healthy=age_seconds <= stale_seconds,
        critical=False,
        details={
            "last_run_at": heartbeat.isoformat(),
            "task_name": (scheduler_last_run or {}).get("task_name") if isinstance(scheduler_last_run, dict) else None,
            "age_seconds": round(age_seconds, 2),
            "stale_seconds": stale_seconds,
        },
    )


def _jobs_queue_dependency() -> dict[str, Any]:
    probe_timeout_seconds = get_ops_probe_timeout_seconds()

    def _read_queue_counts() -> dict[str, int]:
        with UnitOfWork() as uow:
            queued = int(uow.job_repository.count_by_status("queued", conn=uow.conn))
            failed = int(uow.job_repository.count_by_status("failed", conn=uow.conn))
            dead = int(uow.job_repository.count_dead_jobs(conn=uow.conn))
        return {"queued": queued, "failed": failed, "dead": dead}

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            details = executor.submit(_read_queue_counts).result(timeout=probe_timeout_seconds)
        return _dependency_payload(
            name="jobs_queue",
            healthy=True,
            critical=False,
            details=details,
        )
    except FutureTimeoutError:
        return _dependency_payload(
            name="jobs_queue",
            healthy=False,
            critical=False,
            details={"reason": "jobs_queue probe timeout", "probe_timeout_seconds": probe_timeout_seconds},
        )
    except Exception as exc:
        return _dependency_payload(
            name="jobs_queue",
            healthy=False,
            critical=False,
            details={"reason": str(exc)},
        )


def _ldap_dependency(app: FastAPI) -> dict[str, Any]:
    readiness = _postgres_dependency(app)
    if not readiness["healthy"]:
        return _dependency_payload(
            name="ldap",
            healthy=False,
            critical=True,
            details={"reason": "postgresql unavailable; cannot resolve enabled providers"},
        )

    try:
        from app.modules.identity.phase1_service import _decrypt_secret, _provider_uri
        from ldap3 import Connection, Server
    except Exception as exc:
        details = {"reason": f"ldap probe dependencies unavailable: {exc}"}
        observe_dependency_state(component="ldap", healthy=False, details=details)
        return _dependency_payload(name="ldap", healthy=False, critical=True, details=details)

    db_url = os.getenv("DATABASE_URL", "").strip().replace("postgresql+psycopg://", "postgresql://", 1)
    if not db_url:
        details = {"reason": "DATABASE_URL is not configured"}
        observe_dependency_state(component="ldap", healthy=False, details=details)
        return _dependency_payload(name="ldap", healthy=False, critical=True, details=details)

    provider_statuses: list[dict[str, Any]] = []
    healthy = True
    try:
        with get_raw_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT p.id, p.name, p.type, p.is_enabled, p.config_json, COALESCE(s.bind_password_enc, '')
                      FROM app_identity_providers p
                 LEFT JOIN app_identity_provider_secrets s ON s.provider_id = p.id AND s.tenant_id = p.tenant_id
                     WHERE p.is_enabled = TRUE AND p.type IN ('ldap', 'ad')
                    """
                )
                rows = cur.fetchall() or []
        if not rows:
            details = {"status": "no_enabled_ldap_providers"}
            observe_dependency_state(component="ldap", healthy=True, details=details)
            return _dependency_payload(name="ldap", healthy=True, critical=True, details=details)

        for provider_id, provider_name, provider_type, _enabled, config_json, bind_password_enc in rows:
            config = config_json if isinstance(config_json, dict) else {}
            bind_password = _decrypt_secret(str(bind_password_enc or ""))
            if not bind_password:
                provider_statuses.append({
                    "provider_id": int(provider_id),
                    "provider_name": str(provider_name),
                    "provider_type": str(provider_type),
                    "status": "down",
                    "reason": "missing bind password",
                })
                healthy = False
                continue
            try:
                server = Server(
                    _provider_uri(config),
                    connect_timeout=int(config.get("timeout_seconds", get_ops_probe_timeout_seconds()) or get_ops_probe_timeout_seconds()),
                    use_ssl=bool(config.get("use_ssl", True)),
                )
                with Connection(server, user=str(config.get("bind_dn", "")), password=bind_password, auto_bind=True):
                    pass
                provider_statuses.append({
                    "provider_id": int(provider_id),
                    "provider_name": str(provider_name),
                    "provider_type": str(provider_type),
                    "status": "up",
                })
            except Exception as exc:
                healthy = False
                provider_statuses.append({
                    "provider_id": int(provider_id),
                    "provider_name": str(provider_name),
                    "provider_type": str(provider_type),
                    "status": "down",
                    "reason": str(exc),
                })
    except Exception as exc:
        details = {"reason": str(exc)}
        observe_dependency_state(component="ldap", healthy=False, details=details)
        return _dependency_payload(name="ldap", healthy=False, critical=True, details=details)

    details = {"providers": provider_statuses}
    observe_dependency_state(component="ldap", healthy=healthy, details=details)
    return _dependency_payload(name="ldap", healthy=healthy, critical=True, details=details)


def _optional_integrations_dependency() -> dict[str, Any]:
    providers = get_ai_provider_status()
    details = {
        name: ("configured" if enabled else "not_configured")
        for name, enabled in providers.items()
    }
    return _dependency_payload(name="external_integrations", healthy=True, critical=False, details=details)


def comprehensive_payload(app: FastAPI) -> dict[str, Any]:
    # Simplified DB check — only requires session_factory (no engine needed)
    session_factory = getattr(app.state, "admissions_session_factory", None)
    if session_factory is None:
        database_status = "unreachable"
    else:
        try:
            with session_factory() as session:
                session.execute(text("SELECT 1"))
            database_status = "reachable"
        except Exception:
            database_status = "unreachable"

    worker_dep = _worker_dependency()
    scheduler_dep = _scheduler_dependency()

    worker_status = "reachable" if worker_dep["healthy"] else "unreachable"
    scheduler_status = "reachable" if scheduler_dep["healthy"] else "unreachable"

    issues: list[str] = []
    if not worker_dep["healthy"]:
        issues.append("worker_not_running")
    if not scheduler_dep["healthy"]:
        issues.append("scheduler_not_running")
    if database_status == "unreachable":
        issues.append("database_unreachable")

    status = "healthy" if not issues else "degraded"

    metrics: dict[str, Any] = {}
    try:
        with UnitOfWork() as uow:
            metrics["event_queue_size"] = int(uow.job_repository.count_by_status("queued", conn=uow.conn))
    except Exception as exc:
        metrics["error"] = str(exc)

    return {
        "status": status,
        "components": {
            "database": database_status,
            "worker": worker_status,
            "scheduler": scheduler_status,
        },
        "issues": issues,
        "metrics": metrics,
        "timestamp": _now_iso(),
    }


def deep_payload(app: FastAPI) -> dict[str, Any]:
    readiness = readiness_payload(app)
    dependencies = dict(readiness["dependencies"])
    dependencies["ldap"] = _ldap_dependency(app)
    dependencies["jobs_queue"] = _jobs_queue_dependency()
    dependencies["worker"] = _worker_dependency()
    dependencies["scheduler"] = _scheduler_dependency()
    dependencies["external_integrations"] = _optional_integrations_dependency()
    checks = {
        str(name): {"ok": bool(item.get("healthy", False))}
        for name, item in dependencies.items()
    }
    # Fail closed for deep health: any non-OK component makes deep health unhealthy.
    # Check critical components explicitly
    critical_healthy = all(
        bool(item.get("healthy", False))
        for item in dependencies.values()
        if item.get("critical", False)
    )
    # Also check non-critical important components
    healthy = critical_healthy and all(
        bool(item.get("healthy", False)) for item in dependencies.values()
    )
    return {
        "status": "ok" if healthy else "degraded",
        "deep": healthy,
        "timestamp": _now_iso(),
        "dependencies": dependencies,
        "checks": checks,
    }