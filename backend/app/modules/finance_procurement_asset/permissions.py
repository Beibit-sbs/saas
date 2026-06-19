"""Finance / Procurement / Asset permission constants."""

from __future__ import annotations

OVERVIEW_READ = "finance_procurement_asset.overview.read"
READINESS_READ = "finance_procurement_asset.readiness.read"
LIMITATIONS_READ = "finance_procurement_asset.limitations.read"
DASHBOARD_READ = "finance_procurement_asset.dashboard.read"
BILLING_READ = "finance_procurement_asset.billing.read"
BILLING_EVIDENCE = "finance_procurement_asset.billing.evidence"
RECEIVABLES_READ = "finance_procurement_asset.receivables.read"
RECEIVABLES_METADATA = "finance_procurement_asset.receivables.metadata"
BUDGET_PLANS_READ = "finance_procurement_asset.budget_plans.read"
BUDGET_PLANS_MANAGE = "finance_procurement_asset.budget_plans.manage"
BUDGET_CONTROLS_READ = "finance_procurement_asset.budget_controls.read"
BUDGET_CONTROLS_REVIEW = "finance_procurement_asset.budget_controls.review"
PROCUREMENT_REQUESTS_READ = "finance_procurement_asset.procurement_requests.read"
PROCUREMENT_REQUESTS_MANAGE = "finance_procurement_asset.procurement_requests.manage"
PROCUREMENT_REVIEWS_READ = "finance_procurement_asset.procurement_reviews.read"
PROCUREMENT_REVIEWS_REVIEW = "finance_procurement_asset.procurement_reviews.review"
VENDORS_READ = "finance_procurement_asset.vendors.read"
VENDORS_MANAGE = "finance_procurement_asset.vendors.manage"
CONTRACTS_READ = "finance_procurement_asset.contracts.read"
CONTRACTS_EVIDENCE = "finance_procurement_asset.contracts.evidence"
PURCHASE_REQUESTS_READ = "finance_procurement_asset.purchase_requests.read"
PURCHASE_REQUESTS_MANAGE = "finance_procurement_asset.purchase_requests.manage"
PURCHASE_ORDERS_READ = "finance_procurement_asset.purchase_orders.read"
PURCHASE_ORDERS_METADATA = "finance_procurement_asset.purchase_orders.metadata"
ASSETS_READ = "finance_procurement_asset.assets.read"
ASSETS_METADATA = "finance_procurement_asset.assets.metadata"
ASSET_LIFECYCLE_READ = "finance_procurement_asset.asset_lifecycle.read"
ASSET_LIFECYCLE_MANAGE = "finance_procurement_asset.asset_lifecycle.manage"
INVENTORY_MOVEMENTS_READ = "finance_procurement_asset.inventory_movements.read"
INVENTORY_MOVEMENTS_METADATA = "finance_procurement_asset.inventory_movements.metadata"
PAYMENT_READINESS_READ = "finance_procurement_asset.payment_readiness.read"
PAYMENT_READINESS_EVIDENCE = "finance_procurement_asset.payment_readiness.evidence"
ERP_READINESS_READ = "finance_procurement_asset.erp_readiness.read"
ERP_READINESS_EVIDENCE = "finance_procurement_asset.erp_readiness.evidence"
BANK_READINESS_READ = "finance_procurement_asset.bank_readiness.read"
BANK_READINESS_EVIDENCE = "finance_procurement_asset.bank_readiness.evidence"
PAYMENT_GATEWAY_READINESS_READ = "finance_procurement_asset.payment_gateway_readiness.read"
PAYMENT_GATEWAY_READINESS_EVIDENCE = "finance_procurement_asset.payment_gateway_readiness.evidence"
PROVIDER_READINESS_READ = "finance_procurement_asset.provider_readiness.read"
PROVIDER_READINESS_EVIDENCE = "finance_procurement_asset.provider_readiness.evidence"
AUDIT_READ = "finance_procurement_asset.audit.read"
AUDIT_WRITE = "finance_procurement_asset.audit.write"
EVIDENCE_READ = "finance_procurement_asset.evidence.read"
EVIDENCE_WRITE = "finance_procurement_asset.evidence.write"
BRIDGES_EXECUTIVE_READ = "finance_procurement_asset.bridges.executive.read"
BRIDGES_HR_PAYROLL_READ = "finance_procurement_asset.bridges.hr_payroll.read"
BRIDGES_DOCUMENT_CONTRACTS_READ = "finance_procurement_asset.bridges.document_contracts.read"
BRIDGES_PROVIDER_READINESS_READ = "finance_procurement_asset.bridges.provider_readiness.read"
BRIDGES_STUDENT_FINANCE_READ = "finance_procurement_asset.bridges.student_finance.read"
BRIDGES_STUDENT_FINANCE_ACKNOWLEDGE = "finance_procurement_asset.bridges.student_finance.acknowledge"
METADATA_READ = "finance_procurement_asset.metadata.read"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        OVERVIEW_READ,
        READINESS_READ,
        LIMITATIONS_READ,
        DASHBOARD_READ,
        BILLING_READ,
        BILLING_EVIDENCE,
        RECEIVABLES_READ,
        RECEIVABLES_METADATA,
        BUDGET_PLANS_READ,
        BUDGET_PLANS_MANAGE,
        BUDGET_CONTROLS_READ,
        BUDGET_CONTROLS_REVIEW,
        PROCUREMENT_REQUESTS_READ,
        PROCUREMENT_REQUESTS_MANAGE,
        PROCUREMENT_REVIEWS_READ,
        PROCUREMENT_REVIEWS_REVIEW,
        VENDORS_READ,
        VENDORS_MANAGE,
        CONTRACTS_READ,
        CONTRACTS_EVIDENCE,
        PURCHASE_REQUESTS_READ,
        PURCHASE_REQUESTS_MANAGE,
        PURCHASE_ORDERS_READ,
        PURCHASE_ORDERS_METADATA,
        ASSETS_READ,
        ASSETS_METADATA,
        ASSET_LIFECYCLE_READ,
        ASSET_LIFECYCLE_MANAGE,
        INVENTORY_MOVEMENTS_READ,
        INVENTORY_MOVEMENTS_METADATA,
        PAYMENT_READINESS_READ,
        PAYMENT_READINESS_EVIDENCE,
        ERP_READINESS_READ,
        ERP_READINESS_EVIDENCE,
        BANK_READINESS_READ,
        BANK_READINESS_EVIDENCE,
        PAYMENT_GATEWAY_READINESS_READ,
        PAYMENT_GATEWAY_READINESS_EVIDENCE,
        PROVIDER_READINESS_READ,
        PROVIDER_READINESS_EVIDENCE,
        AUDIT_READ,
        AUDIT_WRITE,
        EVIDENCE_READ,
        EVIDENCE_WRITE,
        BRIDGES_EXECUTIVE_READ,
        BRIDGES_HR_PAYROLL_READ,
        BRIDGES_DOCUMENT_CONTRACTS_READ,
        BRIDGES_PROVIDER_READINESS_READ,
        BRIDGES_STUDENT_FINANCE_READ,
        BRIDGES_STUDENT_FINANCE_ACKNOWLEDGE,
        METADATA_READ,
    }
)

FINANCE_PROCUREMENT_ASSET_PERMISSIONS = sorted(ALL_PERMISSIONS)
FINANCE_PROCUREMENT_ASSET_PERMISSION_COUNT = 51
