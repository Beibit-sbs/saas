/**
 * k6 Load Test – 100 Virtual Users, 30s
 * Endpoint: GET /api/auth/me  (authenticated, tenant-scoped)
 * Additional: GET /health    (unauthenticated baseline)
 *
 * Run with:
 *   docker run --rm --network host -i grafana/k6 run - < load_test_100vu.js
 */
import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

const TOKEN_A =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzc2NDE5NzgsImlhdCI6MTc3NzY0MTA3OCwianRpIjoiOGNlZDExOWMtNzlmNy00NDlhLThkYmItYjAzZmYyYzY0NDI5IiwicGciOmZhbHNlLCJyb2xlcyI6WyJzdHVkZW50Il0sInNjcCI6W10sInNyYyI6ImxkYXAiLCJzdWIiOiJhZC5sb2FkX3VzZXJfYSIsInRpZCI6MSwidG9rZW5fdHlwZSI6ImFjY2VzcyIsInZlciI6MX0.ZHKC4sPBCFP3W1P0AL8Q61_chPDKJKKJTOdYMZiQMEo";

const BASE = "http://localhost:8000";

export const options = {
  scenarios: {
    // Scenario 1 – ramp to 100 VU, hold 30s, ramp down
    ramp_100vu: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "10s", target: 100 }, // ramp-up
        { duration: "30s", target: 100 }, // hold
        { duration: "10s", target: 0 }, // ramp-down
      ],
      gracefulRampDown: "5s",
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<500", "p(99)<1000"],
    http_req_failed: ["rate<0.01"],
  },
};

const meErrors = new Counter("me_errors");
const meOK = new Counter("me_ok");
const healthDuration = new Trend("health_duration_ms");
const meDuration = new Trend("me_duration_ms");
const tenantMismatch = new Counter("tenant_mismatch");

export default function () {
  // Request 1: unauthenticated health (baseline)
  const h = http.get(`${BASE}/health`);
  check(h, { "health 200": (r) => r.status === 200 });
  healthDuration.add(h.timings.duration);

  // Request 2: authenticated /api/auth/me
  const r = http.get(`${BASE}/api/auth/me`, {
    headers: { Authorization: `Bearer ${TOKEN_A}` },
  });

  const ok = check(r, {
    "me 200": (rr) => rr.status === 200,
    "me authenticated": (rr) => {
      try {
        const body = JSON.parse(rr.body);
        return body.authenticated === true;
      } catch {
        return false;
      }
    },
    "me tenantId=1": (rr) => {
      try {
        const body = JSON.parse(rr.body);
        return body.user && body.user.tenantId === 1;
      } catch {
        return false;
      }
    },
  });

  meDuration.add(r.timings.duration);

  if (!ok) {
    meErrors.add(1);
    // Check for tenant data leakage
    try {
      const body = JSON.parse(r.body);
      if (body.user && body.user.tenantId !== 1) {
        tenantMismatch.add(1);
      }
    } catch {}
  } else {
    meOK.add(1);
  }

  sleep(0.1); // 100ms think time → ~10 req/s per VU → ~1000 req/s at 100 VU
}
