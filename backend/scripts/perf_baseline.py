#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import random
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx

# Keep benchmark runtime self-contained and aligned with test defaults.
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production-use-only-32ch")
os.environ.setdefault("API_BASE_URL", "https://api.example.test")
os.environ.setdefault("ADMIN_PANEL_URL", "https://admin.example.test")
os.environ.setdefault("INTERNAL_API_TOKEN", "internal-token-for-tests-only")
os.environ.setdefault("RBAC_ALLOW_DEV_FALLBACK", "true")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402
from app.modules.auth.token_service import create_access_token  # noqa: E402
from app.modules.jobs import service as jobs_service  # noqa: E402
from app.modules.observability.metrics import clear_metrics_state  # noqa: E402
from app.modules.rbac import service as rbac_service  # noqa: E402
from app.modules.security import rate_limit as rate_limit_service  # noqa: E402


@dataclass(frozen=True)
class Operation:
    name: str
    method: str
    path: str
    weight: int
    expected_statuses: tuple[int, ...]


@dataclass
class RequestResult:
    op_name: str
    latency_ms: float
    ok: bool
    status_code: int


def percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    idx = (len(sorted_values) - 1) * p
    lower = int(idx)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = idx - lower
    return sorted_values[lower] * (1.0 - fraction) + sorted_values[upper] * fraction


def make_admin_headers(tenant_id: int) -> dict[str, str]:
    token = create_access_token(
        user_id="owner@example.com",
        roles=["admin"],
        auth_source="perf-benchmark",
        tenant_id=tenant_id,
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
        "Content-Type": "application/json",
    }


def make_user_headers(tenant_id: int) -> dict[str, str]:
    return {
        "X-Tenant-ID": str(tenant_id),
        "Content-Type": "application/json",
    }


def suppress_chatty_logs() -> None:
    # Avoid benchmark noise from per-request logs; keep errors visible.
    noisy = [
        "httpx",
        "app.request",
        "app.audit",
        "app.identity.events",
    ]
    for logger_name in noisy:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def choose_operation(ops: list[Operation], rng: random.Random) -> Operation:
    weights = [op.weight for op in ops]
    return rng.choices(ops, weights=weights, k=1)[0]


async def execute_operation(
    client: httpx.AsyncClient,
    op: Operation,
    tenant_id: int,
    seq: int,
) -> RequestResult:
    if op.name == "jobs_enqueue":
        headers = make_admin_headers(1)
        body = {
            "job_type": "sync",
            "payload": {"n": seq, "tenant": 1},
            "max_retries": 1,
        }
    elif op.name == "jobs_list":
        headers = make_admin_headers(1)
        body = None
    else:
        headers = make_user_headers(tenant_id)
        body = None

    started = time.perf_counter()
    try:
        if op.method == "GET":
            response = await client.get(op.path, headers=headers)
        elif op.method == "POST":
            response = await client.post(op.path, headers=headers, json=body)
        else:
            raise ValueError(f"Unsupported method: {op.method}")
        ok = response.status_code in op.expected_statuses
        code = response.status_code
    except Exception:
        ok = False
        code = 0
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    return RequestResult(op_name=op.name, latency_ms=elapsed_ms, ok=ok, status_code=code)


async def run_tier(
    *,
    concurrency: int,
    duration_s: int,
    warmup_s: int,
    seed: int,
) -> dict[str, object]:
    ops = [
        Operation("health_live", "GET", "/health/live", 35, (200,)),
        Operation("metrics", "GET", "/metrics", 20, (200,)),
        Operation("auth_csrf", "GET", "/api/auth/csrf", 25, (200,)),
        Operation("auth_modes", "GET", "/api/auth/modes", 10, (200,)),
        Operation("jobs_list", "GET", "/api/admin/jobs?limit=50", 7, (200,)),
        Operation("jobs_enqueue", "POST", "/api/admin/jobs", 3, (200,)),
    ]

    transport = httpx.ASGITransport(app=app)

    async def worker(worker_id: int, stop_at: float) -> list[RequestResult]:
        rng = random.Random(seed + worker_id * 100_003)
        seq = 0
        tenant_ids = [1, 2, 3]
        local_results: list[RequestResult] = []
        async with httpx.AsyncClient(transport=transport, base_url="http://benchmark") as client:
            while time.perf_counter() < stop_at:
                seq += 1
                op = choose_operation(ops, rng)
                tenant_id = tenant_ids[seq % len(tenant_ids)]
                local_results.append(await execute_operation(client, op, tenant_id, seq))
        return local_results

    # Reset state that can bias cross-tier results.
    jobs_service.clear_jobs_state()
    rate_limit_service.clear_rate_limit_state()
    clear_metrics_state()
    try:
        rbac_service.assign_role_to_user(tenant_id=1, user_id="owner@example.com", role="admin")
    except ValueError:
        pass

    warmup_end = time.perf_counter() + warmup_s
    await asyncio.gather(*[worker(i, warmup_end) for i in range(concurrency)])

    started_at = time.perf_counter()
    stop_at = started_at + duration_s
    chunks = await asyncio.gather(*[worker(i, stop_at) for i in range(concurrency)])
    elapsed = time.perf_counter() - started_at

    all_results = [item for chunk in chunks for item in chunk]
    latencies = sorted(r.latency_ms for r in all_results)
    total = len(all_results)
    ok = sum(1 for r in all_results if r.ok)
    failures = total - ok
    error_rate = (failures / total) if total else 0.0

    by_op: dict[str, dict[str, object]] = {}
    for op in ops:
        op_rows = [r for r in all_results if r.op_name == op.name]
        op_lat = sorted(r.latency_ms for r in op_rows)
        op_total = len(op_rows)
        op_ok = sum(1 for r in op_rows if r.ok)
        op_fail = op_total - op_ok
        status_counts: dict[str, int] = {}
        for row in op_rows:
            key = str(row.status_code)
            status_counts[key] = status_counts.get(key, 0) + 1
        by_op[op.name] = {
            "requests": op_total,
            "ok": op_ok,
            "fail": op_fail,
            "error_rate": (op_fail / op_total) if op_total else 0.0,
            "p50_ms": round(percentile(op_lat, 0.50), 2),
            "p95_ms": round(percentile(op_lat, 0.95), 2),
            "p99_ms": round(percentile(op_lat, 0.99), 2),
            "status_counts": status_counts,
        }

    summary = {
        "concurrency": concurrency,
        "duration_s": duration_s,
        "warmup_s": warmup_s,
        "elapsed_s": round(elapsed, 2),
        "requests": total,
        "ok": ok,
        "fail": failures,
        "error_rate": round(error_rate, 6),
        "rps": round(total / elapsed, 2) if elapsed > 0 else 0.0,
        "latency_ms": {
            "min": round(latencies[0], 2) if latencies else 0.0,
            "mean": round(statistics.fmean(latencies), 2) if latencies else 0.0,
            "p50": round(percentile(latencies, 0.50), 2),
            "p95": round(percentile(latencies, 0.95), 2),
            "p99": round(percentile(latencies, 0.99), 2),
            "max": round(latencies[-1], 2) if latencies else 0.0,
        },
        "by_operation": by_op,
    }
    return summary


def assess_bottlenecks(tiers: list[dict[str, object]]) -> list[str]:
    notes: list[str] = []
    previous_rps: float | None = None

    for tier in tiers:
        conc = int(tier["concurrency"])
        rps = float(tier["rps"])
        err = float(tier["error_rate"])
        lat = tier["latency_ms"]
        p50 = float(lat["p50"])
        p99 = float(lat["p99"])

        if err > 0.01:
            notes.append(f"concurrency={conc}: error_rate={err:.2%} > 1% (service instability under this load)")
        if p50 > 0 and (p99 / p50) > 8.0:
            notes.append(f"concurrency={conc}: p99/p50={p99/p50:.1f} indicates high tail-latency variance")

        if previous_rps is not None:
            growth = (rps / previous_rps) if previous_rps > 0 else 0.0
            if growth < 1.15:
                notes.append(
                    f"concurrency={conc}: throughput scaling flattening (x{growth:.2f} vs previous tier), potential saturation"
                )
        previous_rps = rps

    if not notes:
        notes.append("No clear instability in tested tiers; throughput scaled without major regressions.")
    return notes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 2 baseline benchmark for backend ASGI app")
    parser.add_argument("--duration", type=int, default=20, help="Measured duration per tier in seconds")
    parser.add_argument("--warmup", type=int, default=4, help="Warmup duration per tier in seconds")
    parser.add_argument(
        "--tiers",
        type=str,
        default="1,4,16,32",
        help="Comma-separated concurrency tiers, e.g. 1,4,16,32",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible operation mix")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("test-results/perf_baseline_latest.json"),
        help="Path to JSON output report",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    suppress_chatty_logs()

    tiers = [int(part.strip()) for part in args.tiers.split(",") if part.strip()]
    if not tiers:
        raise SystemExit("No tiers specified")

    runs: list[dict[str, object]] = []
    for concurrency in tiers:
        summary = await run_tier(
            concurrency=concurrency,
            duration_s=args.duration,
            warmup_s=args.warmup,
            seed=args.seed,
        )
        runs.append(summary)
        print(
            f"tier={concurrency:>3} rps={summary['rps']:>8} "
            f"err={summary['error_rate']:.4f} "
            f"p95={summary['latency_ms']['p95']}ms p99={summary['latency_ms']['p99']}ms"
        )

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "in-process-asgi",
        "duration_s": args.duration,
        "warmup_s": args.warmup,
        "tiers": runs,
        "bottleneck_notes": assess_bottlenecks(runs),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")

    print("\nBottleneck notes:")
    for note in report["bottleneck_notes"]:
        print(f"- {note}")
    print(f"\nSaved report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
