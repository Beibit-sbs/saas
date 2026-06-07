"""Integration Provider Readiness backend foundation package."""

from __future__ import annotations

MODULE_NAME = "integration_provider_readiness"
API_PREFIX = "/api/admin/integration-provider-readiness"
RUNTIME_MODE = "READINESS_AND_GOVERNANCE_ONLY"
CONTRACT_VERSION = "A-046.2-RUNTIME"

EXPECTED_PROVIDER_COUNT = 14
EXPECTED_ENTITY_COUNT = 18
EXPECTED_TABLE_COUNT = 22
EXPECTED_WORKFLOW_COUNT = 12
EXPECTED_ROUTE_COUNT = 44
EXPECTED_PERMISSION_COUNT = 42
EXPECTED_DASHBOARD_COUNT = 6

PROVIDER_CONNECTED = False
LIVE_PROVIDER_CALLS = False
CREDENTIALS_STORED = False
EXTERNAL_SUBMISSION = False
SYNC_EXECUTION = False
FAKE_HEALTH_METRICS = False
FAKE_READINESS_METRICS = False
READINESS_ONLY = True

WORKFLOW_NAMES = (
	"Provider Registry Workflow",
	"Provider Profile Workflow",
	"Capability Matrix Workflow",
	"Readiness Assessment Workflow",
	"Evidence Collection Workflow",
	"Compliance Review Workflow",
	"Security Review Workflow",
	"Provider Health Visibility Workflow",
	"Provider Audit Review Workflow",
	"Integration Planning Workflow",
	"Exception and Risk Escalation Workflow",
	"Provider Dashboard Publication Workflow",
)

DASHBOARD_NAMES = (
	"Provider Overview",
	"Provider Readiness",
	"Capability Matrix",
	"Risk Dashboard",
	"Evidence Dashboard",
	"Integration Roadmap",
)

PROVIDER_CATALOG: tuple[dict[str, object], ...] = (
	{
		"provider_id": "UCE-024",
		"provider_name": "SIS (Student Information System)",
		"provider_type": "SIS",
		"readiness_level": "L4_PROVIDER_READINESS_STACK_COMPLETE",
		"future_scope": "L5 controlled live read integration, then L6 operational sync",
		"business_owner_role": "integration_admin",
		"technical_owner_role": "integration_admin",
		"security_owner_role": "security_admin",
		"auditor_visibility": True,
		"executive_visibility": True,
	},
	{
		"provider_id": "UCE-025",
		"provider_name": "ERP (Finance ERP)",
		"provider_type": "ERP",
		"readiness_level": "L4_PROVIDER_READINESS_STACK_COMPLETE",
		"future_scope": "L5 controlled posting/reconciliation integration",
		"business_owner_role": "integration_admin",
		"technical_owner_role": "integration_admin",
		"security_owner_role": "security_admin",
		"auditor_visibility": True,
		"executive_visibility": True,
	},
	{
		"provider_id": "UCE-106",
		"provider_name": "LMS",
		"provider_type": "LMS",
		"readiness_level": "L4_PROVIDER_READINESS_STACK_COMPLETE",
		"future_scope": "L5 controlled course/user/grade sync",
		"business_owner_role": "integration_admin",
		"technical_owner_role": "integration_admin",
		"security_owner_role": "security_admin",
		"auditor_visibility": True,
		"executive_visibility": True,
	},
	{
		"provider_id": "UCE-109",
		"provider_name": "EDS (Digital Signature)",
		"provider_type": "DIGITAL_SIGNATURE",
		"readiness_level": "L4_PROVIDER_READINESS_STACK_COMPLETE",
		"future_scope": "L5 controlled signing verification/exchange",
		"business_owner_role": "platform_admin",
		"technical_owner_role": "integration_admin",
		"security_owner_role": "security_admin",
		"auditor_visibility": True,
		"executive_visibility": True,
	},
	{
		"provider_id": "UCE-030",
		"provider_name": "eGov (Government Services)",
		"provider_type": "GOVERNMENT_SERVICES",
		"readiness_level": "L4_PROVIDER_READINESS_STACK_COMPLETE",
		"future_scope": "L5 controlled submission/exchange orchestration",
		"business_owner_role": "platform_admin",
		"technical_owner_role": "integration_admin",
		"security_owner_role": "security_admin",
		"auditor_visibility": True,
		"executive_visibility": True,
	},
	{
		"provider_id": "UCE-108",
		"provider_name": "IDP (Identity Provider)",
		"provider_type": "IDENTITY_PROVIDER",
		"readiness_level": "L4_PROVIDER_READINESS_STACK_COMPLETE",
		"future_scope": "L5 controlled SSO/federation connectivity",
		"business_owner_role": "platform_admin",
		"technical_owner_role": "integration_admin",
		"security_owner_role": "security_admin",
		"auditor_visibility": True,
		"executive_visibility": True,
	},
	{
		"provider_id": "UCE-027",
		"provider_name": "Email Gateway",
		"provider_type": "EMAIL_GATEWAY",
		"readiness_level": "L4_PROVIDER_READINESS_STACK_COMPLETE",
		"future_scope": "L5 controlled notification dispatch integration",
		"business_owner_role": "integration_admin",
		"technical_owner_role": "integration_admin",
		"security_owner_role": "security_admin",
		"auditor_visibility": True,
		"executive_visibility": True,
	},
	{
		"provider_id": "UCE-028",
		"provider_name": "SMS Gateway",
		"provider_type": "SMS_GATEWAY",
		"readiness_level": "L4_PROVIDER_READINESS_STACK_COMPLETE",
		"future_scope": "L5 controlled SMS dispatch integration",
		"business_owner_role": "integration_admin",
		"technical_owner_role": "integration_admin",
		"security_owner_role": "security_admin",
		"auditor_visibility": True,
		"executive_visibility": True,
	},
	{
		"provider_id": "UCE-110",
		"provider_name": "Payment Gateway",
		"provider_type": "PAYMENT_GATEWAY",
		"readiness_level": "L4_PROVIDER_READINESS_STACK_COMPLETE",
		"future_scope": "L5 controlled payment initiation/reconciliation integration",
		"business_owner_role": "platform_admin",
		"technical_owner_role": "integration_admin",
		"security_owner_role": "security_admin",
		"auditor_visibility": True,
		"executive_visibility": True,
	},
	{
		"provider_id": "UCE-113",
		"provider_name": "HR Provider",
		"provider_type": "HR_PAYROLL_PROVIDER",
		"readiness_level": "L4_PROVIDER_READINESS_STACK_COMPLETE",
		"future_scope": "L5 controlled HR/payroll exchange integration",
		"business_owner_role": "integration_admin",
		"technical_owner_role": "integration_admin",
		"security_owner_role": "security_admin",
		"auditor_visibility": True,
		"executive_visibility": True,
	},
	{
		"provider_id": "UCE-112",
		"provider_name": "Regulatory Reporting Provider",
		"provider_type": "REGULATORY_REPORTING",
		"readiness_level": "L4_PROVIDER_READINESS_STACK_COMPLETE",
		"future_scope": "L5 controlled filing/exchange integration",
		"business_owner_role": "platform_admin",
		"technical_owner_role": "integration_admin",
		"security_owner_role": "security_admin",
		"auditor_visibility": True,
		"executive_visibility": True,
	},
	{
		"provider_id": "UCE-029",
		"provider_name": "Biometric Device Provider",
		"provider_type": "BIOMETRIC_PROVIDER",
		"readiness_level": "PLANNED_PROVIDER_CANDIDATE",
		"future_scope": "L5 controlled attendance/access federation",
		"business_owner_role": "platform_admin",
		"technical_owner_role": "integration_admin",
		"security_owner_role": "security_admin",
		"auditor_visibility": True,
		"executive_visibility": True,
	},
	{
		"provider_id": "PRV-DEX-001",
		"provider_name": "Document Exchange Provider",
		"provider_type": "DOCUMENT_EXCHANGE_PROVIDER",
		"readiness_level": "PLANNED_PROVIDER_CANDIDATE",
		"future_scope": "L5 controlled secure document exchange",
		"business_owner_role": "platform_admin",
		"technical_owner_role": "integration_admin",
		"security_owner_role": "security_admin",
		"auditor_visibility": True,
		"executive_visibility": True,
	},
	{
		"provider_id": "PRV-AIG-001",
		"provider_name": "AI Gateway / Model Provider",
		"provider_type": "AI_GATEWAY_PROVIDER",
		"readiness_level": "PLANNED_PROVIDER_CANDIDATE",
		"future_scope": "L5 controlled model-provider routing readiness",
		"business_owner_role": "platform_admin",
		"technical_owner_role": "integration_admin",
		"security_owner_role": "security_admin",
		"auditor_visibility": True,
		"executive_visibility": True,
	},
)
