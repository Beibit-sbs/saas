# Каталог Runtime Shells

[← Индекс аудита](../README.md) · Верхнеуровневый обзор: [../06_RUNTIME_SHELLS.md](../06_RUNTIME_SHELLS.md)

**Runtime Shell** = frontend‑дашборд + backend `runtime_shell_router.py`, агрегирующий real‑time состояние домена (`getRuntimeShell()`), без автономных действий.

## Файлы

| # | Runtime Shell | Файл | Brain |
|---|---------------|------|-------|
| 1 | Student Success | [student-success-shell.md](student-success-shell.md) | [../brains/student-success.md](../brains/student-success.md) |
| 2 | Academic Operations | [academic-operations-shell.md](academic-operations-shell.md) | [../brains/academic-operations.md](../brains/academic-operations.md) |
| 3 | Executive Governance | [executive-governance-shell.md](executive-governance-shell.md) | [../brains/executive-governance.md](../brains/executive-governance.md) |
| 4 | Quality Accreditation | [quality-accreditation-shell.md](quality-accreditation-shell.md) | [../brains/quality-accreditation.md](../brains/quality-accreditation.md) |
| 5 | Research Brain | [research-brain-shell.md](research-brain-shell.md) | [../brains/research-science.md](../brains/research-science.md) |
| 6 | Reporting Runtime | [reporting-runtime-shell.md](reporting-runtime-shell.md) | [../brains/reporting-ministry.md](../brains/reporting-ministry.md) |
| 7 | Innovation & Commercialization | [innovation-shell.md](innovation-shell.md) | — |
| 8 | Communications (частичный) | [communications-shell.md](communications-shell.md) | — |

Формат каждого файла: Назначение · Страницы · Backend · Frontend · Permissions · Связанные Brain Modules.

## Общие свойства
- Данные тянутся агрегирующим read‑эндпоинтом (`GET /runtime-shell`), permission `<domain>.summary.read`.
- Safety‑gates в ряде shell'ов — metadata‑only (нет живой синхронизации), честно помечены (`boundaryLabels.ts`).
- Каждый shell — пользовательское «окно» соответствующей Brain‑вертикали.
