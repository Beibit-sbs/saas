# AUDIT-14 STRICT v1 — Checklist

Как использовать:
1. В начале дня отметь [ ] у задач дня.
2. По мере выполнения меняй на [x] только после VERIFIED.
3. Если блокер — оставь [ ] и допиши (blocker: ...).

## День 1 — Baseline Freeze

- [ ] D1-T1 Инвентарь backend/frontend/tests/migrations
- [ ] D1-T2 Baseline CRITICAL/WEAK defects
- [ ] D1-T3 Prioritized remediation backlog
- [ ] D1-GATE День закрыт по критериям

## День 2 — Security Surface Hardening

- [ ] D2-T1 RBAC audit по критичным endpoint
- [ ] D2-T2 Tenant enforcement audit read/write
- [ ] D2-T3 Fail-open точки закрыты
- [ ] D2-GATE День закрыт по критериям

## День 3 — Silent Failures Wave 1

- [ ] D3-T1 Удалены silent failures в auth/jobs/billing/admissions
- [ ] D3-T2 Error-path fail-closed + structured logs
- [ ] D3-T3 Добавлены error-path тесты
- [ ] D3-GATE День закрыт по критериям

## День 4 — Silent Failures Wave 2

- [ ] D4-T1 Удалены silent failures в brain/replay/queue/workflows
- [ ] D4-T2 Единый error-policy применен
- [ ] D4-T3 Смежная регрессия пройдена
- [ ] D4-GATE День закрыт по критериям

## День 5 — Tenant Isolation

- [ ] D5-T1 Негативные cross-tenant tests (read/write)
- [ ] D5-T2 Tenant guards до критичных write paths
- [ ] D5-T3 Listing/reporting leakage checks
- [ ] D5-GATE День закрыт по критериям

## День 6 — Domain Guards & Invariants

- [ ] D6-T1 Transition guard audit
- [ ] D6-T2 Cross-entity validation checks
- [ ] D6-T3 Missing invariants fixed + tested
- [ ] D6-GATE День закрыт по критериям

## День 7 — Events/Outbox Integrity

- [ ] D7-T1 Publish/retry/failure-path checks
- [ ] D7-T2 Correlation/causation linkage checks
- [ ] D7-T3 Duplicate/replay handling tests
- [ ] D7-GATE День закрыт по критериям

## День 8 — Replay/Queue Reliability

- [ ] D8-T1 Idempotency checks replay/approve/cancel/claim/complete
- [ ] D8-T2 SLA breach handling checks
- [ ] D8-T3 Conflict/escalation paths verified
- [ ] D8-GATE День закрыт по критериям

## День 9 — Data Integrity

- [ ] D9-T1 Migration checks (clean + upgrade DB)
- [ ] D9-T2 FK/orphan/uniqueness checks
- [ ] D9-T3 Snapshot consistency checks
- [ ] D9-GATE День закрыт по критериям

## День 10 — Test Architecture

- [ ] D10-T1 Flaky patterns removed in critical tests
- [ ] D10-T2 P0/P1 test gaps closed
- [ ] D10-T3 Noise/warnings normalized
- [ ] D10-GATE День закрыт по критериям

## День 11 — Frontend/Backend Contract Parity

- [ ] D11-T1 Endpoint vs hooks/types/pages parity
- [ ] D11-T2 Dead hooks/dead endpoints cleanup
- [ ] D11-T3 Missing critical contracts closed
- [ ] D11-GATE День закрыт по критериям

## День 12 — Observability Hardening

- [ ] D12-T1 Error/SLA metrics coverage
- [ ] D12-T2 Trace linkage by correlation_id
- [ ] D12-T3 Critical alert rules verified
- [ ] D12-GATE День закрыт по критериям

## День 13 — Full Gates

- [ ] D13-T1 Safe/smoke/release gates run
- [ ] D13-T2 All regressions fixed
- [ ] D13-T3 Re-run to full green
- [ ] D13-GATE День закрыт по критериям

## День 14 — Final Red-Team Audit

- [ ] D14-T1 CRITICAL class re-audit complete
- [ ] D14-T2 Anti-hidden verification complete
- [ ] D14-T3 Final hardening report + residual risks
- [ ] D14-GATE День закрыт по критериям

## Глобальные стоп-условия (всегда)

- [ ] S1 Нет UNKNOWN в закрытых задачах
- [ ] S2 Нет незакрытого CRITICAL в текущем дне
- [ ] S3 Каждый VERIFIED имеет Evidence Pack
- [ ] S4 Нет скрытых TODO/FIXME без blocker

## После Day 14 — Continuation Checklist

- [ ] CYCLE-RESET Подготовлен новый цикл Day 1..Day 14
- [ ] CARRY-OVER Все незакрытые P0/P1 перенесены первыми
- [ ] RE-BASELINE Обновлен baseline перед новым циклом
- [ ] STAB-CHK-1 Gate run #1 без CRITICAL
- [ ] STAB-CHK-2 Gate run #2 без CRITICAL
- [ ] STAB-CHK-3 Ноль незакрытых CRITICAL в backlog
- [ ] STAB-CHK-4 Все BLOCKED с owner и ETA
- [ ] STAB-CHK-5 Нет reopen закрытых P0/P1 за 14 дней
- [ ] DECISION Решение зафиксировано: продолжаем hardening или переходим в поддерживающий режим

## Шаблон дневной сводки

Дата:
День:

Сделано:
- 

Не сделано:
- 

Блокеры:
- 

Риски на завтра:
- 
