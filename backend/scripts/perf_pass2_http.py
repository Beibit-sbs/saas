#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import random
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

import httpx


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.auth.token_service import create_service_token  # noqa: E402


@dataclass(frozen=True)
class Operation:
    name: str
    method: str
    path: str | None = None
    weight: int = 1
    path_builder: Callable[[WorkerState], str] | None = None
    body: dict[str, Any] | None = None
    body_builder: Callable[[WorkerState], dict[str, Any]] | None = None
    expected_statuses: tuple[int, ...] = (200,)


@dataclass
class RequestResult:
    op_name: str
    status_code: int
    latency_ms: float
    ok: bool


@dataclass
class WorkerState:
    worker_id: int
    seed: int
    program_id: int
    created_applicant_ids: list[int]
    applicant_seq: int = 0

    def unique_email(self) -> str:
        self.applicant_seq += 1
        return f"perf.{self.seed}.{self.worker_id}.{self.applicant_seq}.{uuid4().hex[:8]}@applicant.edu"


def percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    idx = (len(sorted_values) - 1) * p
    lower = int(idx)
    upper = min(lower + 1, len(sorted_values) - 1)
    ratio = idx - lower
    return sorted_values[lower] * (1.0 - ratio) + sorted_values[upper] * ratio


async def fetch_admin_token(client: httpx.AsyncClient) -> str:
    try:
        response = await client.post(
            "/api/auth/login",
            json={"login": "admin", "password": "admin123"},
            headers={"X-Tenant-ID": "1"},
        )
        if int(response.status_code) == 200:
            token = str(response.json().get("access_token", "")).strip()
            if token:
                return token
    except Exception:
        pass

    return create_service_token(
        service_account_id="perf.pass2.service",
        permissions=[
            "admin.dashboard.read",
            "admin.jobs.read",
            "admin.jobs.write",
            "admin.programs.read",
            "admin.programs.write",
            "students.read",
            "admissions.write",
            "admissions.read",
            "admissions.documents.write",
        ],
        tenant_id=1,
        platform_global=True,
    )


def build_profile_operations(profile: str) -> list[Operation]:
    if profile == "baseline_http":
        return [
            Operation("health_live", "GET", "/health/live", 35),
            Operation("metrics", "GET", "/metrics", 20),
            Operation("auth_csrf", "GET", "/api/auth/csrf", 25),
            Operation("auth_modes", "GET", "/api/auth/modes", 10),
            Operation("jobs_list", "GET", "/api/admin/jobs?limit=50", 7),
            Operation(
                "jobs_enqueue",
                "POST",
                "/api/admin/jobs",
                3,
                body={"job_type": "sync", "payload": {"source": "baseline-http"}, "max_retries": 1},
            ),
        ]

    if profile == "read_heavy":
        return [
            Operation("dashboard", "GET", "/api/admin/dashboard", 20),
            Operation("students_list", "GET", "/api/admin/students?page=1&page_size=20", 25),
            Operation("jobs_list", "GET", "/api/admin/jobs?limit=50", 20),
            Operation("health_live", "GET", "/health/live", 20),
            Operation("metrics", "GET", "/metrics", 15),
        ]

    if profile == "write_heavy":
        return [
            Operation(
                "admissions_create_applicant",
                "POST",
                path="/api/admin/admissions/applicants",
                weight=35,
                body_builder=build_admissions_create_payload,
                expected_statuses=(201,),
            ),
            Operation(
                "admissions_update_applicant",
                "PATCH",
                weight=20,
                path_builder=build_admissions_update_path,
                body_builder=build_admissions_update_payload,
            ),
            Operation(
                "admissions_list_applicants",
                "GET",
                path="/api/admin/admissions/applicants?page=1&page_size=20",
                weight=15,
            ),
            Operation(
                "jobs_enqueue",
                "POST",
                path="/api/admin/jobs",
                weight=30,
                body={"job_type": "sync", "payload": {"source": "write-heavy"}, "max_retries": 1},
                expected_statuses=(200, 201),
            ),
        ]

    if profile == "mixed":
        return [
            Operation("dashboard", "GET", "/api/admin/dashboard", 15),
            Operation("students_list", "GET", "/api/admin/students?page=1&page_size=20", 15),
            Operation("health_live", "GET", "/health/live", 10),
            Operation("metrics", "GET", "/metrics", 10),
            Operation("jobs_list", "GET", "/api/admin/jobs?limit=50", 10),
            Operation(
                "admissions_create_applicant",
                "POST",
                path="/api/admin/admissions/applicants",
                weight=15,
                body_builder=build_admissions_create_payload,
                expected_statuses=(201,),
            ),
            Operation(
                "jobs_enqueue",
                "POST",
                path="/api/admin/jobs",
                weight=10,
                body={"job_type": "sync", "payload": {"source": "mixed"}, "max_retries": 1},
                expected_statuses=(200, 201),
            ),
        ]

    raise ValueError(f"Unknown profile: {profile}")


async def execute_operation(
    client: httpx.AsyncClient,
    operation: Operation,
    token: str,
    state: WorkerState,
) -> RequestResult:
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": "1",
        "Content-Type": "application/json",
    }

    started = time.perf_counter()
    try:
        path = operation.path_builder(state) if operation.path_builder is not None else operation.path
        if not path:
            raise ValueError(f"Operation path is required for {operation.name}")
        body = operation.body_builder(state) if operation.body_builder is not None else operation.body

        if operation.method == "GET":
            response = await client.get(path, headers=headers)
        elif operation.method == "POST":
            response = await client.post(path, headers=headers, json=body)
        elif operation.method == "PATCH":
            response = await client.patch(path, headers=headers, json=body)
        elif operation.method == "PUT":
            response = await client.put(path, headers=headers, json=body)
        else:
            raise ValueError(f"Unsupported method: {operation.method}")
        status_code = int(response.status_code)
        ok = status_code in operation.expected_statuses
        if ok and operation.name == "admissions_create_applicant":
            try:
                created_id = int(response.json().get("id"))
                state.created_applicant_ids.append(created_id)
                if len(state.created_applicant_ids) > 256:
                    state.created_applicant_ids = state.created_applicant_ids[-256:]
            except Exception:
                pass
    except Exception:
        status_code = 0
        ok = False
    latency_ms = (time.perf_counter() - started) * 1000.0
    return RequestResult(operation.name, status_code, latency_ms, ok)


async def run_profile_tier(
    client: httpx.AsyncClient,
    profile: str,
    concurrency: int,
    duration_s: int,
    warmup_s: int,
    seed: int,
) -> dict[str, Any]:
    operations = build_profile_operations(profile)
    weights = [op.weight for op in operations]

    await client.get("/metrics/perf-profile", params={"reset": "true", "top_n": 10})

    token = await fetch_admin_token(client)

    program_id = await discover_program_id(client, token)

    async def worker(worker_id: int, stop_at: float) -> list[RequestResult]:
        rng = random.Random(seed + worker_id * 9_973)
        state = WorkerState(
            worker_id=worker_id,
            seed=seed,
            program_id=program_id,
            created_applicant_ids=[],
        )
        rows: list[RequestResult] = []
        while time.perf_counter() < stop_at:
            operation = rng.choices(operations, weights=weights, k=1)[0]
            if operation.name == "admissions_update_applicant" and not state.created_applicant_ids:
                operation = next((op for op in operations if op.name == "admissions_create_applicant"), operation)
            rows.append(await execute_operation(client, operation, token, state))
        return rows

    warmup_end = time.perf_counter() + warmup_s
    await asyncio.gather(*[worker(i, warmup_end) for i in range(concurrency)])

    started = time.perf_counter()
    stop_at = started + duration_s
    chunks = await asyncio.gather(*[worker(i, stop_at) for i in range(concurrency)])
    elapsed = max(0.001, time.perf_counter() - started)

    results = [row for chunk in chunks for row in chunk]
    total = len(results)
    failures = sum(1 for row in results if not row.ok)
    ok_count = total - failures
    latencies = sorted(row.latency_ms for row in results)

    by_operation: dict[str, dict[str, Any]] = {}
    for operation in operations:
        rows = [row for row in results if row.op_name == operation.name]
        op_lat = sorted(row.latency_ms for row in rows)
        status_counts: dict[str, int] = {}
        for row in rows:
            key = str(row.status_code)
            status_counts[key] = status_counts.get(key, 0) + 1
        op_total = len(rows)
        op_fail = sum(1 for row in rows if not row.ok)
        by_operation[operation.name] = {
            "requests": op_total,
            "fail": op_fail,
            "error_rate": round((op_fail / op_total) if op_total else 0.0, 6),
            "status_counts": status_counts,
            "p50_ms": round(percentile(op_lat, 0.50), 2),
            "p95_ms": round(percentile(op_lat, 0.95), 2),
            "p99_ms": round(percentile(op_lat, 0.99), 2),
        }

    perf_profile_summary: dict[str, Any]
    try:
        perf_profile_response = await client.get("/metrics/perf-profile", params={"top_n": 10})
        if int(perf_profile_response.status_code) >= 400:
            perf_profile_summary = {
                "enabled": False,
                "error": f"status={perf_profile_response.status_code}",
                "top_segments": [],
                "counters": {},
                "top_queries": [],
            }
        else:
            perf_profile_summary = perf_profile_response.json()
    except Exception as exc:
        perf_profile_summary = {
            "enabled": False,
            "error": f"request_failed:{type(exc).__name__}",
            "top_segments": [],
            "counters": {},
            "top_queries": [],
        }

    try:
        ops_response = await client.get("/metrics/ops")
        if int(ops_response.status_code) >= 400:
            ops_metrics = {"error": f"status={ops_response.status_code}"}
        else:
            ops_metrics = ops_response.json()
    except Exception as exc:
        ops_metrics = {"error": f"request_failed:{type(exc).__name__}"}

    try:
        metrics_text = (await client.get("/metrics")).text
    except Exception:
        metrics_text = ""
    db_active = None
    redis_latency = None
    for line in metrics_text.splitlines():
        if line.startswith("db_connections_active "):
            value = line.split(" ", 1)[1].strip()
            db_active = None if value == "NaN" else float(value)
        if line.startswith("redis_latency_seconds "):
            value = line.split(" ", 1)[1].strip()
            redis_latency = None if value == "NaN" else float(value)

    return {
        "profile": profile,
        "concurrency": concurrency,
        "duration_s": duration_s,
        "warmup_s": warmup_s,
        "elapsed_s": round(elapsed, 2),
        "requests": total,
        "ok": ok_count,
        "fail": failures,
        "error_rate": round((failures / total) if total else 0.0, 6),
        "rps": round(total / elapsed, 2),
        "latency_ms": {
            "p50": round(percentile(latencies, 0.50), 2),
            "p95": round(percentile(latencies, 0.95), 2),
            "p99": round(percentile(latencies, 0.99), 2),
            "mean": round(statistics.fmean(latencies), 2) if latencies else 0.0,
        },
        "by_operation": by_operation,
        "hot_path": perf_profile_summary,
        "ops_metrics": ops_metrics,
        "db_active_connections_metric": db_active,
        "redis_latency_seconds_metric": redis_latency,
        "dataset": {
            "program_id": program_id,
        },
    }


def build_admissions_create_payload(state: WorkerState) -> dict[str, Any]:
    return {
        "email": state.unique_email(),
        "first_name": "Perf",
        "last_name": "Applicant",
        "program_id": state.program_id,
        "application_year": 2026,
    }


def build_admissions_update_payload(state: WorkerState) -> dict[str, Any]:
    return {
        "first_name": f"PerfUpdated{max(1, state.applicant_seq)}",
    }


def build_admissions_update_path(state: WorkerState) -> str:
    if state.created_applicant_ids:
        return f"/api/admin/admissions/applicants/{state.created_applicant_ids[-1]}"
    return "/api/admin/admissions/applicants/1"


async def discover_program_id(client: httpx.AsyncClient, token: str) -> int:
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": "1",
    }
    try:
        response = await client.get("/api/admin/university/programs", headers=headers)
        if int(response.status_code) == 200:
            programs = response.json().get("programs", [])
            if programs:
                candidate = int(programs[0].get("id"))
                if candidate > 0:
                    return candidate
    except Exception:
        pass

    create_payload = {
        "program_code": f"PERF-{uuid4().hex[:8].upper()}",
        "title": "Performance Validation Program",
        "degree_type": "BSc",
        "faculty": "Engineering",
        "status": "active",
    }
    try:
        response = await client.post("/api/admin/university/programs", headers=headers, json=create_payload)
        if int(response.status_code) in {200, 201}:
            program = response.json().get("program", {})
            candidate = int(program.get("id"))
            if candidate > 0:
                return candidate
    except Exception:
        pass

    # Last-resort fallback for environments where university programs are pre-seeded.
    return 1


def _write_report_checkpoint(report: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    tmp_path.replace(out_path)


def compare_with_asgi(
    asgi_report: dict[str, Any],
    baseline_http_tiers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    asgi_by_concurrency = {int(row["concurrency"]): row for row in asgi_report.get("tiers", [])}
    rows: list[dict[str, Any]] = []
    for http_row in baseline_http_tiers:
        concurrency = int(http_row["concurrency"])
        asgi_row = asgi_by_concurrency.get(concurrency)
        if asgi_row is None:
            continue
        rows.append(
            {
                "concurrency": concurrency,
                "asgi_rps": float(asgi_row.get("rps", 0.0) or 0.0),
                "http_rps": float(http_row.get("rps", 0.0) or 0.0),
                "delta_rps_percent": round(
                    ((float(http_row.get("rps", 0.0) or 0.0) - float(asgi_row.get("rps", 0.0) or 0.0)) /
                     max(0.001, float(asgi_row.get("rps", 0.0) or 0.0)))
                    * 100.0,
                    2,
                ),
                "asgi_p99_ms": float((asgi_row.get("latency_ms") or {}).get("p99", 0.0) or 0.0),
                "http_p99_ms": float((http_row.get("latency_ms") or {}).get("p99", 0.0) or 0.0),
                "delta_p99_ms": round(
                    float((http_row.get("latency_ms") or {}).get("p99", 0.0) or 0.0)
                    - float((asgi_row.get("latency_ms") or {}).get("p99", 0.0) or 0.0),
                    2,
                ),
            }
        )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Performance Pass 2 benchmark over real HTTP stack")
    parser.add_argument("--base-url", type=str, default="http://127.0.0.1:8000", help="Target backend base URL")
    parser.add_argument("--duration", type=int, default=6, help="Measured duration per tier")
    parser.add_argument("--warmup", type=int, default=2, help="Warmup duration per tier")
    parser.add_argument("--tiers", type=str, default="1,4,8,16,32", help="Concurrency tiers")
    parser.add_argument(
        "--profiles",
        type=str,
        default="baseline_http,read_heavy,write_heavy,mixed",
        help="Comma-separated profiles",
    )
    parser.add_argument(
        "--asgi-baseline",
        type=Path,
        default=Path("backend/test-results/perf_baseline_latest.json"),
        help="Path to ASGI baseline report",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("backend/test-results/perf_pass2_http.json"),
        help="Output report path",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--checkpoint-every-tier",
        action="store_true",
        help="Persist a checkpoint report after each completed tier",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    tiers = [int(part.strip()) for part in args.tiers.split(",") if part.strip()]
    profiles = [part.strip() for part in args.profiles.split(",") if part.strip()]

    timeout = httpx.Timeout(connect=5.0, read=60.0, write=60.0, pool=60.0)
    limits = httpx.Limits(max_connections=400, max_keepalive_connections=200)

    results_by_profile: dict[str, list[dict[str, Any]]] = {name: [] for name in profiles}
    async with httpx.AsyncClient(base_url=args.base_url, timeout=timeout, limits=limits) as client:
        health = await client.get("/health/live")
        health.raise_for_status()

        for profile in profiles:
            for concurrency in tiers:
                summary = await run_profile_tier(
                    client=client,
                    profile=profile,
                    concurrency=concurrency,
                    duration_s=args.duration,
                    warmup_s=args.warmup,
                    seed=args.seed,
                )
                results_by_profile[profile].append(summary)
                print(
                    f"profile={profile:>12} c={concurrency:>2} rps={summary['rps']:>8} "
                    f"err={summary['error_rate']:.4f} p95={summary['latency_ms']['p95']}ms p99={summary['latency_ms']['p99']}ms"
                )
                if args.checkpoint_every_tier:
                    _write_report_checkpoint(
                        {
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "mode": "real-http-stack",
                            "base_url": args.base_url,
                            "duration_s": args.duration,
                            "warmup_s": args.warmup,
                            "tiers": tiers,
                            "profiles": results_by_profile,
                            "asgi_http_comparison": [],
                            "partial": True,
                        },
                        args.out,
                    )

    asgi_report: dict[str, Any] = {}
    if args.asgi_baseline.exists():
        asgi_report = json.loads(args.asgi_baseline.read_text(encoding="utf-8"))

    comparison = compare_with_asgi(asgi_report, results_by_profile.get("baseline_http", []))

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "real-http-stack",
        "base_url": args.base_url,
        "duration_s": args.duration,
        "warmup_s": args.warmup,
        "tiers": tiers,
        "profiles": results_by_profile,
        "asgi_http_comparison": comparison,
    }

    _write_report_checkpoint(report, args.out)
    print(f"Saved report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
