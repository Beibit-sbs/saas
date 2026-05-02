/**
 * k6 Load Test – 500 Virtual Users, 20s sustained
 * Endpoint: GET /api/auth/me  (authenticated)
 *
 * Laptop-constrained: shorter duration, but full VU count.
 * Results will be annotated with hardware constraints in the report.
 *
 * Run with:
 *   docker run --rm --network host -i grafana/k6 run - < load_test_500vu.js
 */
import http from "k6/http";
import { check } from "k6";

const TOKEN_A =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzc2NDE5NzgsImlhdCI6MTc3NzY0MTA3OCwianRpIjoiOGNlZDExOWMtNzlmNy00NDlhLThkYmItYjAzZmYyYzY0NDI5IiwicGciOmZhbHNlLCJyb2xlcyI6WyJzdHVkZW50Il0sInNjcCI6W10sInNyYyI6ImxkYXAiLCJzdWIiOiJhZC5sb2FkX3VzZXJfYSIsInRpZCI6MSwidG9rZW5fdHlwZSI6ImFjY2VzcyIsInZlciI6MX0.ZHKC4sPBCFP3W1P0AL8Q61_chPDKJKKJTOdYMZiQMEo";

const BASE = "http://localhost:8000";

export const options = {
  scenarios: {
    ramp_500vu: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "10s", target: 500 },
        { duration: "20s", target: 500 },
        { duration: "5s", target: 0 },
      ],
      gracefulRampDown: "5s",
    },
  },
  thresholds: {
    http_req_duration: ["p(99)<5000"], // relaxed for laptop
    http_req_failed: ["rate<0.05"],    // 5% error budget for resource-constrained env
  },
};

export default function () {
  const r = http.get(`${BASE}/api/auth/me`, {
    headers: { Authorization: `Bearer ${TOKEN_A}` },
    timeout: "10s",
  });

  check(r, {
    "me 200": (rr) => rr.status === 200,
    "me authenticated": (rr) => {
      try {
        return JSON.parse(rr.body).authenticated === true;
      } catch {
        return false;
      }
    },
  });
}
