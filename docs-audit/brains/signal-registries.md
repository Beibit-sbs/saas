# Сигнальные реестры (L2 Signal Registries)

[← Каталог Brain](README.md) · [Обзор Brain](../07_BRAIN_MODULES.md)

5 доменных сигнальных реестров — L2‑конверты (контракт A‑027.6), присвоены UCE‑ID. **Все запрещают автономное исполнение** (`HUMAN_APPROVAL_REQUIRED=True`, `BRAIN_EXECUTION_ALLOWED=False`).

| Реестр | Модуль | UCE‑ID | Домен | Назначение |
|--------|--------|--------|-------|-----------|
| Student Risk | `student_risk_signal_registry` | UCE‑049 | Student Success | Таксономия сигналов рисков студента |
| Curriculum Gap | `curriculum_gap_signal_registry` | UCE‑132 | Curriculum Governance | Сигналы пробелов учебного плана (A‑030.1: L3 readiness) |
| Finance Anomaly | `finance_anomaly_signal_registry` | UCE‑050 | Finance | Сигналы финансовых аномалий |
| Procurement Risk | `procurement_risk_signal_registry` | UCE‑129 | Procurement/Contracts/Assets | Сигналы рисков закупок |
| Academic Quality | `academic_quality_signal_registry` | UCE‑051 | Academic Affairs | Сигналы академического качества |

## Роль в архитектуре
Реестры задают **таксономию сигналов** домена (детерминированный envelope‑контракт), которую потребляют Brain Core и Digital Twin. Они не исполняют действий — только классифицируют/нормализуют сигналы для последующего человеко‑контролируемого решения.

## Входные / выходные данные
- **Вход:** доменные события/риск‑индикаторы.
- **Выход:** нормализованные сигналы с метаданными (tenant_scope, severity, governance_policy_reference).

## Проблемы
Часть реестров — на уровне L2/L3 readiness (не полный runtime). Требуют доведения детерминированной логики (см. `A-029.*`, `A-030.*`).
