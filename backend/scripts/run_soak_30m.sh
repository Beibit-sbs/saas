#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

mkdir -p test-results/soak_segments

set -a
. backend/.perf.env
set +a

for i in 1 2 3 4 5 6; do
  echo "[soak] segment ${i}/6 start"
  backend/.venv/bin/python -u backend/scripts/perf_pass2_http.py \
    --base-url http://127.0.0.1:8010 \
    --profiles mixed \
    --tiers 16 \
    --duration 300 \
    --warmup 5 \
    --out "test-results/soak_segments/mixed_c16_seg${i}.json"
  echo "[soak] segment ${i}/6 done"
done

backend/.venv/bin/python - << 'PY'
import json
from pathlib import Path

base = Path("test-results/soak_segments")
segments = []
for i in range(1, 7):
    path = base / f"mixed_c16_seg{i}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    row = (payload.get("profiles", {}).get("mixed") or [])[0]
    by_op = row.get("by_operation", {})
    jobs = by_op.get("jobs_enqueue", {})
    segments.append(
        {
            "segment": i,
            "created_at": payload.get("created_at"),
            "total": row.get("requests"),
            "success": row.get("ok"),
            "errors": row.get("fail"),
            "error_rate": row.get("error_rate"),
            "rps": row.get("rps"),
            "p50_ms": (row.get("latency_ms") or {}).get("p50"),
            "p95_ms": (row.get("latency_ms") or {}).get("p95"),
            "p99_ms": (row.get("latency_ms") or {}).get("p99"),
            "jobs_enqueue_requests": jobs.get("requests"),
            "jobs_enqueue_fail": jobs.get("fail"),
            "jobs_enqueue_error_rate": jobs.get("error_rate"),
        }
    )

totals = {
    "total": sum(int(item.get("total") or 0) for item in segments),
    "success": sum(int(item.get("success") or 0) for item in segments),
    "errors": sum(int(item.get("errors") or 0) for item in segments),
}
if totals["total"] > 0:
    totals["error_rate"] = round(totals["errors"] / totals["total"], 6)

artifact = {
    "duration_minutes": 30,
    "profile": "mixed",
    "concurrency": 16,
    "segments": segments,
    "totals": totals,
}
out = Path("test-results/perf_soak_mixed_c16_30m_trend_20260328.json")
out.write_text(json.dumps(artifact, indent=2, ensure_ascii=True), encoding="utf-8")
print(f"SOAK_ARTIFACT={out}")
PY
