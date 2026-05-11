# SBS_UB University Completeness Expansion Map

## 1. Executive Summary

A-027.0 is a planning-only audit that treats the existing 150 modules as the stabilized baseline core, not the final ceiling. The 25 controlled extensions remain a separate tracking plane. This document defines a realistic beyond-150 expansion roadmap for maximum University OS completeness, without runtime implementation or maturity inflation.

Key result:
- A new University Completeness Expansion Candidate Registry is defined with 54 candidates.
- The registry spans modules, workflows, integrations, reports, policy controls, Brain signals, autonomous workflow candidates, data entities, and audit evidence capabilities.
- Baseline metrics remain unchanged.

## 2. Current Baseline 150 Status

- Baseline target modules: 150
- Baseline maturity: L0=0, L1=0, L2=0, L3=55, L4=68, L5=25, L6=2
- Baseline arithmetic: PASS
- Baseline quality posture: lower-level cleanup complete; primary remaining effort is broad L3 to L4 operational visibility uplift and selected L4 to L5 governance/evidence uplift.

## 3. Existing Extension 25 Status

- Extension candidates: 25
- Tracking mode: separate controlled extension plane
- Baseline impact in this action: none
- Runtime state: planning-only unless separately evidenced in prior runtime waves

## 4. University Operating Domain Model

| Domain | Existing Coverage | Missing Modules | Missing Workflows | Missing Integrations | Missing Reports | Brain Signal Candidates | Priority |
|---|---|---|---|---|---|---|---|
| Governance / Rectorate / Strategy | medium | strategy_execution_office, policy_decision_register | rector escalation chain | egov policy feed | rector strategy dashboard | governance deviation signal | P0 |
| Academic Affairs | medium | curriculum_mapping, competency_framework | academic calendar governance | ministry curriculum sync | academic quality scorecard | curriculum risk signal | P0 |
| Student Lifecycle | strong | student_discipline, student_appeals | scholarship committee flow | biometric attendance sync | student lifecycle operations board | student risk signal | P0 |
| Admissions / Enrollment / Registrar | medium | admission_decision_committee_ops | admission exception workflow | platonus integration | admissions conversion dashboard | admissions anomaly signal | P1 |
| Curriculum / Programs / Syllabus / Competencies | weak | syllabus_management, program_outcome_registry | syllabus approval lifecycle | ministry standards sync | curriculum compliance dashboard | outcome gap signal | P0 |
| Teaching / LMS / Assessment / Exams | medium | teaching_observation, exam_board_governance | assessment moderation workflow | lms integration | assessment integrity dashboard | exam integrity drift signal | P1 |
| Faculty / HR / Workload / Payroll Interfaces | weak | staff_recruitment, staff_onboarding, employee_records, leave_management, performance_appraisal | recruitment to onboarding workflow | 1c integration, payroll gateway | HR operations dashboard | faculty overload signal | P0 |
| Research / Grants / Publications / Ethics / Labs | medium | grant_deliverable_tracking, research_data_management | ethics amendment workflow | external grant platform integration | research performance dashboard | grant execution risk signal | P1 |
| Finance / Budget / Billing / Procurement / Assets | strong | cost_center_management, financial_close_orchestration | month-end close workflow | bank gateway integration | finance executive dashboard | finance anomaly signal | P0 |
| Legal / Contracts / Compliance / Audit | medium | legal_case_tracking, regulatory_register | contract exception escalation | egov legal register sync | legal compliance dashboard | compliance breach signal | P0 |
| Campus / Facilities / Rooms / Maintenance / Safety | medium | dormitory_management, transport_shuttle_management | campus incident response workflow | IoT device integration | campus operations dashboard | facility risk signal | P1 |
| Library / Knowledge / Digital Repository | medium | archive_retention_management | archive disposal approval workflow | digital repository integration | library quality dashboard | content freshness signal | P2 |
| Student Support / Health / Counseling / Career / Alumni | medium | international_student_support | intervention follow-up workflow | external counseling referral integration | student success dashboard | support escalation signal | P0 |
| Communications / Notifications / Parent / Community | medium | correspondence_management | crisis communication workflow | sms and email gateway integration | communications reliability dashboard | notification failure signal | P1 |
| Security / IAM / Access Control / SOC / Incidents | medium | soc_case_management, privileged_access_management | security incident triage workflow | SIEM integration | security risk dashboard | security incident signal | P0 |
| IT Operations / DevOps / Platform / Observability | strong | patch_management, endpoint_inventory | change failure response workflow | monitoring federation integration | platform reliability dashboard | platform degradation signal | P1 |
| Data / Analytics / KPI / BI / Reporting | medium | data_catalog_governance | KPI certification workflow | BI warehouse integration | executive data trust dashboard | KPI quality signal | P0 |
| Quality Assurance / Accreditation / Regulatory | medium | accreditation_evidence_repository | nonconformance closure workflow | ministry accreditation integration | accreditation dashboard | accreditation risk signal | P0 |
| International Office / Mobility / Partnerships | weak | international_office, partnership_registry, mou_lifecycle | mobility approval workflow | visa status integration | international mobility dashboard | mobility risk signal | P0 |
| Dormitory / Housing / Transport / Parking | weak | dormitory_management, transport_shuttle_management | housing assignment workflow | access control turnstile integration | housing transport dashboard | housing occupancy risk signal | P1 |
| Events / Conferences / Public Relations | medium | public_relations_ops | event risk and escalation workflow | media distribution integration | event governance dashboard | event risk signal | P2 |
| Document Management / Archive / e-Signature | weak | document_workflow, order_decree_registry | decree routing workflow | e-signature integration | document SLA dashboard | document bottleneck signal | P0 |
| Integration Layer / External Systems | weak | integration_registry_ops | integration failure triage workflow | platonus, 1c, bank, egov, idp, lms | integration health dashboard | integration failure signal | P0 |
| AI / Brain / Agents / Automation | medium | brain_signal_registry, decision_audit_trail | brain human review workflow | model and vector platform integration | AI governance dashboard | cross-domain recommendation confidence signal | P0 |
| Ministry / Government / Regulatory Reporting | weak | ministry_pack_orchestrator | submission and correction workflow | government filing integration | ministry reporting dashboard | filing compliance risk signal | P0 |

## 5. Baseline Coverage Audit

| Domain | Baseline Modules Covering It | Coverage Quality | Gaps | Recommended Additions | Risk |
|---|---|---|---|---|---|
| Governance / Rectorate / Strategy | university_core, admin, workflows, plans | PARTIAL_BUT_NEEDS_WORKFLOWS | weak strategic execution and escalation model | strategy execution office + rector dashboard workflow | high |
| Academic Affairs | courses, programs, syllabus_governance, teaching_quality | MEDIUM | competency and outcomes traceability gaps | curriculum mapping + outcomes registry | high |
| Student Lifecycle | students, student_portal, student_services, interventions | STRONG | discipline/appeals orchestration gap | student appeals workflow + discipline case module | medium |
| Admissions / Enrollment / Registrar | admissions, enrollments, academic_records, transcripts | MEDIUM | committee and exception lifecycle gap | admissions committee module + workflow | medium |
| Curriculum / Programs / Syllabus / Competencies | programs, courses, syllabus_governance | WEAK | competency framework and outcome lineage missing | competency framework module | high |
| Teaching / LMS / Assessment / Exams | lms_content, lms_assessment_center, exam_governance, exam_proctoring | MEDIUM | teaching observation and moderation workflow missing | teaching observation module + moderation workflow | medium |
| Faculty / HR / Workload / Payroll Interfaces | faculty, hr_payroll, workload_management | WEAK | HR process stack incomplete | HR module family and payroll integration gateway | critical |
| Research / Grants / Publications / Ethics / Labs | research, research_grants, publications, research_ethics, lab_operations | MEDIUM | deliverable tracking and data governance | grant deliverable and data governance modules | medium |
| Finance / Budget / Billing / Procurement / Assets | billing, budget_planning, procurement, asset_inventory, online_payments | STRONG | financial close orchestration and tax/reporting depth | financial close workflow + tax reporting support | medium |
| Legal / Contracts / Compliance / Audit | contracts_hr, contracts_legal_repository, audit, pdpl | MEDIUM | legal case tracking and compliance control plane missing | legal case tracking + policy controls | high |
| Campus / Facilities / Rooms / Maintenance / Safety | facilities_work_orders, room_booking, parking, parking_enforcement | MEDIUM | dormitory and transport operations weak | dormitory and shuttle modules | high |
| Library / Knowledge / Digital Repository | library, library_circulation, digital_documents, knowledge_retrieval | MEDIUM | archive retention and repository governance weak | archive retention management | medium |
| Student Support / Health / Counseling / Career / Alumni | counseling, counseling_case_management, health_services, career_services, alumni | MEDIUM | integrated support orchestration incomplete | support coordination workflows | high |
| Communications / Notifications / Parent / Community | communications, notification_center, parent_portal, parent_engagement | MEDIUM | correspondence routing and crisis comms workflow missing | correspondence module + workflow | medium |
| Security / IAM / Access Control / SOC / Incidents | auth, rbac, access_control, security, security_operations, sso_saml | MEDIUM | SOC case and privileged access lifecycle missing | soc case management + PAM module | critical |
| IT Operations / DevOps / Platform / Observability | platform, platform_health, observability, jobs, feature_flags | STRONG | endpoint and patch governance missing | endpoint inventory + patch management | medium |
| Data / Analytics / KPI / BI / Reporting | analytics, platform_shared, model_evaluation | PARTIAL_BUT_NEEDS_WORKFLOWS | KPI certification and data catalog governance weak | data catalog governance + KPI certification workflow | high |
| Quality Assurance / Accreditation / Regulatory | accreditation, accreditation_compliance, academic_integrity | MEDIUM | accreditation evidence repository and closure workflows missing | accreditation evidence repository | high |
| International Office / Mobility / Partnerships | partnership-related capability is implicit only | MISSING | no full domain module family | international office, mobility, partnership modules | critical |
| Dormitory / Housing / Transport / Parking | housing, transport, parking, parking_permit_ops | WEAK | dormitory workflow depth missing | dormitory and housing assignment workflow | high |
| Events / Conferences / Public Relations | events_management, conference_management | MEDIUM | PR and media workflows missing | public relations ops module | medium |
| Document Management / Archive / e-Signature | digital_documents, records_hub | WEAK | document workflow and decree registry missing | document workflow stack | high |
| Integration Layer / External Systems | integrations, ai_gateway, ldap, sso_saml | WEAK | canonical external connectors missing | platonus, 1c, bank, egov, lms integrations | critical |
| AI / Brain / Agents / Automation | brain_core, ai_guardrails, ai_copilot_ops, prompt_management | PARTIAL_BUT_NEEDS_WORKFLOWS | signal registry and decision audit trail missing | Brain governance modules and workflows | high |
| Ministry / Government / Regulatory Reporting | reporting capability spread across modules only | MISSING | no dedicated ministry reporting orchestration | ministry pack orchestrator + dashboard | critical |

## 6. Extension Candidate Review

| Extension Candidate | Domain | Should Remain Extension? | Should Become Baseline? | Should Merge With Existing Module? | Priority | Rationale |
|---|---|---|---|---|---|---|
| digital_credentials_wallet | academic | yes | later | no | P1 | PROMOTE_TO_EXPANSION_MODULE for regulated credential proofs |
| micro_credentials_stack | academic | yes | later | no | P2 | KEEP_AS_EXTENSION_BACKLOG until curriculum competency stack matures |
| alumni_career_outcomes | student-success | yes | later | maybe with alumni | P2 | MERGE_INTO_EXISTING_MODULE is possible with alumni analytics |
| grant_peer_review | research | yes | later | no | P1 | PROMOTE_TO_EXPANSION_MODULE for research governance depth |
| research_data_governance | research | yes | later | no | P1 | PROMOTE_TO_EXPANSION_MODULE for compliance and reproducibility |
| llm_eval_harness | AI platform | yes | no | maybe with model_evaluation | P1 | MERGE_INTO_EXISTING_MODULE may reduce duplication |
| prompt_lifecycle_governance | AI platform | yes | no | no | P1 | PROMOTE_TO_EXPANSION_MODULE for controlled prompt governance |
| knowledge_retrieval_fabric | AI platform | yes | no | maybe with knowledge_retrieval | P2 | SPLIT_INTO_MULTIPLE_CAPABILITIES likely needed |
| ai_model_registry | AI platform | yes | no | maybe with model_evaluation | P1 | MERGE_INTO_EXISTING_MODULE viable in first wave |
| model_cost_optimizer | finance/AI | yes | later | maybe with ai_cost_governance | P2 | KEEP_AS_EXTENSION_BACKLOG pending finance signal maturity |
| copilot_safety_ops | AI governance | yes | later | no | P1 | PROMOTE_TO_EXPANSION_MODULE for safety workflows |
| policy_simulation_lab | governance | yes | later | no | P2 | KEEP_AS_EXTENSION_BACKLOG until policy data model stabilizes |
| incident_command_center | security/governance | yes | later | no | P1 | PROMOTE_TO_EXPANSION_MODULE due cross-domain impact |
| threat_intel_fusion | security | yes | later | no | P1 | PROMOTE_TO_EXPANSION_MODULE after SOC base modules |
| privacy_request_orchestrator | compliance | yes | later | no | P0 | PROMOTE_TO_EXPANSION_MODULE for regulatory obligations |
| data_retention_orchestrator | compliance | yes | later | no | P0 | PROMOTE_TO_EXPANSION_MODULE tied to legal requirements |
| billing_reconciliation_ops | finance | yes | later | maybe with billing | P1 | MERGE_INTO_EXISTING_MODULE possible for first implementation |
| revenue_leak_detection | finance | yes | later | maybe with billing analytics | P2 | KEEP_AS_EXTENSION_BACKLOG pending anomaly registry |
| procurement_vendor_risk | procurement | yes | later | maybe with procurement_approval_workflow | P1 | MERGE_INTO_EXISTING_MODULE first, split later if needed |
| classroom_iot_telemetry | campus | yes | no | no | P3 | DEFER until campus IoT integration baseline exists |
| energy_optimization_ops | campus | yes | no | no | P3 | DEFER after telemetry and facilities data quality improves |
| transport_fleet_ops | campus | yes | later | maybe with transport | P2 | MERGE_INTO_EXISTING_MODULE initially |
| admissions_yield_prediction | admissions | yes | later | maybe with admissions | P2 | KEEP_AS_EXTENSION_BACKLOG due model governance dependency |
| student_success_playbooks | student-success | yes | later | maybe with interventions | P1 | MERGE_INTO_EXISTING_MODULE for first controlled rollout |
| faculty_workload_optimizer | HR/faculty | yes | later | maybe with workload_management | P1 | MERGE_INTO_EXISTING_MODULE until HR stack is expanded |

## 7. Missing Capability Registry

## A-027.0 University Completeness Expansion Candidate Registry

| ID | Candidate Name | Type | Domain | Problem It Solves | Existing Coverage Gap | Priority | Target Initial Level | Recommended Wave | Notes |
|---|---|---|---|---|---|---|---:|---|---|
| UCE-001 | staff_recruitment | NEW_MODULE | Faculty / HR | hiring lifecycle and approvals | HR process stack missing | P0 | L2 | A-027.2 | tenant-safe recruitment contract |
| UCE-002 | staff_onboarding | NEW_MODULE | Faculty / HR | onboarding tasks and compliance | onboarding workflow missing | P0 | L2 | A-027.2 | links HR and IAM |
| UCE-003 | employee_records | NEW_MODULE | Faculty / HR | canonical employee profile and employment state | fragmented employee evidence | P0 | L2 | A-027.2 | no payroll mutation in first slice |
| UCE-004 | leave_management | NEW_MODULE | Faculty / HR | leave requests and balances governance | no leave lifecycle | P1 | L2 | A-027.2 | read-only visibility first |
| UCE-005 | performance_appraisal | NEW_MODULE | Faculty / HR | formal appraisal cycle | no formal appraisal module | P1 | L2 | A-027.3 | evidence-based reviews |
| UCE-006 | training_certification | NEW_MODULE | Faculty / HR | mandatory training tracking | compliance training gap | P1 | L2 | A-027.3 | policy-linked controls |
| UCE-007 | disciplinary_case_management | NEW_MODULE | Faculty / HR | disciplinary case lifecycle | no controlled disciplinary process | P1 | L2 | A-027.3 | strict human review boundaries |
| UCE-008 | position_budgeting | NEW_MODULE | Faculty / HR | staffing plan to budget alignment | HR-finance planning gap | P1 | L2 | A-027.3 | integrates with budget_planning |
| UCE-009 | document_workflow | NEW_MODULE | Document Management | formal document routing lifecycle | digital docs too generic | P0 | L2 | A-027.2 | decree/memo routing core |
| UCE-010 | internal_memo_routing | NEW_MODULE | Document Management | inter-office memo approvals | no memo workflow module | P1 | L2 | A-027.3 | can later merge with document_workflow |
| UCE-011 | order_decree_registry | NEW_MODULE | Governance / Document | legal orders and decrees register | no dedicated decree governance | P0 | L2 | A-027.2 | high compliance value |
| UCE-012 | archive_retention_management | NEW_MODULE | Library / Archive | retention schedules and disposal controls | retention controls weak | P0 | L2 | A-027.2 | policy-coupled module |
| UCE-013 | incoming_outgoing_correspondence | NEW_MODULE | Communications | official correspondence tracking | correspondence traceability gap | P1 | L2 | A-027.3 | SLA and audit required |
| UCE-014 | curriculum_mapping | NEW_MODULE | Academic Affairs | map courses to outcomes and competencies | curriculum traceability missing | P0 | L2 | A-027.2 | core accreditation driver |
| UCE-015 | syllabus_management | NEW_MODULE | Academic Affairs | syllabus lifecycle and version control | missing lifecycle workflow | P0 | L2 | A-027.2 | policy and approval bound |
| UCE-016 | competency_framework | NEW_MODULE | Academic Affairs | competency model governance | no competency catalog module | P0 | L2 | A-027.3 | supports outcomes tracking |
| UCE-017 | dormitory_management | NEW_MODULE | Campus Operations | housing allocation and occupancy control | housing depth weak | P1 | L2 | A-027.3 | tenant and room boundaries |
| UCE-018 | transport_shuttle_management | NEW_MODULE | Campus Operations | shuttle operations and incidents | transport operations gap | P2 | L2 | A-027.3 | integrates with transport |
| UCE-019 | international_office | NEW_MODULE | International Office | mobility, exchange, visa support operations | domain missing | P0 | L2 | A-027.2 | foundational international domain |
| UCE-020 | visa_support | SUBMODULE | International Office | visa case handling in international office | visa workflow absent | P1 | L2 | A-027.3 | submodule under UCE-019 |
| UCE-021 | unified_party_profile | DATA_ENTITY | Data / Master Data | shared identity graph for student-staff-parent-party links | cross-domain entity fragmentation | P1 | L1 | A-027.1 | entity governance only |
| UCE-022 | partnership_registry | NEW_MODULE | International Office | partnership and agreement inventory | no dedicated partnership module | P1 | L2 | A-027.3 | ties to legal/contracts |
| UCE-023 | mou_lifecycle | NEW_MODULE | International Office | MOU draft-review-sign-renew-close lifecycle | MOU process missing | P1 | L2 | A-027.3 | high inter-domain value |
| UCE-024 | platonus_integration | INTEGRATION | Integration Layer | SIS interop for enrollment and records | connector absent | P0 | L2 | A-027.2 | integration contract only |
| UCE-025 | one_c_integration | INTEGRATION | Integration Layer | HR/finance ERP synchronization | ERP connector absent | P0 | L2 | A-027.2 | strict anti-mutation start |
| UCE-026 | bank_gateway_integration | INTEGRATION | Integration Layer | payment and reconciliation exchange | payment rails incomplete | P0 | L2 | A-027.2 | read/verify first |
| UCE-027 | email_gateway_integration | INTEGRATION | Integration Layer | controlled outbound email channel | no unified gateway contract | P1 | L2 | A-027.3 | provider-safe boundaries |
| UCE-028 | sms_gateway_integration | INTEGRATION | Integration Layer | controlled outbound SMS channel | no unified gateway contract | P1 | L2 | A-027.3 | provider-safe boundaries |
| UCE-029 | biometric_device_integration | INTEGRATION | Integration Layer | access/attendance device federation | device integration gap | P2 | L2 | A-027.3 | tenant and privacy guard |
| UCE-030 | egov_integration | INTEGRATION | Integration Layer | government filing and verification exchange | ministry/reporting interop weak | P0 | L2 | A-027.2 | regulatory high priority |
| UCE-031 | rector_strategy_dashboard | REPORT_DASHBOARD | Governance | executive operational and strategic visibility | no unified rector dashboard | P0 | L1 | A-027.5 | depends on evidence contracts |
| UCE-032 | ministry_reporting_dashboard | REPORT_DASHBOARD | Regulatory Reporting | ministry pack status and evidence lineage | reporting orchestration weak | P0 | L1 | A-027.5 | no fake filing claims |
| UCE-033 | finance_executive_dashboard | REPORT_DASHBOARD | Finance | consolidated finance risk and close metrics | fragmented finance visibility | P1 | L1 | A-027.5 | fed by UCE-026 workflows |
| UCE-034 | student_success_dashboard | REPORT_DASHBOARD | Student Success | intervention outcomes and leading indicators | student support visibility fragmented | P1 | L1 | A-027.5 | links interventions and counseling |
| UCE-035 | security_risk_dashboard | REPORT_DASHBOARD | Security | SOC and IAM risk overview | no single security command view | P1 | L1 | A-027.5 | fed by SOC workflows |
| UCE-036 | ai_governance_dashboard | REPORT_DASHBOARD | AI Governance | AI model/prompt/risk transparency | governance visibility spread across modules | P1 | L1 | A-027.5 | evidence and policy first |
| UCE-037 | scholarship_committee_workflow | WORKFLOW | Student Lifecycle | committee approvals and exceptions | scholarship decision workflow incomplete | P1 | L2 | A-027.4 | orchestrates existing modules |
| UCE-038 | student_appeals_workflow | WORKFLOW | Student Lifecycle | appeals intake-review-resolution process | no formal appeals workflow | P1 | L2 | A-027.4 | human-review mandatory |
| UCE-039 | academic_calendar_governance_workflow | WORKFLOW | Academic Affairs | calendar proposal-review-publish approvals | no governance workflow | P1 | L2 | A-027.4 | avoids direct publish automation |
| UCE-040 | grant_deliverable_tracking_workflow | WORKFLOW | Research | deliverable deadlines and evidence closure | grant follow-through gap | P1 | L2 | A-027.4 | linked to research_grants |
| UCE-041 | financial_close_workflow | WORKFLOW | Finance | month-end close checklist and approvals | financial close lifecycle missing | P0 | L2 | A-027.4 | high executive value |
| UCE-042 | internal_audit_case_workflow | WORKFLOW | Audit / Compliance | audit case handling and remediation closure | audit process fragmentation | P0 | L2 | A-027.4 | ties to legal and policy controls |
| UCE-043 | campus_incident_response_workflow | WORKFLOW | Campus Operations | incident triage and escalation routing | emergency workflows fragmented | P1 | L2 | A-027.4 | cross-module orchestration |
| UCE-044 | emergency_drill_workflow | WORKFLOW | Campus Operations | preparedness drill planning and evidence | no drill lifecycle module | P2 | L2 | A-027.4 | evidence-focused first |
| UCE-045 | data_privacy_request_policy | POLICY_CONTROL | Compliance | DSAR response obligations and SLA policy | policy governance not explicit | P0 | L1 | A-027.1 | control definition only |
| UCE-046 | consent_management_policy | POLICY_CONTROL | Compliance | legal consent model and revocation handling | consent control missing | P0 | L1 | A-027.1 | prerequisite for outreach automation |
| UCE-047 | third_party_risk_policy | POLICY_CONTROL | Security / Legal | vendor and partner risk control baseline | third-party governance weak | P1 | L1 | A-027.1 | policy first, implementation later |
| UCE-048 | data_retention_policy_control | POLICY_CONTROL | Compliance | retention categories and legal hold controls | retention governance gap | P0 | L1 | A-027.1 | paired with UCE-012 |
| UCE-049 | student_risk_signal_registry | BRAIN_SIGNAL | Student Success | normalized student risk signal definitions | no central signal registry | P1 | L1 | A-029 | candidate-only, no execution |
| UCE-050 | finance_anomaly_signal_registry | BRAIN_SIGNAL | Finance | normalized finance anomaly signal taxonomy | finance signal fragmentation | P1 | L1 | A-029 | candidate-only, no execution |
| UCE-051 | academic_quality_signal_registry | BRAIN_SIGNAL | Academic Affairs | quality and outcome signal definitions | quality signal gap | P1 | L1 | A-029 | candidate-only, no execution |
| UCE-052 | security_risk_signal_registry | BRAIN_SIGNAL | Security | security threat and control signal taxonomy | SOC signal standardization missing | P1 | L1 | A-029 | candidate-only, no execution |
| UCE-053 | safe_autonomous_notification_agent | AUTONOMOUS_WORKFLOW_CANDIDATE | AI / Automation | proposes low-risk notification drafts for approval | no safe autonomous candidate lane | P2 | L1 | A-030 | human approval required |
| UCE-054 | brain_decision_audit_trail | AUDIT_EVIDENCE_CAPABILITY | AI Governance | captures recommendation-to-decision lineage | no unified decision evidence chain | P0 | L1 | A-029 | mandatory before autonomy expansion |

Registry summary counts:
- total candidates: 54
- NEW_MODULE: 20
- WORKFLOW: 8
- INTEGRATION: 7
- REPORT_DASHBOARD: 6
- POLICY_CONTROL: 4
- BRAIN_SIGNAL: 4
- AUTONOMOUS_WORKFLOW_CANDIDATE: 1
- SUBMODULE: 1
- DATA_ENTITY: 1
- AUDIT_EVIDENCE_CAPABILITY: 1

## 8. Coverage Score by Domain

Scoring scale: 0-5 (0 missing, 5 excellent).

| Domain | Module Coverage | Workflow Coverage | Integration Coverage | Reports | Compliance | Brain Signals | Security/Tenant | Overall Score | Gap Severity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Governance / Rectorate / Strategy | 2 | 2 | 1 | 1 | 3 | 2 | 3 | 2.0 | HIGH |
| Academic Affairs | 2 | 1 | 1 | 1 | 3 | 2 | 3 | 1.9 | CRITICAL |
| Student Lifecycle | 3 | 2 | 1 | 2 | 3 | 2 | 3 | 2.3 | HIGH |
| Admissions / Enrollment / Registrar | 3 | 2 | 1 | 1 | 3 | 2 | 3 | 2.1 | HIGH |
| Curriculum / Programs / Syllabus / Competencies | 2 | 1 | 1 | 1 | 3 | 1 | 3 | 1.7 | CRITICAL |
| Teaching / LMS / Assessment / Exams | 3 | 2 | 1 | 2 | 3 | 2 | 3 | 2.3 | HIGH |
| Faculty / HR / Workload / Payroll Interfaces | 1 | 1 | 1 | 1 | 2 | 1 | 3 | 1.4 | CRITICAL |
| Research / Grants / Publications / Ethics / Labs | 3 | 2 | 1 | 2 | 3 | 2 | 3 | 2.3 | HIGH |
| Finance / Budget / Billing / Procurement / Assets | 4 | 2 | 2 | 2 | 3 | 2 | 4 | 2.7 | MEDIUM |
| Legal / Contracts / Compliance / Audit | 3 | 2 | 1 | 2 | 3 | 1 | 4 | 2.3 | HIGH |
| Campus / Facilities / Rooms / Maintenance / Safety | 3 | 2 | 1 | 2 | 2 | 1 | 3 | 2.0 | HIGH |
| Library / Knowledge / Digital Repository | 3 | 1 | 1 | 1 | 2 | 1 | 3 | 1.7 | HIGH |
| Student Support / Health / Counseling / Career / Alumni | 3 | 2 | 1 | 2 | 2 | 2 | 3 | 2.1 | HIGH |
| Communications / Notifications / Parent / Community | 3 | 2 | 2 | 2 | 2 | 1 | 3 | 2.1 | HIGH |
| Security / IAM / Access Control / SOC / Incidents | 3 | 2 | 2 | 2 | 3 | 2 | 4 | 2.6 | MEDIUM |
| IT Operations / DevOps / Platform / Observability | 4 | 2 | 2 | 2 | 2 | 2 | 4 | 2.6 | MEDIUM |
| Data / Analytics / KPI / BI / Reporting | 3 | 1 | 2 | 2 | 2 | 2 | 3 | 2.1 | HIGH |
| Quality Assurance / Accreditation / Regulatory | 3 | 2 | 1 | 2 | 3 | 2 | 3 | 2.3 | HIGH |
| International Office / Mobility / Partnerships | 0 | 0 | 1 | 0 | 2 | 1 | 2 | 0.9 | CRITICAL |
| Dormitory / Housing / Transport / Parking | 2 | 1 | 1 | 1 | 2 | 1 | 3 | 1.6 | HIGH |
| Events / Conferences / Public Relations | 2 | 1 | 1 | 1 | 2 | 1 | 3 | 1.6 | HIGH |
| Document Management / Archive / e-Signature | 2 | 1 | 1 | 1 | 3 | 1 | 3 | 1.7 | HIGH |
| Integration Layer / External Systems | 1 | 1 | 1 | 1 | 2 | 1 | 3 | 1.4 | CRITICAL |
| AI / Brain / Agents / Automation | 3 | 2 | 1 | 2 | 3 | 2 | 3 | 2.3 | HIGH |
| Ministry / Government / Regulatory Reporting | 0 | 1 | 1 | 1 | 3 | 1 | 3 | 1.4 | CRITICAL |

## 9. Candidate Type Decision Rules

| Candidate Type | Criteria | Example | Initial Maturity Target |
|---|---|---|---|
| NEW_MODULE | owns distinct data, lifecycle, permissions, and domain reports | staff_recruitment | L2 |
| SUBMODULE | bounded capability under a larger parent domain module | visa_support under international_office | L2 |
| WORKFLOW | orchestrates existing modules without independent primary data ownership | financial_close_workflow | L2 |
| INTEGRATION | primary purpose is external-system connectivity | platonus_integration | L2 |
| REPORT_DASHBOARD | aggregates existing evidence for visibility | rector_strategy_dashboard | L1 |
| POLICY_CONTROL | codifies compliance and governance constraints | data_retention_policy_control | L1 |
| BRAIN_SIGNAL | derived insight/recommendation candidate without primary data ownership | finance_anomaly_signal_registry | L1 |
| AUTONOMOUS_WORKFLOW_CANDIDATE | safe, bounded automation candidate requiring mandatory human approval | safe_autonomous_notification_agent | L1 |
| DATA_ENTITY | shared master-data structure used by multiple modules | unified_party_profile | L1 |
| AUDIT_EVIDENCE_CAPABILITY | cross-cutting lineage and audit evidence substrate | brain_decision_audit_trail | L1 |

## 10. Expansion Waves

| Wave | Purpose | Candidate Count | Scope | Expected Output | Maturity Target |
|---|---|---:|---|---|---|
| A-027.1 | controlled expansion registry finalization and canonicalization | 54 | classify candidates and lock governance rules | approved canonical registry and decision rules | L1 planning artifacts |
| A-027.2 | new modules L1/L2 foundation batch 1 | 10-14 | P0 modules and critical integrations | foundational service contracts and tenant-safe scaffolds | L2 |
| A-027.3 | new modules L1/L2 foundation batch 2 | 10-14 | remaining P1 modules and integration connectors | additional contracts and policy-bound scaffolds | L2 |
| A-027.4 | L2 to L3 deterministic logic batch | 12-18 | selected modules and workflows | deterministic service logic and safety boundaries | L3 |
| A-027.5 | L3 to L4 operational visibility batch | 10-16 | admin/API/report visibility for selected domains | route/report visibility with security checks | L4 |
| A-028 | killer workflow implementation wave | 8-12 | cross-module rector/ministry/admin workflows | bounded, testable cross-module orchestration | L3-L4 |
| A-029 | strategic Brain core wave | 8-10 | signal registries, evidence lineage, review queue | governance-ready Brain candidates, no autonomous critical execution | L4-L5 readiness |
| A-030 | human-approved autonomous wave | 3-6 | low-risk safe autonomy pilots | human-approved autonomous workflow candidates | controlled L4-L5 readiness |

## 11. Prioritization Matrix

| Priority | Rule | Typical Candidate Types | Delivery Horizon |
|---|---|---|---|
| P0 | legal/regulatory, core operations, or critical domain missing | NEW_MODULE, INTEGRATION, POLICY_CONTROL, WORKFLOW | A-027.1 to A-027.3 |
| P1 | high-value operational depth and reporting uplift | NEW_MODULE, WORKFLOW, REPORT_DASHBOARD, BRAIN_SIGNAL | A-027.3 to A-027.5 |
| P2 | important but dependency-heavy or lower immediate impact | REPORT_DASHBOARD, INTEGRATION, AUTONOMOUS_WORKFLOW_CANDIDATE | A-028 onward |
| P3 | optional/later or exploratory | AUTONOMOUS_WORKFLOW_CANDIDATE, niche modules | post A-030 |

## 12. Brain / Signal / Agent Candidate Map

| Candidate | Type | Domain | Notes |
|---|---|---|---|
| student_risk_signal_registry | BRAIN_SIGNAL | Student Success | candidate-only signal taxonomy |
| finance_anomaly_signal_registry | BRAIN_SIGNAL | Finance | candidate-only anomaly taxonomy |
| academic_quality_signal_registry | BRAIN_SIGNAL | Academic Affairs | candidate-only quality signal set |
| security_risk_signal_registry | BRAIN_SIGNAL | Security | candidate-only security signal set |
| safe_autonomous_notification_agent | AUTONOMOUS_WORKFLOW_CANDIDATE | AI / Automation | no autonomous critical action; human approval mandatory |
| brain_decision_audit_trail | AUDIT_EVIDENCE_CAPABILITY | AI Governance | prerequisite evidence layer for later autonomy |

## 13. Integration Candidate Map

| Candidate | External System Class | Initial Target | Risk |
|---|---|---|---|
| platonus_integration | SIS | L2 | medium |
| one_c_integration | ERP/HR/Finance | L2 | high |
| bank_gateway_integration | Banking | L2 | high |
| email_gateway_integration | Messaging | L2 | medium |
| sms_gateway_integration | Messaging | L2 | medium |
| biometric_device_integration | Device/Access | L2 | medium |
| egov_integration | Government | L2 | high |

## 14. Dashboard / Report Candidate Map

| Candidate | Primary Persona | Data Dependency | Initial Target |
|---|---|---|---|
| rector_strategy_dashboard | rectorate | cross-domain KPIs and evidence | L1 |
| ministry_reporting_dashboard | compliance and reporting office | regulatory payloads and lineage | L1 |
| finance_executive_dashboard | finance leadership | reconciliation and close workflows | L1 |
| student_success_dashboard | student success office | intervention and support outcomes | L1 |
| security_risk_dashboard | security operations | IAM/SOC indicators | L1 |
| ai_governance_dashboard | AI governance committee | model/prompt/signal evidence | L1 |

## 15. Compliance / Policy Control Candidate Map

| Candidate | Scope | Why Needed | Initial Target |
|---|---|---|---|
| data_privacy_request_policy | DSAR lifecycle and SLA | legal requirement and auditability | L1 |
| consent_management_policy | consent capture and revocation | lawful processing boundary | L1 |
| third_party_risk_policy | vendor and partner control baseline | procurement and legal risk control | L1 |
| data_retention_policy_control | retention and legal hold controls | compliance and evidence integrity | L1 |

## 16. Anti-Inflation Rules

- No candidate in this map is treated as implemented.
- No new candidate is assigned above L1/L2 without runtime evidence.
- No fake Brain execution claim.
- No fake autonomous workflow claim.
- No fake integration claim.
- No fake compliance certification claim.
- No fake dashboard/report claim.
- Baseline 150 and extension 25 remain separate from expansion registry.
- Expansion registry is roadmap-only until future implementation waves produce evidence.

## 17. Next Action

- Next action id: A-027.1
- Action title: Controlled Expansion Registry and New Module Canonicalization
- Scope: planning and canonicalization only; no runtime code.

## A-027.0.B1 — Deep University Completeness Expansion Sweep

### Why B1 Was Needed

- The initial A-027.0 registry (54 candidates) was intentionally conservative.
- University OS completeness requires deeper subdomain coverage across HR, registrar, document governance, security operations, international office, ministry reporting, and Brain/evidence control planes.
- User strategy is explicit: baseline 150 is not a ceiling.

### Expanded Domain Granularity

Deep-sweep audit expanded coverage decisions across 40 domains:

1. Governance / Rectorate / Strategy
2. Academic Affairs
3. Registrar / Student Records
4. Admissions / Enrollment
5. Curriculum / Programs / Competencies
6. Syllabus / Course Management
7. Teaching Quality
8. LMS / Digital Learning
9. Assessment / Exams / Proctoring
10. Faculty Lifecycle
11. HR / Personnel
12. Payroll / Position Budgeting Interfaces
13. Workload / Timetable / Capacity
14. Research / Grants / Publications
15. Labs / Equipment / Research Data
16. Ethics / Compliance / IP / Tech Transfer
17. Finance / Budget / Billing
18. Procurement / Contracts / Assets
19. Legal / Internal Audit
20. Document Workflow / Archive / EDS
21. Campus / Facilities / Maintenance
22. Dormitory / Housing
23. Transport / Parking
24. Security / Access Control / SOC
25. IAM / Federation / Privileged Access
26. IT Operations / DevOps / Release Governance
27. Data / BI / KPI / Reporting
28. Quality Assurance / Accreditation
29. Ministry / Government / Regulatory Reporting
30. International Office / Mobility / Partnerships
31. Student Life / Clubs / Discipline / Appeals
32. Student Support / Health / Counseling
33. Career / Alumni / Employer Relations
34. Communications / Notifications / PR
35. Library / Repository / Knowledge
36. Integration Layer / External Systems
37. AI Governance / Brain / Agents
38. Risk Management / Incident Management
39. Sustainability / ESG / Safety
40. Commercialization / Continuing Education / Online Programs

### Added Candidate Registry (UCE-055 to UCE-149)

| UCE ID | Candidate Name | Type | Domain | Problem It Solves | Existing Coverage Gap | Priority | Target Initial Level | Recommended Wave | Notes |
|---|---|---|---|---|---|---|---:|---|---|
| UCE-055 | staff_recruitment | NEW_MODULE | HR / Personnel | hiring request-to-offer lifecycle | no dedicated recruitment lifecycle | P0 | L2 | A-027.2 | tenant-safe contracts only |
| UCE-056 | staff_onboarding | NEW_MODULE | Faculty Lifecycle | onboarding checkpoints and policy tasks | no structured onboarding module | P0 | L2 | A-027.2 | links HR and IAM controls |
| UCE-057 | staff_probation_review | NEW_MODULE | Faculty Lifecycle | probation evaluation and outcomes | probation governance gap | P1 | L2 | A-027.3 | human review required |
| UCE-058 | employee_records | NEW_MODULE | HR / Personnel | canonical employment profile lifecycle | fragmented HR evidence | P0 | L2 | A-027.2 | no payroll mutation in first slice |
| UCE-059 | leave_management | NEW_MODULE | HR / Personnel | leave request and approval lifecycle | leave process missing | P1 | L2 | A-027.3 | policy-bound leave rules |
| UCE-060 | timesheet_management | NEW_MODULE | HR / Personnel | timesheet capture and approval | no unified timesheet controls | P1 | L2 | A-027.3 | deterministic approvals |
| UCE-061 | faculty_attestation | NEW_MODULE | Faculty Lifecycle | yearly faculty attestation and compliance | attestation workflow missing | P1 | L2 | A-027.3 | evidence-first design |
| UCE-062 | faculty_promotion | NEW_MODULE | Faculty Lifecycle | promotion dossier and committee outcomes | no promotion lifecycle module | P1 | L2 | A-027.3 | strong audit trail needed |
| UCE-063 | performance_appraisal | NEW_MODULE | Faculty Lifecycle | appraisal goals, cycles, and outcomes | appraisal stack incomplete | P1 | L2 | A-027.3 | human-reviewed scoring only |
| UCE-064 | training_certification | NEW_MODULE | Faculty Lifecycle | mandatory training completion tracking | training governance gap | P1 | L2 | A-027.3 | compliance-linked controls |
| UCE-065 | disciplinary_case_management | NEW_MODULE | Faculty Lifecycle | disciplinary case intake-review-resolution | no controlled disciplinary module | P1 | L2 | A-027.3 | strict safety boundaries |
| UCE-066 | succession_planning | NEW_MODULE | Governance / HR | leadership continuity planning | succession governance missing | P2 | L2 | A-027.3 | planning-only first |
| UCE-067 | teaching_load_contracts | NEW_MODULE | Workload / Timetable / Capacity | formal teaching load obligations | workload contract gap | P1 | L2 | A-027.3 | links faculty and timetable |
| UCE-068 | adjunct_faculty_management | NEW_MODULE | Faculty Lifecycle | adjunct engagement and contract states | adjunct lifecycle missing | P1 | L2 | A-027.3 | tenant and legal boundaries |
| UCE-069 | vacancy_planning | NEW_MODULE | HR / Personnel | planned vacancy forecast and approvals | staffing planning gap | P2 | L2 | A-027.3 | tied to position budgets |
| UCE-070 | staff_exit_offboarding | NEW_MODULE | HR / Personnel | offboarding task and entitlement closure | offboarding process missing | P1 | L2 | A-027.3 | IAM and asset closure links |
| UCE-071 | program_learning_outcomes | NEW_MODULE | Curriculum / Programs / Competencies | program-level outcomes catalog | outcomes traceability gap | P0 | L2 | A-027.2 | accreditation-critical |
| UCE-072 | course_learning_outcomes | NEW_MODULE | Curriculum / Programs / Competencies | course outcome definitions and mapping | CLO governance missing | P0 | L2 | A-027.2 | ties to syllabus and assessment |
| UCE-073 | elective_course_selection | NEW_MODULE | Academic Affairs | elective demand and approval lifecycle | elective workflow incomplete | P1 | L2 | A-027.3 | bounded selection policy |
| UCE-074 | prerequisite_management | NEW_MODULE | Curriculum / Programs / Competencies | prerequisite rule governance | prerequisite rule engine missing | P1 | L2 | A-027.3 | deterministic validation boundaries |
| UCE-075 | transfer_credit_management | NEW_MODULE | Registrar / Student Records | transfer credit evaluation workflow | transfer credit lifecycle missing | P1 | L2 | A-027.3 | human-approved evaluation |
| UCE-076 | course_catalog_management | NEW_MODULE | Academic Affairs | versioned course catalog publication lifecycle | no dedicated catalog module | P1 | L2 | A-027.3 | no direct publish automation |
| UCE-077 | thesis_dissertation_management | NEW_MODULE | Academic Affairs | end-to-end thesis/dissertation governance | thesis lifecycle fragmented | P1 | L2 | A-027.3 | review-gated progression |
| UCE-078 | academic_integrity_case_management | NEW_MODULE | Assessment / Exams / Proctoring | integrity case handling and adjudication | core integrity module too broad for caseflow | P1 | L2 | A-027.3 | strict human decision boundary |
| UCE-079 | meal_plan_management | NEW_MODULE | Student Life / Clubs / Discipline / Appeals | meal plan enrollment and eligibility | cafeteria-service governance missing | P2 | L2 | A-027.3 | no billing mutation first |
| UCE-080 | student_clubs_management | NEW_MODULE | Student Life / Clubs / Discipline / Appeals | club registry, approvals, and activities | student club governance missing | P2 | L2 | A-027.3 | policy-bound approvals |
| UCE-081 | disability_support_services | NEW_MODULE | Student Support / Health / Counseling | accommodations case lifecycle and evidence | disability support flow missing | P0 | L2 | A-027.2 | sensitive data controls required |
| UCE-082 | student_financial_hardship | NEW_MODULE | Student Support / Health / Counseling | hardship case intake and review | hardship intervention flow missing | P1 | L2 | A-027.3 | links aid and counseling |
| UCE-083 | student_orientation_management | NEW_MODULE | Student Lifecycle | orientation planning and completion tracking | orientation lifecycle missing | P2 | L2 | A-027.3 | event and student links |
| UCE-084 | graduation_ceremony_management | NEW_MODULE | Student Lifecycle | ceremony eligibility and logistics | graduation operations gap | P2 | L2 | A-027.3 | readiness and attendance tracking |
| UCE-085 | joint_program_management | NEW_MODULE | International Office / Mobility / Partnerships | joint program governance and obligations | partnerships not lifecycle-managed | P1 | L2 | A-027.3 | multi-party control boundaries |
| UCE-086 | inbound_exchange_management | NEW_MODULE | International Office / Mobility / Partnerships | inbound exchange admissions and support | inbound process missing | P1 | L2 | A-027.3 | ties visa and registrar |
| UCE-087 | outbound_exchange_management | NEW_MODULE | International Office / Mobility / Partnerships | outbound exchange application and approvals | outbound process missing | P1 | L2 | A-027.3 | policy and risk checks |
| UCE-088 | international_grant_coordination | NEW_MODULE | International Office / Mobility / Partnerships | international grant lifecycle coordination | cross-border grant workflow gap | P2 | L2 | A-027.3 | integration-ready design |
| UCE-089 | document_template_library | NEW_MODULE | Document Workflow / Archive / EDS | controlled template versioning and approvals | template governance not explicit | P1 | L2 | A-027.3 | links document workflow |
| UCE-090 | committee_decision_registry | NEW_MODULE | Governance / Rectorate / Strategy | formal committee resolutions and decisions | decision evidence chain missing | P0 | L2 | A-027.2 | critical governance evidence |
| UCE-091 | payroll_interface_workflow | WORKFLOW | Payroll / Position Budgeting Interfaces | orchestrate payroll data handoff approvals | payroll interface workflow missing | P0 | L2 | A-027.4 | no direct payroll execution |
| UCE-092 | degree_audit_workflow | WORKFLOW | Registrar / Student Records | end-to-end degree audit routing | audit orchestration gap | P0 | L2 | A-027.4 | human-reviewed completion |
| UCE-093 | academic_appeals_workflow | WORKFLOW | Student Life / Clubs / Discipline / Appeals | appeal intake-review-resolution flow | appeals orchestration incomplete | P1 | L2 | A-027.4 | committee gates required |
| UCE-094 | thesis_supervision_workflow | WORKFLOW | Academic Affairs | supervisor assignment and milestone approvals | supervision orchestration fragmented | P1 | L2 | A-027.4 | no autonomous approval |
| UCE-095 | graduation_clearance_workflow | WORKFLOW | Registrar / Student Records | cross-domain graduation readiness clearance | fragmented clearance checks | P1 | L2 | A-027.4 | deterministic checklist orchestration |
| UCE-096 | inventory_writeoff_workflow | WORKFLOW | Procurement / Contracts / Assets | controlled writeoff review and approval routing | writeoff path not standardized | P1 | L2 | A-027.4 | audit trail mandatory |
| UCE-097 | contract_obligation_tracking_workflow | WORKFLOW | Legal / Internal Audit | monitor obligation due dates and escalations | legal obligation tracking gap | P0 | L2 | A-027.4 | compliance critical |
| UCE-098 | procurement_plan_approval_workflow | WORKFLOW | Procurement / Contracts / Assets | annual procurement plan approval orchestration | planning approvals fragmented | P1 | L2 | A-027.4 | risk and budget gates |
| UCE-099 | rector_resolution_tracking_workflow | WORKFLOW | Governance / Rectorate / Strategy | track resolution execution and closure evidence | strategy execution visibility gap | P0 | L2 | A-027.4 | rectorate governance value |
| UCE-100 | emergency_drill_execution_workflow | WORKFLOW | Sustainability / ESG / Safety | drill planning-to-execution evidence flow | safety drill workflow missing | P1 | L2 | A-027.4 | no automated emergency actions |
| UCE-101 | service_catalog_request_workflow | WORKFLOW | IT Operations / DevOps / Release Governance | service request intake and approvals | service catalog orchestration gap | P1 | L2 | A-027.4 | ties helpdesk and IAM |
| UCE-102 | helpdesk_ticket_escalation_workflow | WORKFLOW | IT Operations / DevOps / Release Governance | deterministic escalation routing | escalation policy not formalized | P1 | L2 | A-027.4 | SLA evidence first |
| UCE-103 | ethics_amendment_workflow | WORKFLOW | Ethics / Compliance / IP / Tech Transfer | amendment submission and committee handling | ethics change workflow missing | P1 | L2 | A-027.4 | research governance critical |
| UCE-104 | patent_application_workflow | WORKFLOW | Ethics / Compliance / IP / Tech Transfer | patent filing review and approval flow | patent lifecycle orchestration weak | P2 | L2 | A-027.4 | commercialization linkage |
| UCE-105 | epvo_integration | INTEGRATION | Integration Layer / External Systems | national education platform interoperability | connector absent | P1 | L2 | A-027.3 | contract only, no live provider |
| UCE-106 | lms_integration | INTEGRATION | Integration Layer / External Systems | federated LMS synchronization contracts | LMS connector incomplete | P1 | L2 | A-027.3 | read and reconcile first |
| UCE-107 | turnstile_sks_integration | INTEGRATION | Integration Layer / External Systems | turnstile access event federation | physical access integration missing | P1 | L2 | A-027.3 | security and privacy boundaries |
| UCE-108 | idp_sso_integration | INTEGRATION | IAM / Federation / Privileged Access | external IdP SSO interoperability | SSO federation depth gap | P1 | L2 | A-027.3 | no privileged bypass |
| UCE-109 | eds_signature_integration | INTEGRATION | Document Workflow / Archive / EDS | digital signature verification gateway | e-signature connector missing | P0 | L2 | A-027.2 | compliance-critical |
| UCE-110 | payment_gateway_integration | INTEGRATION | Finance / Budget / Billing | payment provider abstraction and evidence | payment integration fragmentation | P1 | L2 | A-027.3 | no autonomous settlement |
| UCE-111 | document_archive_integration | INTEGRATION | Document Workflow / Archive / EDS | archive system sync and retrieval contracts | archive interop gap | P1 | L2 | A-027.3 | retention policy compatibility |
| UCE-112 | ministry_reporting_integration | INTEGRATION | Ministry / Government / Regulatory Reporting | machine-readable reporting exchange | ministry interface missing | P0 | L2 | A-027.2 | regulatory priority |
| UCE-113 | hr_payroll_system_integration | INTEGRATION | Payroll / Position Budgeting Interfaces | HR to payroll system federation | payroll connector missing | P0 | L2 | A-027.2 | contract-only first |
| UCE-114 | accreditation_dashboard | REPORT_DASHBOARD | Quality Assurance / Accreditation | accreditation readiness and gap visibility | no dedicated accreditation dashboard | P0 | L2 | A-027.5 | evidence-backed only |
| UCE-115 | research_performance_dashboard | REPORT_DASHBOARD | Research / Grants / Publications | publication/grant/lab KPI visibility | research reporting fragmentation | P1 | L2 | A-027.5 | no synthetic KPIs |
| UCE-116 | hr_dashboard | REPORT_DASHBOARD | HR / Personnel | staffing, attrition, compliance visibility | no unified HR dashboard | P1 | L2 | A-027.5 | policy-compliant aggregations |
| UCE-117 | campus_operations_dashboard | REPORT_DASHBOARD | Campus / Facilities / Maintenance | facilities, incidents, maintenance visibility | campus ops view fragmented | P1 | L2 | A-027.5 | tenant and role scopes |
| UCE-118 | international_office_dashboard | REPORT_DASHBOARD | International Office / Mobility / Partnerships | mobility and partnerships visibility | domain dashboard missing | P1 | L2 | A-027.5 | interop-dependent |
| UCE-119 | curriculum_quality_dashboard | REPORT_DASHBOARD | Curriculum / Programs / Competencies | curriculum and outcomes quality tracking | quality dashboard gap | P1 | L2 | A-027.5 | evidence lineage required |
| UCE-120 | document_workflow_dashboard | REPORT_DASHBOARD | Document Workflow / Archive / EDS | document SLA and routing bottleneck visibility | document governance visibility weak | P1 | L2 | A-027.5 | no fake processing claims |
| UCE-121 | procurement_risk_dashboard | REPORT_DASHBOARD | Procurement / Contracts / Assets | vendor and obligation risk visibility | procurement risk reporting gap | P1 | L2 | A-027.5 | depends on workflow evidence |
| UCE-122 | compliance_calendar_dashboard | REPORT_DASHBOARD | Legal / Internal Audit | deadline and remediation calendar visibility | compliance calendar gap | P0 | L2 | A-027.5 | critical for audit readiness |
| UCE-123 | academic_integrity_policy_control | POLICY_CONTROL | Assessment / Exams / Proctoring | codified integrity decision boundaries | policy control missing | P0 | L1 | A-027.1 | no automatic sanctions |
| UCE-124 | examination_governance_policy_control | POLICY_CONTROL | Assessment / Exams / Proctoring | exam board and change governance constraints | governance policy not explicit | P1 | L1 | A-027.1 | policy-only first |
| UCE-125 | laboratory_safety_policy_control | POLICY_CONTROL | Sustainability / ESG / Safety | lab safety control baseline and escalation rules | safety policy control gap | P1 | L1 | A-027.1 | ties lab operations |
| UCE-126 | campus_emergency_response_policy_control | POLICY_CONTROL | Sustainability / ESG / Safety | emergency protocol control definitions | emergency policy set incomplete | P1 | L1 | A-027.1 | no autonomous emergency actions |
| UCE-127 | records_retention_legal_hold_policy_control | POLICY_CONTROL | Legal / Internal Audit | legal hold and retention precedence rules | retention/legal hold policy gap | P0 | L1 | A-027.1 | audit-critical |
| UCE-128 | ai_model_risk_policy_control | POLICY_CONTROL | AI Governance / Brain / Agents | AI model risk classification and controls | AI risk policy controls missing | P1 | L1 | A-027.1 | governance foundation |
| UCE-129 | procurement_risk_signal_registry | BRAIN_SIGNAL | Procurement / Contracts / Assets | normalized procurement risk signal taxonomy | procurement signal standard missing | P1 | L2 | A-029 | candidate-only signals |
| UCE-130 | facility_risk_signal_registry | BRAIN_SIGNAL | Campus / Facilities / Maintenance | facilities risk signal standards | facility signal gap | P1 | L2 | A-029 | candidate-only signals |
| UCE-131 | hr_risk_signal_registry | BRAIN_SIGNAL | HR / Personnel | HR risk and compliance signal taxonomy | HR signal governance missing | P1 | L2 | A-029 | candidate-only signals |
| UCE-132 | curriculum_gap_signal_registry | BRAIN_SIGNAL | Curriculum / Programs / Competencies | curriculum quality gap signal definitions | quality signal gap | P1 | L2 | A-029 | no autonomous action |
| UCE-133 | document_delay_signal_registry | BRAIN_SIGNAL | Document Workflow / Archive / EDS | document routing delay signal standards | no standardized delay signals | P1 | L2 | A-029 | supports document dashboard |
| UCE-134 | compliance_deadline_signal_registry | BRAIN_SIGNAL | Legal / Internal Audit | compliance deadline risk signals | deadline signal model missing | P0 | L2 | A-029 | audit-critical |
| UCE-135 | integration_failure_signal_registry | BRAIN_SIGNAL | Integration Layer / External Systems | standardized integration failure signals | integration reliability signal gap | P0 | L2 | A-029 | drives resilience reviews |
| UCE-136 | enrollment_conversion_signal_registry | BRAIN_SIGNAL | Admissions / Enrollment | admissions conversion signal taxonomy | admissions signal standard missing | P2 | L2 | A-029 | explainability boundary |
| UCE-137 | dropout_prevention_signal_registry | BRAIN_SIGNAL | Student Lifecycle | dropout risk signal standardization | student risk signal depth gap | P1 | L2 | A-029 | human review required |
| UCE-138 | scholarship_abuse_signal_registry | BRAIN_SIGNAL | Student Lifecycle | scholarship misuse risk indicators | scholarship controls under-modeled | P1 | L2 | A-029 | no enforcement automation |
| UCE-139 | payroll_anomaly_signal_registry | BRAIN_SIGNAL | Payroll / Position Budgeting Interfaces | payroll anomaly signal taxonomy | payroll oversight gap | P1 | L2 | A-029 | policy and audit bound |
| UCE-140 | contract_breach_signal_registry | BRAIN_SIGNAL | Legal / Internal Audit | contract breach early-warning signals | legal risk signal standards missing | P1 | L2 | A-029 | legal review required |
| UCE-141 | cyber_threat_signal_registry | BRAIN_SIGNAL | Security / Access Control / SOC | cyber risk signal standardization | SOC signal taxonomy incomplete | P1 | L2 | A-029 | no auto-block execution |
| UCE-142 | sustainability_esg_signal_registry | BRAIN_SIGNAL | Sustainability / ESG / Safety | ESG and safety signal governance | ESG signal registry missing | P2 | L2 | A-029 | evidence-driven only |
| UCE-143 | commercialization_pipeline_signal_registry | BRAIN_SIGNAL | Commercialization / Continuing Education / Online Programs | commercialization pipeline health signals | commercialization signal gap | P2 | L2 | A-029 | candidate-only signals |
| UCE-144 | brain_signal_quality_monitor | BRAIN_SIGNAL | AI Governance / Brain / Agents | detect drift/quality issues in signal pipelines | signal quality governance gap | P1 | L2 | A-029 | no autonomous correction |
| UCE-145 | safe_evidence_summary_agent | AUTONOMOUS_WORKFLOW_CANDIDATE | AI Governance / Brain / Agents | draft evidence summaries for human review | manual evidence summarization bottleneck | P2 | L1 | A-030 | human approval mandatory |
| UCE-146 | safe_task_drafting_agent | AUTONOMOUS_WORKFLOW_CANDIDATE | Governance / Rectorate / Strategy | draft task cards and action templates | manual planning overhead | P2 | L1 | A-030 | no direct execution rights |
| UCE-147 | safe_report_draft_agent | AUTONOMOUS_WORKFLOW_CANDIDATE | Data / BI / KPI / Reporting | draft report narrative from approved evidence | reporting drafting bottleneck | P2 | L1 | A-030 | human sign-off required |
| UCE-148 | safe_document_routing_agent | AUTONOMOUS_WORKFLOW_CANDIDATE | Document Workflow / Archive / EDS | suggest routing path for incoming documents | routing triage latency | P2 | L1 | A-030 | cannot auto-approve |
| UCE-149 | safe_compliance_calendar_agent | AUTONOMOUS_WORKFLOW_CANDIDATE | Legal / Internal Audit | draft reminder schedule for compliance deadlines | calendar maintenance burden | P2 | L1 | A-030 | no autonomous enforcement |

### Deduplication Review (150 Baseline + 25 Extension + UCE-001..054)

| Candidate | Existing Similar Capability | Decision | Rationale |
|---|---|---|---|
| UCE-078 academic_integrity_case_management | baseline academic_integrity | ACCEPT_SEPARATE | dedicated case lifecycle distinct from broader integrity domain |
| UCE-061 faculty_attestation | baseline faculty | ACCEPT_SEPARATE | distinct attestation lifecycle and compliance evidence requirements |
| UCE-067 teaching_load_contracts | baseline workload_management | ACCEPT_SEPARATE | contractual obligations differ from planning classification |
| UCE-091 payroll_interface_workflow | UCE-113 hr_payroll_system_integration | ACCEPT_BOTH | workflow orchestration and integration contracts are distinct types |
| UCE-109 eds_signature_integration | A-027.0 document/e-sign direction | ACCEPT_SEPARATE | explicit external connector needed for signature trust chain |
| UCE-112 ministry_reporting_integration | UCE-032 ministry_reporting_dashboard | ACCEPT_BOTH | integration transport and reporting surface are different capabilities |
| UCE-114 accreditation_dashboard | baseline accreditation modules | ACCEPT_SEPARATE | dashboard visibility capability is not implemented by module existence |
| UCE-122 compliance_calendar_dashboard | UCE-048 data_retention_policy_control | ACCEPT_BOTH | policy control and operational visibility remain separate layers |
| UCE-127 records_retention_legal_hold_policy_control | UCE-012 archive_retention_management | ACCEPT_BOTH | policy definitions and execution module are distinct |
| UCE-129 procurement_risk_signal_registry | UCE-047 third_party_risk_policy | ACCEPT_BOTH | policy control != signal taxonomy |
| UCE-144 brain_signal_quality_monitor | UCE-054 brain_decision_audit_trail | ACCEPT_SEPARATE | signal quality oversight differs from decision lineage logging |
| UCE-145 safe_evidence_summary_agent | A-025 safe agent concept | ACCEPT_SEPARATE | explicit bounded candidate with A-030 placement and constraints |
| UCE-146 safe_task_drafting_agent | A-025 safe agent concept | ACCEPT_SEPARATE | candidate formalized with restrictions and governance links |
| UCE-147 safe_report_draft_agent | report drafting workflows | ACCEPT_SEPARATE | distinct autonomous draft candidate under human approval |
| UCE-148 safe_document_routing_agent | UCE-009 document_workflow | ACCEPT_BOUNDED | routing suggestion candidate only; execution remains in workflow module |
| UCE-149 safe_compliance_calendar_agent | UCE-122 dashboard + policy controls | ACCEPT_BOUNDED | reminder suggestion is separate from policy and dashboard layers |

### Updated Registry Counts After B1

- original A-027.0 candidates: 54
- added in A-027.0.B1: 95
- total university completeness candidates: 149

Type counts (all candidates):
- candidate_new_modules: 56
- candidate_workflows: 22
- candidate_integrations: 16
- candidate_reports_dashboards: 15
- candidate_policy_controls: 10
- candidate_brain_signals: 20
- candidate_autonomous_workflow_candidates: 6
- candidate_submodules: 1
- candidate_data_entities: 1
- candidate_audit_evidence_capabilities: 1

### Priority Summary (All Candidates)

- P0: regulatory/compliance-critical and major domain-missing capabilities (international office foundation, ministry interoperability, HR foundations, document governance, compliance calendar and deadline signals)
- P1: high-value operational capabilities that unlock L3/L4 readiness depth
- P2: important but dependency-heavy or post-foundation optimization slices
- P3: intentionally deferred exploratory candidates

### Recommended Next Governance Action

- Keep next action at A-027.1 (registry lock/canonicalization).
- A-027.1 inputs should now include:
	- canonical dedup rules for module vs workflow vs integration vs dashboard vs policy vs signal vs autonomous candidate
	- P0 hard-selection list for A-027.2 batch sizing
	- domain ownership assignment and acceptance criteria templates per candidate type

### Anti-Fake Rules (Reaffirmed)

- No candidate in UCE-001..149 is treated as implemented.
- No candidate maturity is claimed above initial planning target without runtime evidence.
- No fake Brain execution claim.
- No fake autonomous workflow claim.
- No fake integration-live claim.
- No fake compliance certification claim.
- Baseline 150 and extension 25 remain isolated from expansion registry counts.

## A-027.1 — Controlled Expansion Registry Governance Lock (UCE-001..UCE-149)

### Governance-Lock Objective

- Freeze canonical planning decisions for all 149 UCE candidates before any runtime implementation planning.
- Enforce count integrity and decision transparency so A-027.2 can only consume approved and non-inflated candidates.

### Extraction Integrity (Task 2)

- Extracted row rule: only lines matching `| UCE-### | ... |` from the canonical registry tables.
- Unique ID check: PASS (`UCE-001..UCE-149`, 149 unique).
- Raw type counts from extracted rows:
	- NEW_MODULE: 57
	- WORKFLOW: 22
	- INTEGRATION: 16
	- REPORT_DASHBOARD: 15
	- POLICY_CONTROL: 10
	- BRAIN_SIGNAL: 20
	- AUTONOMOUS_WORKFLOW_CANDIDATE: 6
	- SUBMODULE: 1
	- DATA_ENTITY: 1
	- AUDIT_EVIDENCE_CAPABILITY: 1

### Canonicalization and Dedup Outcomes (Task 3)

- Decision totals:
	- ACCEPT: 138
	- MERGE_WITH_OTHER_UCE: 6
	- DEFER: 3
	- REJECT_DUPLICATE: 2
- Accepted type counts:
	- NEW_MODULE: 53
	- WORKFLOW: 20
	- INTEGRATION: 16
	- REPORT_DASHBOARD: 15
	- POLICY_CONTROL: 10
	- BRAIN_SIGNAL: 17
	- AUTONOMOUS_WORKFLOW_CANDIDATE: 6
	- AUDIT_EVIDENCE_CAPABILITY: 1

### Locked Merge / Defer / Reject Set

- MERGE_WITH_OTHER_UCE:
	- UCE-010 -> `document_workflow_internal_memo_flow`
	- UCE-020 -> `international_office_visa_support`
	- UCE-021 -> `employee_records_party_profile`
	- UCE-068 -> `faculty_contracting_and_employee_records`
	- UCE-093 -> `student_appeals_workflow`
	- UCE-132 -> `academic_quality_signal_registry`
- DEFER:
	- UCE-066 (`DEFER_DEPENDENCY_HEAVY`)
	- UCE-079 (`DEFER_LOW_PRIORITY`)
	- UCE-143 (`DEFER_DEPENDENCY_HEAVY`)
- REJECT_DUPLICATE:
	- UCE-100 (covered by emergency drill capability set and flow overlap)
	- UCE-137 (covered by existing student risk signal scope)

### A-027.2 Controlled Selection Gate

- A-027.2 can select only from accepted candidates.
- Any merged candidate is ineligible as a standalone implementation unit and must be represented through its canonical target.
- Deferred and rejected candidates are explicitly excluded from A-027.2 selection.
- Priority policy for A-027.2 batching: accepted P0 first, then accepted P1, then accepted P2 if capacity remains.

### Governance Rules (Locked)

- Rule 1: Candidate presence in this map is not implementation evidence.
- Rule 2: No candidate may claim maturity advancement without runtime evidence and scoped validation.
- Rule 3: No baseline 150 or extension 25 metrics may be altered by expansion registry planning actions.
- Rule 4: Autonomous candidates remain human-approval-bound and non-executing in planning waves.
- Rule 5: Brain signals remain candidate taxonomies until runtime evidence and policy gates exist.

### Canonical Decision Matrix Location

- Full 149-row per-candidate canonicalization table is locked in:
	- `A-027.1-CONTROLLED_EXPANSION_REGISTRY_AND_GOVERNANCE_LOCK_REPORT.md`

### Next Action

- Next action id: A-027.2
- Action title: Controlled implementation selection from accepted registry set
- Scope: planning/runtime preparation only for selected accepted candidates under anti-inflation guardrails
