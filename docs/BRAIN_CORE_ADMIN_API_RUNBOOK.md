# Brain Core Admin API Runbook

Документ фиксирует эксплуатационный контракт Brain Core для админ-консоли и ops-команды.

## 1. Auth и доступ

- Base path: `/api/admin/brain`
- Read endpoints требуют: `admin.dashboard.read`
- Write endpoints требуют: `admin.dashboard.write`
- Все ответы tenant-scoped (контекст берется из входного payload/решения).

## 2. Read endpoints

- `GET /health`
- `GET /signals`
- `GET /decisions`
- `GET /decisions/{decision_id}`
- `GET /explanations/{decision_id}`
- `GET /dispatch/snapshot`
- `GET /outcomes`
- `GET /learning/metrics`
- `GET /policy/{tenant_id}`
- `GET /learning/policy-tuning/{tenant_id}`
- `GET /metrics`
- `GET /traces?limit=100`

## 3. Write endpoints

- `PUT /policy/{tenant_id}`
- `POST /simulate/student-risk`
- `POST /simulate/thesis-delay`
- `POST /simulate/faculty-overload`
- `POST /simulate/payment-overdue`
- `POST /simulate/supply-low`
- `POST /simulate/research-grant-deadline`
- `POST /simulate/research-publication-stagnant`
- `POST /decisions/{decision_id}/approve`
- `POST /decisions/{decision_id}/cancel`
- `POST /decisions/{decision_id}/outcome`
- `POST /learning/policy-tuning/{tenant_id}/apply`

## 4. Policy profile contract

`PUT /policy/{tenant_id}` payload:

```json
{
  "autonomy_level": 2,
  "require_approval_for_critical": true,
  "default_approval_role": "dean_office",
  "enable_ai_reasoning": false,
  "actor": "admin@brain"
}
```

Правила:

- `autonomy_level`: `0..4`
- `default_approval_role`: непустая строка, max 64
- Критические решения могут принудительно идти в approval в зависимости от tenant policy

## 5. Decision actions contract

Approve:

```json
{
  "actor": "dean@tenant"
}
```

Cancel:

```json
{
  "actor": "ops@tenant",
  "reason": "manual_review_needed"
}
```

Outcome:

```json
{
  "actor": "ops@tenant",
  "outcome_type": "completed",
  "effectiveness": "positive",
  "notes": "closed_on_time"
}
```

## 6. Explanation payload example

`GET /explanations/{decision_id}`:

```json
{
  "summary": "Decision for student=STU-1 based on academic.attendance_risk.detected; priority=high",
  "factors": [
    "event_type=academic.attendance_risk.detected",
    "situation_type=academic_risk",
    "severity=high",
    "urgency=high",
    "attendance_rate=0.35",
    "grade_trend=declining",
    "ai_reasoning=enabled"
  ],
  "policy_notes": [
    "policy_passed",
    "approval_role=dean_office"
  ],
  "expected_outcome": "Actions dispatched or queued for approval based on policy."
}
```

## 7. Ops checks

Минимальный smoke-read:

```bash
curl -sS "$BASE/health"
curl -sS "$BASE/decisions"
curl -sS "$BASE/outcomes"
```

Минимальный simulate flow (student risk):

```bash
curl -sS -X POST "$BASE/simulate/student-risk" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": 101,
    "student_id": "STU-1",
    "attendance_rate": 0.35,
    "grade_trend": "declining"
  }'
```

## 8. Known constraints

- Полный backend coverage gate (`fail-under=80`) не является валидатором только Brain Core пути.
- Для scoped функциональной проверки Brain Core используем:

```bash
docker compose --env-file .env run --rm -T backend-tests \
  pytest -q /app/app/modules/brain_core/tests --no-cov
```
