import { describe, expect, it } from 'vitest';
import {
  SECURITY_ACCESS_COMPLIANCE_API_BASE,
  SECURITY_ACCESS_COMPLIANCE_BACKEND_ROUTE_COUNT,
  SECURITY_ACCESS_COMPLIANCE_PLANNED_ROUTE_COUNT,
  SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE,
  SECURITY_ACCESS_COMPLIANCE_SAFETY_FLAGS,
  SECURITY_ACCESS_COMPLIANCE_SOURCE_BACKEND_B1_COMMIT,
  SECURITY_ACCESS_COMPLIANCE_SOURCE_BACKEND_RUNTIME_COMMIT,
  SECURITY_ACCESS_COMPLIANCE_TABLE_COUNT,
} from '@/modules/security-access-compliance/constants';
import type {
  SacAbacEvidence,
  SacAccessGovernance,
  SacApiResult,
  SacAuditEventReview,
  SacBridgeFamily,
  SacComplianceControl,
  SacCrossVerticalBridge,
  SacDashboard,
  SacDataProtectionReadiness,
  SacIncidentReview,
  SacLimitations,
  SacLoginEventReview,
  SacMetadataContract,
  SacMfaReadiness,
  SacOverview,
  SacPermission,
  SacPermissionRecord,
  SacPolicyControlBridge,
  SacPrivacyReadiness,
  SacReadiness,
  SacRemediationTracking,
  SacRiskRegister,
  SacRbacEvidence,
  SacRole,
  SacRouteDefinition,
  SacRouteKey,
  SacSafetyFlags,
  SacSecurityException,
  SacSecurityIncident,
  SacSensitiveActionReview,
  SacSessionVisibility,
  SacTenantIsolationEvidence,
  SacVisitorAccessBridge,
  SacWorkflowDefinition,
} from '@/modules/security-access-compliance/types';

describe('Security / Access / Compliance types', () => {
  const safetyFlags: SacSafetyFlags = {
    fake_security_certification: false,
    fake_compliance_certification: false,
    legal_regulatory_compliance_claimed: false,
    soc_siem_replacement_claimed: false,
    fake_incident_resolution: false,
    fake_audit_proof: false,
    fake_penetration_test_result: false,
    fake_vulnerability_scan_result: false,
    fake_risk_score: false,
    hidden_user_risk_score_present: false,
    discriminatory_ranking_present: false,
    autonomous_enforcement_enabled: false,
    automatic_user_blocking_enabled: false,
    automatic_user_sanction_enabled: false,
    automatic_data_deletion_enabled: false,
    external_regulator_submission_enabled: false,
    production_security_claimed: false,
    human_review_required: true,
    incomplete_data: true,
    limitations: ['metadata-only'],
  };

  it('exports the expected safety flag shape', () => {
    expect(safetyFlags.fake_security_certification).toBe(false);
    expect(safetyFlags.human_review_required).toBe(true);
    expect(safetyFlags.limitations).toContain('metadata-only');
  });

  it('supports overview and readiness shapes', () => {
    const overview: SacOverview = {
      module: 'security_access_compliance',
      contract_version: 'A-043.3.FRONTEND',
      runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE,
      tenant_id: 1,
      safety_flags: safetyFlags,
      title: 'Security / Access / Compliance',
      summary: 'metadata only',
      route_count: SECURITY_ACCESS_COMPLIANCE_PLANNED_ROUTE_COUNT,
      backend_route_count: SECURITY_ACCESS_COMPLIANCE_BACKEND_ROUTE_COUNT,
      table_count: SECURITY_ACCESS_COMPLIANCE_TABLE_COUNT,
      permission_count: 44,
      bridge_count: 4,
      data_source: 'computed',
    };

    const readiness: SacReadiness = {
      module: 'security_access_compliance',
      contract_version: 'A-043.3.FRONTEND',
      runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE,
      tenant_id: 1,
      safety_flags: safetyFlags,
      title: 'Readiness',
      readiness_status: 'human_review_required',
      recommended_next_step: 'review metadata',
      missing_evidence: ['evidence-only'],
    };

    expect(overview.backend_route_count).toBe(47);
    expect(readiness.missing_evidence).toContain('evidence-only');
  });

  it('supports dashboard and limitations shapes', () => {
    const dashboard: SacDashboard = {
      module: 'security_access_compliance',
      contract_version: 'A-043.3.FRONTEND',
      runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE,
      tenant_id: 1,
      safety_flags: safetyFlags,
      title: 'Dashboard',
      summary: 'read-only',
      widgets: [],
      incomplete_data: true,
    };

    const limitations: SacLimitations = {
      module: 'security_access_compliance',
      contract_version: 'A-043.3.FRONTEND',
      runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE,
      tenant_id: 1,
      safety_flags: safetyFlags,
      title: 'Limitations',
      limitations: ['No production-ready security claim'],
    };

    expect(dashboard.incomplete_data).toBe(true);
    expect(limitations.limitations).toContain('No production-ready security claim');
  });

  it('supports role and permission record shapes', () => {
    const role: SacRole = { role: 'auditor', scope: 'read_only', permissions: ['security_access_compliance.overview.read'] };
    const permission: SacPermissionRecord = { permission: 'security_access_compliance.dashboard.read' };

    expect(role.permissions).toHaveLength(1);
    expect(permission.permission).toContain('dashboard.read');
  });

  it('supports route and workflow definitions', () => {
    const route: SacRouteDefinition = {
      key: 'overview' as SacRouteKey,
      title: 'Overview',
      route: '/console/security-access-compliance',
      requiredPermission: 'security_access_compliance.overview.read',
      backendEndpoints: ['GET /api/admin/security-access-compliance/overview'],
      primaryWidgets: ['governance-summary'],
      safetyBoundaryLabels: ['Human review required'],
      emptyState: 'empty',
      incompleteDataNotice: 'incomplete',
      permissionDeniedState: 'denied',
      noOverclaimFooter: ['No fake security certification'],
      humanReviewBadge: 'Human review required',
      noForbiddenUiActions: ['No certification action'],
    };

    const workflow: SacWorkflowDefinition = {
      key: 'incident-review',
      title: 'Incident review',
      routeKey: 'incident-review',
      summary: 'metadata only',
      humanReviewPoint: 'human review required',
    };

    expect(route.route).toContain('/console/security-access-compliance');
    expect(workflow.routeKey).toBe('incident-review');
  });

  it('supports bridge and audit-style shapes', () => {
    const bridge: SacBridgeFamily = {
      key: 'hr',
      title: 'HR bridge',
      routeKey: 'bridges',
      summary: 'metadata-only',
      backendEndpoint: 'GET /api/admin/security-access-compliance/bridges/hr',
      requiredPermission: 'security_access_compliance.bridges.hr',
    };

    const crossVertical: SacCrossVerticalBridge = {
      module: 'security_access_compliance',
      contract_version: 'A-043.3.FRONTEND',
      runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE,
      tenant_id: 1,
      safety_flags: safetyFlags,
      title: 'HR bridge',
      bridge_family: 'hr',
      endpoints: ['GET /api/admin/security-access-compliance/bridges/hr'],
    };

    const apiResult: SacApiResult<{ item: { title: string } }> = {
      module: 'security_access_compliance',
      contract_version: 'A-043.3.FRONTEND',
      runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE,
      tenant_id: 1,
      safety_flags: safetyFlags,
      item: { title: 'ok' },
    };

    expect(bridge.backendEndpoint).toContain('/bridges/hr');
    expect(crossVertical.bridge_family).toBe('hr');
    expect(apiResult.item.title).toBe('ok');
  });

  it('supports the remaining domain response types', () => {
    const responses: Array<
      SacAbacEvidence
      | SacAccessGovernance
      | SacAuditEventReview
      | SacComplianceControl
      | SacDataProtectionReadiness
      | SacIncidentReview
      | SacLoginEventReview
      | SacMetadataContract
      | SacMfaReadiness
      | SacPolicyControlBridge
      | SacPrivacyReadiness
      | SacRbacEvidence
      | SacSecurityException
      | SacSecurityIncident
      | SacSensitiveActionReview
      | SacSessionVisibility
      | SacTenantIsolationEvidence
      | SacVisitorAccessBridge
      | SacRiskRegister
      | SacRemediationTracking
    > = [
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'ABAC', evidence_status: 'metadata-only', limitations: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Access governance', summary: 'metadata-only', routes: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Audit', events: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Compliance controls', controls: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Data protection', evidence: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Incident review', reviews: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Login events', login_events: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Metadata contract', expected_table_count: 24, expected_route_count: 47, expected_permission_count: 44, permission_namespace: 'security_access_compliance.*' },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'MFA', readiness_status: 'ready', evidence_items: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Policy controls', policies: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Privacy readiness', evidence: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'RBAC', evidence_status: 'metadata-only', limitations: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Exceptions', exceptions: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Incidents', incidents: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Sensitive actions', reviews: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Sessions', sessions: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Tenant isolation', evidence_items: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Visitor access', visitors: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Risk register', risks: [] },
      { module: 'security_access_compliance', contract_version: 'A-043.3.FRONTEND', runtime_mode: SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE, tenant_id: 1, safety_flags: safetyFlags, title: 'Remediation', items: [] },
    ];

    expect(responses).toHaveLength(20);
  });
});
