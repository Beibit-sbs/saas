# Модуль: Finance / Procurement / Asset (Финансы, закупки, активы)

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `finance_procurement_asset/`, `budget_planning/`, `expense_controls/`, `procurement/`, `procurement_approval_workflow/`, `asset_inventory/`, `delinquency_collections/`, `online_payments/`, `payment_reconciliation/`, `finance_anomaly_signal_registry/`, `procurement_risk_signal_registry/`
Frontend: `frontend/modules/finance-procurement-asset/`, `budget-planning/`, `delinquency-collections/`, `asset-inventory/`
Вертикаль: **V07 Finance / Procurement / Asset** (RUNTIME_VERIFIED)

## Назначение
Финансово‑хозяйственный контур: бюджеты, расходы, закупки (PO), поставщики, активы/инвентаризация, задолженности, платежи, сверка.

## Бизнес‑функции
Бюджетное планирование/контроль · контроль расходов · закупки (request→approval→PO→delivery→asset) · управление поставщиками/контрактами · инвентаризация и амортизация · взыскание задолженностей · онлайн‑платежи и сверка · финансовый мост студента.

## Пользователи (роли)
`finance_procurement_asset_admin` (finance director), finance officer, procurement team; `auditor`.

## Страницы / Dashboard
- `/console/finance-procurement-asset/*` (~21: assets, budget-planning, budget-control, contracts, purchase-orders, purchase-requests, procurement-reviews, providers, vendors, receivables, student-finance, payment/erp/bank-readiness, inventory-movements, bridges, dashboard, audit).
- `/console/budget-planning`, `/console/delinquency-collections`, `/console/expense-controls`, `/console/asset-inventory`.

## Backend
- **Router:** `finance_procurement_asset/router.py` + `budget_planning`, `expense_controls`, `procurement`, `asset_inventory`, `delinquency_collections`, `online_payments`, `payment_reconciliation`.
- **Permissions:** `finance_procurement_asset/permissions.py` (65+).

## Database
`university_procurement_vendors/contracts/assets/inventory_items/risk_alerts`, `university_asset_inventory_items`, `university_asset_depreciation_records`, `university_asset_writeoff_records`, `budget_plans`, `budget_allocations`, `budget_overrun_alerts`, `expense_records`, `cost_centers`, `finance_expense_*`, `university_delinquency_records`, `payment_orders/transactions/refunds/failure_alerts`.

## API
`/api/admin/finance-procurement-asset/*`, `/api/admin/budget-planning`, `/api/admin/procurement`, `/api/admin/asset-inventory`, `/api/admin/delinquency-collections`. Permissions `budget.*`, `expense.*`, `procurement.*(approve)`, `asset_inventory.*`.

## Связанные модули
`billing`, `student_lifecycle` (student‑finance bridge), `hr_payroll`, `brain_core`, `campus_facilities` (finance_asset_bridge).

## Workflow
Закупка→PO→актив ([../08_WORKFLOWS.md](../08_WORKFLOWS.md) §9.5), задолженность ([../08_WORKFLOWS.md](../08_WORKFLOWS.md) §9.6).

## Brain / AI
Сигнальные реестры `finance_anomaly_signal_registry` (UCE‑050), `procurement_risk_signal_registry` (UCE‑129). Сигналы `finance.payment_overdue.detected`, `finance.expense.budget_exceeded`, `procurement.*`, `inventory.low_stock.detected`, `supply.risk.detected`; решения `payment_recovery`, `budget_overrun_prevention`, `procurement_approval_automation`, `procurement_supply_chain`, `inventory_low_stock`, `finance_operations_health`.

## Интеграции / Jobs / Flags
Интеграции: `finance_erp_integration`, `payment_gateway_integration` (L2). Jobs: `subscription_rollover`, KPI‑refresh. Флаги: динамические.

## Проблемы / Рекомендации
- **Реверифицирован** (52 backend‑теста прошли после починки red‑моделей). Наиболее «живая» вертикаль. Рекомендация: реализовать живые адаптеры ERP/платежей перед продом.
