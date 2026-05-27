"""Security / Access / Compliance schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SacSafetyFlags(BaseModel):
    fake_security_certification: bool = False
    fake_compliance_certification: bool = False
    legal_regulatory_compliance_claimed: bool = False
    soc_siem_replacement_claimed: bool = False
    fake_incident_resolution: bool = False
    fake_audit_proof: bool = False
    fake_penetration_test_result: bool = False
    fake_vulnerability_scan_result: bool = False
    fake_risk_score: bool = False
    hidden_user_risk_score_present: bool = False
    discriminatory_ranking_present: bool = False
    autonomous_enforcement_enabled: bool = False
    automatic_user_blocking_enabled: bool = False
    automatic_user_sanction_enabled: bool = False
    automatic_data_deletion_enabled: bool = False
    external_regulator_submission_enabled: bool = False
    production_security_claimed: bool = False
    human_review_required: bool = True
    incomplete_data: bool = False
    limitations: list[str] = Field(default_factory=list)


class SacMetadataWriteRequest(BaseModel):
    record_key: str = Field(min_length=1, max_length=128)
    status: str = Field(default="active", min_length=1, max_length=64)
    metadata: dict = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    incomplete_data: bool = False


class SacBridgeWriteRequest(SacMetadataWriteRequest):
    bridge_key: str = Field(min_length=1, max_length=64)


class SacResponseBase(BaseModel):
    module: str
    contract_version: str
    runtime_mode: str
    tenant_id: int
    safety_flags: SacSafetyFlags


class SacCollectionResponse(SacResponseBase):
    items: list[dict] = Field(default_factory=list)


class SacOverviewResponse(SacCollectionResponse):
    pass


class SacReadinessResponse(SacCollectionResponse):
    pass


class SacDashboardResponse(SacCollectionResponse):
    pass


class SacLimitationsResponse(SacCollectionResponse):
    pass


class SacRoleResponse(SacCollectionResponse):
    pass


class SacPermissionResponse(SacCollectionResponse):
    pass


class SacAccessGovernanceResponse(SacCollectionResponse):
    pass


class SacRbacEvidenceResponse(SacCollectionResponse):
    pass


class SacAbacEvidenceResponse(SacCollectionResponse):
    pass


class SacSessionVisibilityResponse(SacCollectionResponse):
    pass


class SacLoginEventReviewResponse(SacCollectionResponse):
    pass


class SacMfaReadinessResponse(SacCollectionResponse):
    pass


class SacTenantIsolationEvidenceResponse(SacCollectionResponse):
    pass


class SacSecurityIncidentResponse(SacCollectionResponse):
    pass


class SacIncidentReviewResponse(SacCollectionResponse):
    pass


class SacRemediationTrackingResponse(SacCollectionResponse):
    pass


class SacRiskRegisterResponse(SacCollectionResponse):
    pass


class SacComplianceControlResponse(SacCollectionResponse):
    pass


class SacPolicyControlBridgeResponse(SacCollectionResponse):
    pass


class SacAuditEventReviewResponse(SacCollectionResponse):
    pass


class SacSensitiveActionReviewResponse(SacCollectionResponse):
    pass


class SacDataProtectionReadinessResponse(SacCollectionResponse):
    pass


class SacPrivacyReadinessResponse(SacCollectionResponse):
    pass


class SacSecurityExceptionResponse(SacCollectionResponse):
    pass


class SacVisitorAccessBridgeResponse(SacCollectionResponse):
    pass


class SacCrossVerticalBridgeResponse(SacCollectionResponse):
    pass


class SacMetadataContractResponse(SacResponseBase):
    expected_table_count: int
    expected_route_count: int
    expected_permission_count: int
    permission_namespace: str


class SacMutationResponse(SacResponseBase):
    item: dict
