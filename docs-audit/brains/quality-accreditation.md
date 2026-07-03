# Brain: Quality Accreditation

[← Каталог Brain](README.md) · Модуль: [../modules/quality-accreditation.md](../modules/quality-accreditation.md)

Модуль: `backend/app/modules/quality_accreditation/` · A‑050

## Назначение
Brain‑вертикаль качества и аккредитации: самооценка, доказательства, аудит‑находки, корректирующие действия, планы улучшений, мониторинг готовности.

## Функции (под‑роутеры, 8)
`accreditation_evidence`, `accreditation_registry`, `audit_findings`, `corrective_action`, `dashboard`, `improvement_plan`, `readiness_monitoring`, `self_assessment` + `runtime_shell`.

## Входные данные
Сигнал `accreditation.status_changed`; данные самооценки, доказательства, аудит‑находки.

## Выходные данные
Решение `accreditation_remediation`; accreditation remediation workflow; уведомления compliance; готовность к отчёту министерству.

## Связанный Runtime Shell
`QualityAccreditationRuntimeShellPage` (`/console/quality-accreditation/runtime-shell`): baseline‑скор, комплаенс, evidence, remediation, готовность.

## Данные / БД
`accreditation_records`, `accreditation_risk_alerts`, QA‑таблицы (`qa38a2rt01_a0382`).

## Проблемы
Дубль‑семейство `quality_accreditation` vs `accreditation`×3; FE route drift (19→27, P2).
