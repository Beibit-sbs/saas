# GLOBAL-ROADMAP-R2 - Strong Vertical Inventory Re-Baseline and Production Readiness Direction

## Scope
This report re-baselines the authoritative strong-vertical inventory using `SBS_UB.md` as the source of truth, with supporting confirmation from `SBS_UB_UNIVERSITY_COMPLETENESS_EXPANSION_MAP.md`, `SBS_UB_STRATEGIC_EXECUTION_POLICY_20_STRONG_VERTICALS_BEFORE_PRODUCTION.md`, and `SBS_UB_EVIDENCE_INDEX.md`.

The goal is to answer four questions:
1. How many strong verticals are actually closed.
2. Which verticals are closed but need evidence normalization.
3. Which verticals are open or incomplete.
4. Whether the next direction should be continued vertical closure, Production Hardening, tracker cleanup, or human decision.

## Authoritative Baseline
The tracker already contains a closed inventory summary after the A-041.5 and A-042.0 sequence:

- `completed_vertical_count_before: 8`
- `closed_vertical_inventory: PASS (Executive Governance, Student Lifecycle, Academic Operations, Research / Science, Quality / Accreditation, HR / Staff Governance, Finance / Procurement / Asset, Document / Decree / Correspondence)`
- `candidate_options_reviewed: PASS (Student Services / Welfare / Support; Campus / Facilities / Dormitory / Access; Library / Learning Resources; Security / Access / Compliance; Integration / Provider Readiness; Executive Brain / Strategic Intelligence; Infrastructure / Operations / SRE)`

The tracker then adds additional closed baselines for:

- `Ministry / Regulatory Reporting Brain` with `vertical_status: CLOSED_BASELINED`
- `Integration / Provider Readiness` with `vertical_status: CLOSED`
- `Student Services / Welfare / Support` via the A-042.5 closure chain

The authoritative closure and selection chain also shows that later items such as Campus, Security, and Integration were still being selected or deferred at the time of those blocks, while A-053 was normalized as a superseded extension chain rather than a new independent strong vertical.

## Strong Closed Count
Strict strong-vertical count: `9`
strong_closed_count: `9`

Counted as strong closed verticals:
- Executive Governance
- Student Lifecycle
- Academic Operations
- Research / Science
- Quality / Accreditation
- HR / Staff Governance
- Finance / Procurement / Asset
- Document / Decree / Correspondence
- Ministry / Regulatory Reporting

Why this count is strict:
- Each item above has explicit closure evidence in the authoritative tracker.
- Each one is not merely selected or deferred; it is baselined or certified closed.
- A-053 is not counted as a new strong vertical because it is a superseded extension recovery chain over the already closed Research baseline.

## Closed But Needing Normalization
Strict normalization-only count: `0`
closed_but_needs_normalization_count: `0`

There is one borderline readiness lane worth calling out for inventory hygiene:
- Integration / Provider Readiness

It is closed, but it is structurally a provider-readiness / governance lane rather than a clean product vertical in the same sense as the core strong product closures. For a strict strong-vertical threshold, it should not be used to inflate the count. I am therefore keeping it out of the strong-closed total rather than treating it as a separate normalized strong vertical.

## Open Or Incomplete
Open or incomplete remaining candidate families in the authoritative inventory: `15`
open_or_partial_candidate_families: `15`

The tracker explicitly records `remaining_candidate_count: 15` in the A-044 inventory block. The concrete open/deferred families visible in the tracker include:
- Campus / Facilities / Housing / Transport
- Library / Archive / Knowledge Services
- Security / Access / Compliance
- Integration / Provider Readiness
- Communications / Notification / Community
- Career / Alumni / Employer Relations
- Learning / LMS / MOOC / Teaching Support
- Exam / Proctoring / Assessment Governance
- Legal / Contracts / Policy Governance
- Data Platform / Analytics / KPI Intelligence
- Executive Brain / Strategic Intelligence
- Infrastructure / Operations / SRE

That list is not a closure count; it is the remaining candidate inventory that still needs vertical decisioning and closure work.

## Superseded Or Stale Signals
- `A-053` / `Research & Innovation` is a superseded extension chain, classified in the tracker as `DUPLICATE_VERTICAL_NEEDS_SUPERSESSION`.
- `A-047.1` remains a stale continuation signal and should not be treated as a live execution prompt.

A-053 closure preservation: preserved; the A-053 chain remains closed and is not reopened in this inventory baseline.

These signals should not be counted as new strong verticals.

## Direction
Recommended direction: continue vertical closure toward 20 strong verticals.
recommended_next_action: `CONTINUE_VERTICAL_CLOSURE`

Reasoning:
- The authoritative strong-closed count is still below the policy threshold of approximately 20 fully closed product verticals before Production Hardening / Pilot Deployment.
- The remaining candidate inventory is still substantial.
- Production Hardening is premature if the count is based only on strict strong closures.
- Tracker cleanup is useful, but it is not a substitute for closing more true verticals.

Production Hardening assessment: not recommended yet.

## Decision
Final decision: `CONTINUE_VERTICAL_CLOSURE`

Secondary note:
- If the team wants to count readiness-only or superseded extension chains differently, that requires a human decision on inventory policy, not a tracker rewrite.

## Summary
- strong_closed_count: `9`
- closed_but_needs_normalization_count: `0`
- open_or_partial_candidate_families: `15`
- Superseded extension chains: `1` primary chain to exclude from strong-vertical counting
- recommended_next_action: `CONTINUE_VERTICAL_CLOSURE`
- Production Hardening assessment: not recommended yet