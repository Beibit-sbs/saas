# Brain: Reporting / Ministry (Регуляторная отчётность)

[← Каталог Brain](README.md) · Модуль‑каталог: [../modules/README.md](../modules/README.md)

Модуль: `backend/app/modules/reporting_runtime/` · Prefix `/api/v1/reporting` · A‑049

## Назначение
Brain‑вертикаль регуляторной и министерской отчётности: готовность отчётов (Ministry / NOBD / рейтинги / регуляторные), аккредитационная отчётность, delivery‑аудит.

## Функции (сервисы, 8)
`runtime_accreditation`, `runtime_compliance`, `runtime_ministry`, `runtime_nobd`, `runtime_ranking`, `runtime_regulatory`, `runtime_dashboard`, `runtime_registry`.

## Входные данные
Сигналы `accreditation.status_changed`, `compliance.review.required`; данные аккредитации, NOBD‑датасеты, рейтинговые индикаторы, регуляторные дедлайны.

## Выходные данные
Готовность отчётов, реестр отчётов, delivery‑аудит; решение `accreditation_remediation`.

## Связанный Runtime Shell
`ReportingRuntimeShellPage` (`/console/reporting-runtime`): реестр/расписание отчётов, готовность Ministry/NOBD/ranking/regulatory, delivery‑аудит.

## Регуляторный контекст
KZ (NOBD, министерство). Интеграция `regulatory_reporting_integration` (L2), `government_services_integration`.

## Проблемы
Историческое закрытие (`A-049`), reworked валидация (`A-049.14 B2/B3`). Требует реверификации lineage.
