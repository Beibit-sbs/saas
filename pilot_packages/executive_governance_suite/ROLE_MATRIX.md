# Executive Governance Suite Role Matrix

Role-only template. No real users, no names, no credentials, and no personal data are included.

## 1. Rector / President

- responsibilities: review Control Tower, review executive assignments, confirm governance visibility priorities
- allowed suite areas: Control Tower, assignment oversight, linked governance records, audit read, archive read
- forbidden actions: no fake KPI, no auto-signature, no autonomous decision, no hidden score override
- required permissions / permission groups: executive_governance_read, control_tower_read, assignment_oversight_read, audit_read, archive_read
- demo scenario involvement: opens and closes the executive demo story
- pilot training notes: reinforce incomplete/foundation metric labels and no production-ready claim

## 2. Vice Rector

- responsibilities: monitor delegated assignments, review SLA exposure, track linked document progress
- allowed suite areas: Control Tower read, assignment read, SLA visibility, linked workflow read, audit read
- forbidden actions: no auto-approval, no fake registry status, no provider integration claim
- required permissions / permission groups: executive_governance_read, delegated_assignment_read, sla_visibility_read, audit_read
- demo scenario involvement: reviews delegated execution state after rector overview
- pilot training notes: emphasize oversight scope, not execution ownership

## 3. Chief of Staff / Executive Secretary

- responsibilities: coordinate executive follow-up, link assignments to governance records, prepare briefing status
- allowed suite areas: assignment workflow, document and correspondence context, SLA visibility, audit/history
- forbidden actions: no fake evidence, no autonomous decision, no live dispatch claim
- required permissions / permission groups: assignment_manage, document_read, correspondence_read, sla_visibility_read, audit_read
- demo scenario involvement: links assignment to the supporting governance record
- pilot training notes: focus on traceability and evidence completeness

## 4. Chancellery Clerk

- responsibilities: register and route official records, maintain metadata quality, support archive handoff
- allowed suite areas: document workflow, decree workflow, correspondence routing, archive views
- forbidden actions: no fake sent/delivered state, no fake signature, no hard delete
- required permissions / permission groups: document_registry_manage, correspondence_routing_manage, archive_read
- demo scenario involvement: demonstrates workflow routing and metadata-only labels
- pilot training notes: reinforce metadata-only boundaries for signed, sent, and delivered labels

## 5. Department Director / Dean

- responsibilities: coordinate departmental execution, review evidence progress, watch overdue exposure
- allowed suite areas: assignment details, report/evidence views, linked records, SLA visibility
- forbidden actions: no signature claim, no autonomous reassignment, no fake KPI restatement
- required permissions / permission groups: owned_assignment_manage, evidence_read, sla_visibility_read
- demo scenario involvement: reviews departmental execution progress
- pilot training notes: keep departmental oversight separate from chancellery/legal control

## 6. Executor / Responsible Officer

- responsibilities: accept assignment, perform work, submit report, attach evidence, respond to revision
- allowed suite areas: assignment detail, report submission, evidence attachment, status history
- forbidden actions: no fake evidence, no approval bypass, no archive deletion
- required permissions / permission groups: assignment_accept, assignment_update_owned, report_submit, evidence_manage_owned
- demo scenario involvement: demonstrates acceptance and report/evidence submission
- pilot training notes: use placeholders only; no real personal data and no credentials

## 7. Document Controller

- responsibilities: maintain registry quality, coordinate lifecycle state, preserve archival metadata
- allowed suite areas: document workflow, decree registry, archive, audit history
- forbidden actions: no fake signature state, no unauthorized assignment mutation, no provider integration claim
- required permissions / permission groups: document_workflow_manage, archive_manage, audit_read
- demo scenario involvement: validates linked governance lifecycle and archive outcome
- pilot training notes: center lifecycle correctness and metadata integrity

## 8. Legal Reviewer

- responsibilities: review decrees and legal drafts, mark legal-review progress, verify approval-for-signing readiness
- allowed suite areas: decree lifecycle, legal review surfaces, supporting document context, audit read
- forbidden actions: no auto-approval, no fake legal decision, no signature fabrication
- required permissions / permission groups: decree_legal_review_manage, document_read, audit_read
- demo scenario involvement: shows legal review stage in decree flow
- pilot training notes: approval-for-signing remains metadata, not live signature execution

## 9. Internal Auditor

- responsibilities: inspect audit trail, evidence completeness, status history, archive integrity
- allowed suite areas: audit trail, archive, evidence review, Control Tower read
- forbidden actions: no operational mutation, no hard delete, no fake KPI normalization
- required permissions / permission groups: audit_read, archive_read, evidence_read, control_tower_read
- demo scenario involvement: closes the traceability story with control evidence
- pilot training notes: reinforce no hard delete and no hidden score boundaries

## 10. Platform Admin

- responsibilities: maintain tenant and RBAC setup, coordinate troubleshooting, backup expectations, rollback readiness
- allowed suite areas: platform admin guidance, permissions mapping, support planning, logs/request_id references
- forbidden actions: no real users, no credentials, no production-ready claim, no provider integration enabled
- required permissions / permission groups: platform_admin, rbac_admin, tenant_admin, audit_read
- demo scenario involvement: explains support boundaries and operational readiness limits
- pilot training notes: separate platform operations from business workflow authority
