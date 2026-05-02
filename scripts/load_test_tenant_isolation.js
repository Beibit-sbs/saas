/**
 * k6 Tenant A/B Isolation Test – 50 VU, 30s
 *
 * Half VUs use Tenant A token (tid=1), half use Tenant B token (tid=2).
 * Each iteration asserts that the returned tenantId matches the token's tenant.
 * A cross-tenant data leak registers as a custom counter.
 *
 * Run with:
 *   docker run --rm --network host -i grafana/k6 run - < load_test_tenant_isolation.js
 */
import http from "k6/http";
import { check } from "k6";
import { Counter } from "k6/metrics";

const TOKEN_A =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzc2NDE5NzgsImlhdCI6MTc3NzY0MTA3OCwianRpIjoiOGNlZDExOWMtNzlmNy00NDlhLThkYmItYjAzZmYyYzY0NDI5IiwicGciOmZhbHNlLCJyb2xlcyI6WyJzdHVkZW50Il0sInNjcCI6W10sInNyYyI6ImxkYXAiLCJzdWIiOiJhZC5sb2FkX3VzZXJfYSIsInRpZCI6MSwidG9rZW5fdHlwZSI6ImFjY2VzcyIsInZlciI6MX0.ZHKC4sPBCFP3W1P0AL8Q61_chPDKJKKJTOdYMZiQMEo";

const TOKEN_B =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzc2NDE5NzgsImlhdCI6MTc3NzY0MTA3OCwianRpIjoiNDRjZDk4M2YtMjJlYy00OWMzLTlkMmEtZDkxNTk5YjQ3YWZiIiwicGciOmZhbHNlLCJyb2xlcyI6WyJzdHVkZW50Il0sInNjcCI6W10sInNyYyI6ImxkYXAiLCJzdWIiOiJhZC5sb2FkX3VzZXJfYiIsInRpZCI6MiwidG9rZW5fdHlwZSI6ImFjY2VzcyIsInZlciI6MX0.MXGryX54Z4XaAcxX1sFTWNqMtUdrMc0XRAUdtJ9mhgQ";

const BASE = "http://localhost:8000";

export const options = {
  scenarios: {
    tenant_a_users: {
      executor: "constant-vus",
      vus: 25,
      duration: "30s",
      env: { TENANT: "A", TOKEN: TOKEN_A, EXPECTED_TID: "1" },
    },
    tenant_b_users: {
      executor: "constant-vus",
      vus: 25,
      duration: "30s",
      env: { TENANT: "B", TOKEN: TOKEN_B, EXPECTED_TID: "2" },
    },
  },
  thresholds: {
    "tenant_isolation_violations": ["count==0"],
    "http_req_failed": ["rate<0.01"],
    "http_req_duration": ["p(95)<1500"],
  },
};

const tenantIsolationViolations = new Counter("tenant_isolation_violations");
const tenantCorrect = new Counter("tenant_correct_assertions");

export default function () {
  const token = __ENV.TOKEN;
  const expectedTid = parseInt(__ENV.EXPECTED_TID, 10);
  const tenantLabel = __ENV.TENANT;

  const r = http.get(`${BASE}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
    tags: { tenant: tenantLabel },
  });

  const bodyOk = check(r, {
    [`[${tenantLabel}] status 200`]: (rr) => rr.status === 200,
    [`[${tenantLabel}] authenticated=true`]: (rr) => {
      try {
        return JSON.parse(rr.body).authenticated === true;
      } catch {
        return false;
      }
    },
    [`[${tenantLabel}] tenantId correct`]: (rr) => {
      try {
        const body = JSON.parse(rr.body);
        return body.user && body.user.tenantId === expectedTid;
      } catch {
        return false;
      }
    },
    [`[${tenantLabel}] no cross-tenant data`]: (rr) => {
      // Ensure Tenant A never sees Tenant B's tenantId and vice versa
      try {
        const body = JSON.parse(rr.body);
        if (!body.user) return true; // unauthenticated is safe (no data)
        const gotTid = body.user.tenantId;
        return gotTid === expectedTid;
      } catch {
        return false;
      }
    },
  });

  // Record isolation metric
  try {
    const body = JSON.parse(r.body);
    if (body.user && body.user.tenantId !== expectedTid) {
      tenantIsolationViolations.add(1);
    } else if (body.user) {
      tenantCorrect.add(1);
    }
  } catch {}
}
