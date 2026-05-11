# SBS_UB University Completeness Expansion Map

## 1. Executive Summary

A-027.0 is a planning-only audit that treats the existing 150 modules as the stabilized baseline core, not the final ceiling. The 25 controlled extensions remain a separate tracking plane. This document defines a realistic beyond-150 expansion roadmap for maximum University OS completeness, without runtime implementation or maturity inflation.

Key result:
- A new University Completeness Expansion Candidate Registry is defined with 53 candidates.
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
