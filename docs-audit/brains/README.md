# Каталог Brain‑модулей

[← Индекс аудита](../README.md) · Верхнеуровневый обзор: [../07_BRAIN_MODULES.md](../07_BRAIN_MODULES.md)

Brain‑слой = централизованный движок принятия решений (`brain_core`) + доменные brain‑вертикали (runtime‑пакеты) + сигнальные реестры + digital twin. Все решения **человеко‑контролируемы** (никаких автономных исполнений).

## Файлы

| Brain | Файл | Модуль |
|-------|------|--------|
| Brain Core (движок) | [brain-core.md](brain-core.md) | `brain_core` |
| Digital Twin | [digital-twin.md](digital-twin.md) | `digital_twin` |
| Student Success Brain | [student-success.md](student-success.md) | `student_success_runtime` |
| Academic Operations Brain | [academic-operations.md](academic-operations.md) | `academic_operations_runtime` |
| Reporting / Ministry Brain | [reporting-ministry.md](reporting-ministry.md) | `reporting_runtime` |
| Executive Governance Brain | [executive-governance.md](executive-governance.md) | `executive_governance` |
| Research Science Brain | [research-science.md](research-science.md) | `research_science` |
| Quality Accreditation Brain | [quality-accreditation.md](quality-accreditation.md) | `quality_accreditation` |
| Сигнальные реестры (L2, 5) | [signal-registries.md](signal-registries.md) | `*_signal_registry` |

## Сводка

- **Сигнальных сценариев:** 66 · **решений:** 36 · **доменных brain‑вертикалей:** 6 · **сигнальных реестров L2:** 5.
- **Жизненный цикл:** signal intake → context build → classify → reason → policy guard → action plan → dispatch → outcome → learning.
- **Human gating:** ApprovalPolicy, human‑approved timetable, safe‑агенты, approval queue.
