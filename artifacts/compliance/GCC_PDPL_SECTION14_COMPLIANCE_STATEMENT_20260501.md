# PDPL Section 14 Compliance Statement (GCC Enterprise Pack)

## Statement Purpose

This statement summarizes platform controls that support compliance with Saudi PDPL Section 14 obligations for lawful, controlled, and protected processing of personal data.

- Statement date (UTC): 2026-05-01
- System owner: Platform Engineering
- Review type: Technical control statement (non-legal advice)

## Control Position Summary

The platform implements defense-in-depth controls aligned with PDPL core principles:

- Access control and authorization:
  - Role + permission checks enforced at API boundaries
  - Admin write operations gated by explicit dashboard write permissions
- Tenant-scoped processing:
  - Tenant identifiers are required and propagated through service and persistence layers
  - Cross-tenant access is restricted and monitored
- Security and integrity:
  - Controlled backend execution via dockerized gate workflows
  - Release gate includes data safety and rollback readiness checks
- Auditability:
  - Operational and release evidence retained in artifacts and runbook logs

## Evidence Anchors

- Smoke validation gate: [scripts/platform_smoke_check.sh](../../scripts/platform_smoke_check.sh)
- Release safety gate: [scripts/release_gate.sh](../../scripts/release_gate.sh)
- Data layer integrity gate logs under [artifacts/audits](../audits)

## Residual Risk and Boundaries

- This statement maps technical safeguards to PDPL-oriented expectations.
- Final legal sufficiency depends on customer-specific data flows, contracts, and legal review.
- External systems integrated by customers are out of direct platform control scope.

## Attestation

Based on current evidence and gate outcomes, the platform demonstrates an operational control baseline that is suitable for PDPL-focused enterprise due diligence.
