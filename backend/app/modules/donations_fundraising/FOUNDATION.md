# Donations Fundraising — Module Foundation Registry
# Maturity: L1 (A-023.4 foundation lift from L0)
# Category: Planned Expansion — Finance / Fundraising
# Action: A-023.4 — Finance / Procurement / Assets Level 1–2 Foundation Lift

## Purpose

The `donations_fundraising` module defines tenant-scoped donation campaign
metadata, pledge tracking contracts, and finance handoff references.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `DonationCampaign` | Donation campaign metadata |
| `DonationPledge` | Pledge registration and status reference |
| `DonationSettlementRef` | Settlement handoff pointer |

## Planned Capabilities (roadmap)

- Register donation campaign metadata
- Record pledge reference status history
- Provide settlement handoff markers for finance reconciliation
- Expose non-destructive reporting contract inputs

## Dependencies

| Module | Relationship |
|---|---|
| `alumni_relations_ops` | Upstream campaign operations context |
| `payment_reconciliation` | Settlement coordination linkage |
| `invoices` | Reference-only finance document linkage |

## Safety Notes

- No automatic payment capture.
- No automatic invoice mutation.
- No automatic fund transfer behavior.

## Maturity Gate Checklist

- [x] L1: module foundation documented
- [ ] L2: schemas + service skeleton
- [ ] L3: tests + tenant guard + FSM/events
- [ ] L4: API/frontend/KPI integration
