# Digital Certificates — Module Foundation Registry
# Maturity: L1 (A-023.1 foundation lift from L0)
# Category: Planned Expansion — Academic Services
# Action: A-023.1 — Academic/Education Level 1–2 Foundation Lift

## Purpose

The `digital_certificates` module manages the issuance, verification, and
revocation of tamper-evident digital academic credentials (degrees, diplomas,
course completion certificates, micro-credentials) within the multi-tenant
university platform.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `Certificate` | Issued credential record (type, recipient, issued date) |
| `CertificateTemplate` | Tenant-configurable template per award type |
| `VerificationToken` | One-time or persistent public verification link |
| `RevocationRecord` | Revocation entry with reason and authority |

## Planned Capabilities (roadmap)

- Certificate issuance upon degree/course completion trigger
- PDF/HTML generation from configurable template
- Public verification endpoint (no auth required)
- Revocation with cryptographic invalidation (future: Blockcerts / W3C VC)
- Blockchain anchoring hook (optional tenant-level config)
- Batch issuance for graduation events

## Dependencies

| Module | Relationship |
|---|---|
| `academic_records` | Degree completion trigger |
| `transcripts` | Supplemental data for diploma supplement |
| `enrollments` | Course completion trigger |
| `graduation` | Graduation ceremony batch event |

## Integration Points (L2 scope, not yet implemented)

- `POST /certificates/issue` — issue a certificate
- `GET /certificates/{id}` — retrieve certificate (authenticated)
- `GET /certificates/verify/{token}` — public verification
- `POST /certificates/{id}/revoke` — revoke a certificate

## Maturity Gate Checklist

- [x] L1: Module registered; key entities and dependencies documented
- [ ] L2: Pydantic schemas + service skeleton
- [ ] L3: Backend tests, tenant guard, FSM, events
- [ ] L4: REST router, frontend integration
