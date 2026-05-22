# SBS_UB Full University OS Capability Master Matrix

## 1. Role and Authority

- `SBS_UB.md` remains the active execution tracker and handoff source of truth.
- This file is the authoritative completeness and reconciliation matrix for Full University OS planning.
- This file exists to prevent missing capabilities, duplicate canonicals, and accidental narrowing back to the 150 baseline ceiling.
- Baseline, extension, expansion, verticals, Brain, integrations, dashboards, bridges, evidence, and forbidden autonomous boundaries are tracked together here.
- Maturity metrics remain separate from this matrix and stay unchanged unless separately evidenced.
- A capability row does not equal a backend package, frontend page, or standalone runtime module.
- Canonical module reuse is mandatory.

## 2. Full University OS Principle

- SBS UB target is Full University OS capability universe, not only the baseline 150 modules.
- Locked baseline scope remains `150` and controlled extension scope remains `25`, for locked tracked total `175`.
- The Full University OS capability universe is allowed to exceed `300` and may reasonably reach `450-520+` rows once modules, workflows, submodules, bridges, dashboards, Brain signals, integrations, evidence layers, and forbidden actions are fully enumerated.
- Because authoritative sources today fully lock the baseline `150`, the controlled extension `25`, and the University Completeness Expansion registry `54`, this B2 file seeds the matrix framework and high-value row set while reserving exhaustive row completion for `A-036.2-B2.R1`.

## 3. Coverage Planes

| Plane | Meaning | Current Locked State |
|---|---|---|
| `BASELINE_150` | canonical platform baseline | locked at `150` |
| `CONTROLLED_EXTENSION_25` | controlled extension lane | locked at `25` |
| `UNIVERSITY_COMPLETENESS_EXPANSION` | beyond-150 registry and overlays | `54` candidates currently tracked in the expansion map |
| `PRODUCT_VERTICAL` | vertical operating capabilities and seeded scope items | multiple suites active or planned |
| `BRIDGE_CAPABILITY` | cross-suite read-only or controlled orchestration links | required to avoid duplicate packages |
| `BRAIN_LAYER` | signal, governance, review, draft, and audit surfaces | planning and seeded overlay |
| `INTEGRATION_LAYER` | provider and external-system readiness | planning and seeded overlay |
| `REPORTING_DASHBOARD` | executive, operational, compliance, and trust visibility | mixed implemented and planned |
| `FORBIDDEN_ACTION_REGISTRY` | human-review-only and prohibited autonomous actions | mandatory boundary plane |
| `FUTURE_VERTICAL` | domain family deferred to later suite closure | active planning bucket |

## 4. Matrix Taxonomy

### 4.1 Required Row Fields

1. `capability_id`
2. `capability_name`
3. `canonical_module_name`
4. `source_plane`
5. `source_reference`
6. `domain`
7. `product_vertical`
8. `capability_type`
9. `implementation_status`
10. `maturity_level`
11. `runtime_evidence`
12. `frontend_evidence`
13. `e2e_evidence`
14. `bridge_dependencies`
15. `duplicate_risk`
16. `sensitive_risk`
17. `anti_fake_boundaries`
18. `brain_readiness`
19. `provider_integration_need`
20. `dashboard_need`
21. `backend_needed`
22. `frontend_needed`
23. `e2e_needed`
24. `next_action`
25. `notes`

### 4.2 Allowed ID Prefixes

- `BAS-xxx` baseline 150
- `EXT-xxx` extension 25
- `UCE-xxx` completeness expansion candidate registry
- `VRT-xxx` product vertical capability
- `BRG-xxx` bridge capability
- `BRN-xxx` Brain capability
- `INT-xxx` integration/provider capability
- `RPT-xxx` dashboard/report capability
- `FORBID-xxx` forbidden autonomous action

### 4.3 Allowed Classification Values

- `source_plane`: `BASELINE_150`, `CONTROLLED_EXTENSION_25`, `UNIVERSITY_COMPLETENESS_EXPANSION`, `PRODUCT_VERTICAL`, `BRIDGE_CAPABILITY`, `BRAIN_LAYER`, `INTEGRATION_LAYER`, `REPORTING_DASHBOARD`, `FORBIDDEN_ACTION_REGISTRY`, `FUTURE_VERTICAL`
- `capability_type`: `NEW_MODULE`, `EXISTING_CANONICAL_MODULE`, `EXISTING_ADJACENT_MODULE`, `WORKFLOW`, `SUBMODULE`, `DATA_ENTITY`, `INTEGRATION`, `REPORT_DASHBOARD`, `POLICY_CONTROL`, `BRAIN_SIGNAL`, `AUTONOMOUS_WORKFLOW_CANDIDATE`, `AUDIT_EVIDENCE_CAPABILITY`, `BRIDGE_TO_EXISTING_VERTICAL`, `FORBIDDEN_AUTONOMOUS_ACTION`
- `implementation_status`: `IMPLEMENTED_RUNTIME`, `IMPLEMENTED_BACKEND_ONLY`, `IMPLEMENTED_FRONTEND_ONLY`, `IMPLEMENTED_E2E`, `SPECIFIED_ONLY`, `PLANNED`, `DEFERRED`, `BLOCKED`, `NOT_STARTED`, `FORBIDDEN`
- `maturity_level`: `L0`, `L1`, `L2`, `L3`, `L4`, `L5`, `L6`, `NOT_APPLICABLE`, `SEPARATE_OVERLAY`
- `duplicate_risk`: `NONE`, `LOW`, `MEDIUM`, `HIGH`, `RESOLVED_BY_ALIAS`, `RESOLVED_BY_BRIDGE`, `HUMAN_REVIEW_REQUIRED`
- `brain_readiness`: `NO_BRAIN`, `SIGNAL_READY`, `GOVERNANCE_ONLY`, `HUMAN_REVIEW_QUEUE_READY`, `SAFE_AGENT_DRAFT_ONLY`, `DEFERRED`, `FORBIDDEN`
- `provider_integration_need`: `NONE`, `FUTURE_READINESS_ONLY`, `NON_LIVE_PROFILE_ONLY`, `READ_ONLY_INTEGRATION`, `LIVE_INTEGRATION_DEFERRED`, `FORBIDDEN`
- `dashboard_need`: `NONE`, `MODULE_SUMMARY`, `EXECUTIVE_VISIBILITY`, `OPERATIONAL_DASHBOARD`, `COMPLIANCE_DASHBOARD`, `BRAIN_GOVERNANCE_DASHBOARD`
- `backend_needed`: `YES`, `NO`, `ALREADY_EXISTS`, `BRIDGE_ONLY`, `DEFERRED`
- `frontend_needed`: `YES`, `NO`, `ALREADY_EXISTS`, `BRIDGE_ONLY`, `DEFERRED`
- `e2e_needed`: `YES`, `NO`, `ALREADY_EXISTS`, `DEFERRED`

## 5. Locked Metrics and Non-Movement

- `L0=0`
- `L1=0`
- `L2=0`
- `L3=55`
- `L4=68`
- `L5=25`
- `L6=2`
- `total=150`
- `extension_total_count=25`
- `total_tracked_modules=175`
- `expansion_L2_foundation_count=67`
- `expansion_L3_logic_count=50`
- `expansion_L4_visibility_count=40`
- `expansion_L4_api_route_count=40`
- `provider_readiness_foundation_count=11`
- `brain_governance_foundation_count=5`

## 6. Baseline 150 Summary by Domain and Maturity

| Domain | Baseline Coverage Summary | Current Posture |
|---|---|---|
| Governance / Rectorate / Strategy | `university_core`, `admin`, `workflows`, `plans` | partial; workflows and dashboards still thin |
| Student Lifecycle | `students`, `student_portal`, `student_services`, `interventions`, `academic_records`, `transcripts` | strongest existing product vertical with runtime, frontend, and E2E evidence |
| Academic Operations | `attendance`, `room_booking`, `workload_management`, `exam_governance`, `exam_proctoring` | partial academic operating substrate only |
| Finance / Procurement / Assets | `billing`, `budget_planning`, `procurement`, `asset_inventory`, `online_payments` | strong baseline module presence |
| Security / IAM / SOC | `auth`, `rbac`, `access_control`, `security`, `security_operations`, `sso_saml` | medium; SOC and PAM depth still missing |
| Platform / DevOps / Observability | `platform`, `platform_health`, `observability`, `jobs`, `feature_flags` | strong baseline infrastructure layer |
| Data / Analytics / KPI | `analytics`, `platform_shared`, `model_evaluation` | partial; governance and trust layers incomplete |
| Library / Knowledge | `library`, `library_circulation`, `digital_documents`, `knowledge_retrieval` | medium coverage |
| Research / Science | `research`, `research_grants`, `publications`, `research_ethics`, `lab_operations` | medium foundation, not a closed vertical |
| Campus / Facilities | `facilities_work_orders`, `room_booking`, `parking`, `parking_enforcement`, `housing`, `transport` | medium coverage with operational gaps |

Baseline interpretation:

- Baseline `150` is stable and remains the maturity-measured canonical foundation.
- Baseline is not the final platform ceiling.
- Baseline rows must be reused, not re-created under new vertical names.

## 7. Controlled Extension 25 Summary by Domain and Status

| Extension Family | Representative Items | Status |
|---|---|---|
| AI platform extension | `llm_eval_harness`, `prompt_lifecycle_governance`, `ai_model_registry`, `knowledge_retrieval_fabric`, `copilot_safety_ops` | extension lane; mixed merge/promote/defer decisions |
| Compliance extension | `privacy_request_orchestrator`, `data_retention_orchestrator` | high-value controlled extension, not baseline |
| Finance extension | `billing_reconciliation_ops`, `revenue_leak_detection` | controlled overlay; partly mergeable with billing |
| Procurement / risk extension | `procurement_vendor_risk` | controlled overlay; may merge first |
| Campus extension | `classroom_iot_telemetry`, `energy_optimization_ops`, `transport_fleet_ops` | deferred until integration/data quality mature |
| Student-success extension | `student_success_playbooks`, `alumni_career_outcomes` | extension overlay, not baseline |
| Academic / digital credential extension | `digital_credentials_wallet`, `micro_credentials_stack` | controlled future lane |
| Governance / security extension | `incident_command_center`, `threat_intel_fusion`, `policy_simulation_lab` | future controlled overlays |

Extension interpretation:

- Extension `25` remains separate from baseline.
- Extension items are not automatically missing runtime work; some are merge candidates, some future overlays, and some future vertical depth.

## 8. Expansion Candidate Registry Summary

- Authoritative expansion registry currently defines `54` candidates.
- Type distribution: `20 NEW_MODULE`, `8 WORKFLOW`, `7 INTEGRATION`, `6 REPORT_DASHBOARD`, `4 POLICY_CONTROL`, `4 BRAIN_SIGNAL`, `1 AUTONOMOUS_WORKFLOW_CANDIDATE`, `1 SUBMODULE`, `1 DATA_ENTITY`, `1 AUDIT_EVIDENCE_CAPABILITY`.
- UCE candidates are not automatically "missing and unimplemented"; some are now canonicals or adjacent overlays referenced by later vertical work.
- B2 treats the expansion registry as a major input plane, not the final capability universe ceiling.

## 9. Vertical Coverage Summary

| Product Vertical | Status | Modules Already Covered | Missing Modules | Bridges Needed | Brain Needs | Provider Needs | Dashboard Needs | Sensitivity | Recommended Action |
|---|---|---|---|---|---|---|---|---|---|
| Executive Governance Suite | CLOSED_BASELINED | rector assignment, document workflow, executive control tower | strategy office depth, decision policy depth | to academic, finance, ministry | governance deviation, decision audit | egov policy feed deferred | rector dashboard, leadership dashboard | high | preserve canonicals, expand via bridges |
| Student Lifecycle Suite | CLOSED_BASELINED | admissions-to-degree core, requests, interventions, student evidence | discipline, hardship, committee depth | to academic ops, support, executive | student risk | SIS/platonus deferred | lifecycle dashboard, student success dashboard | high | reuse canonicals, no duplicate registrar core |
| Academic Operations Suite | SPECIFIED_AND_RECONCILED | academic ops contract, 28-item reconciliation, existing canonicals | true-new subset of 6 plus bridge wrappers | to registrar, document, quality, governance | curriculum and academic quality signals | SIS/LMS deferred | academic ops dashboard | critical | canonical-aware runtime only after B2.R1 or careful reuse |
| Research / Science Suite | FUTURE_VERTICAL | research base modules exist | projects, grants, ethics amendments, evidence depth | to accreditation, thesis, library | grant execution risk | grant and repository integrations deferred | research dashboard | high | future vertical planning |
| Quality / Accreditation Suite | FUTURE_VERTICAL | accreditation and compliance base | evidence repository, gap tracking, review workflows | to curriculum, research, ministry | academic quality signal | ministry accreditation deferred | accreditation dashboard, scorecard | critical | future vertical planning |
| HR / Staff Governance Suite | FUTURE_VERTICAL | hr_payroll, workload anchors | recruitment, onboarding, employee records, leave, appeals | to academic teaching load, IAM | faculty overload signal | 1C/payroll deferred | HR ops dashboard | critical | future vertical planning |
| Finance / Procurement / Asset Suite | PARTIAL_CANONICAL | billing, budgets, procurement, assets | close orchestration, vendor risk, tax support | to governance, provider, audit | finance anomaly signal | bank/ERP deferred | finance dashboard | critical | preserve canonicals, add depth later |
| Campus / Facilities / Housing Suite | PARTIAL_CANONICAL | rooms, parking, facilities, housing/transport basics | dormitory depth, incidents, safety, fleet | to academic room allocation, security | facility risk | IoT/access control deferred | campus dashboard | high | future vertical planning |
| International / Mobility / Partnerships Suite | FUTURE_VERTICAL | implicit only plus some registry items | international office, mobility, partnership lifecycle | to practice, ministry, legal | mobility risk | visa and partner integrations deferred | mobility dashboard | medium | future vertical planning |
| Security / IAM / SOC Suite | PARTIAL_CANONICAL | auth, RBAC, security ops, SSO | SOC case, PAM, threat fusion | to every suite | security incident signal | IDP/SIEM deferred | security dashboard | critical | preserve canonicals, deepen later |
| Data / Analytics / KPI Suite | PARTIAL_CANONICAL | analytics, model evaluation, platform shared | KPI registry, trust, lineage, catalog | to all reporting planes | KPI quality signal | BI warehouse deferred | data trust dashboard | high | future vertical planning |
| Integration / Provider Suite | FUTURE_VERTICAL | integrations, ai_gateway, ldap, SSO anchors | registry ops, health, connector governance | to all provider-dependent verticals | integration failure signal | all providers non-live first | provider readiness dashboard | critical | future vertical planning |
| Brain Governance / Agent Suite | PARTIAL_CANONICAL | brain_core, ai_guardrails, ai_copilot_ops, prompt_management | signal registry, decision audit, review queue | to all signal-enabled suites | full signal family | model/vector/provider deferred | AI governance dashboards | critical | governance-only expansion |
| Library / Archive / Knowledge Suite | PARTIAL_CANONICAL | library, circulation, digital docs, knowledge retrieval | retention, repository, freshness, archive depth | to document, research, data | content freshness signal | repository integration deferred | library/archive dashboard | medium | future vertical planning |
| Communications / Notification Suite | PARTIAL_CANONICAL | communications, notification_center, parent_portal | correspondence, crisis workflow, reliability layer | to governance, student lifecycle, provider layer | notification failure signal | email/SMS deferred | communications reliability dashboard | medium | preserve canonicals and expand |
| Ministry / Regulatory Reporting Suite | FUTURE_VERTICAL | reporting spread across modules only | orchestrator, submission/correction, evidence pack | to compliance, finance, academic, executive | filing compliance risk | government integrations deferred | ministry dashboard | critical | future vertical planning |

## 10. Academic Operations 28-Item Reconciliation

- `EXISTING_CANONICAL_MODULE = 3`
- `EXISTING_ADJACENT_MODULE = 11`
- `BRIDGE_TO_EXISTING_VERTICAL = 8`
- `NEW_TRUE_MODULE = 6`
- `DEFERRED_FUTURE_VERTICAL = 0`

Direct canonical mappings:

- `course_catalog -> course_catalog_management / UCE-076`
- `elective_course_selection -> UCE-073`
- `academic_committee_decisions -> committee_decision_registry / UCE-090`

True-new modules:

- `academic_group_management`
- `cohort_management`
- `gradebook_metadata`
- `retake_management`
- `summer_semester_management`
- `advisor_tutor_management`

Runtime decision:

- `A-036.2-RUNTIME` must be canonical-aware.
- No duplicate modules may be created.
- Bridge-first architecture is required.

## 11. Brain / AI / Agent Readiness Matrix

| Capability | Domain | Input Sources | Output Type | Human Review Required | Autonomy Level | Forbidden Actions | Evidence Needed | Next Action |
|---|---|---|---|---|---|---|---|---|
| `student_risk_signal_registry` | Student Lifecycle | interventions, support, academic evidence | signal taxonomy | yes | governance-only | sanction, dismissal, hidden scoring | lineage + policy | B2.R1 row completion |
| `curriculum_gap_signal_registry` | Academic Operations / Quality | curriculum mapping, outcomes, catalog | signal taxonomy | yes | governance-only | fake compliance or approval | evidence registry | B2.R1 row completion |
| `academic_quality_signal_registry` | Quality / Academic | curriculum, syllabus, quality evidence | signal taxonomy | yes | governance-only | automated accreditation decision | lineage + audit | B2.R1 row completion |
| `finance_anomaly_signal_registry` | Finance | billing, budget, procurement evidence | anomaly taxonomy | yes | governance-only | financial approval automation | evidence + review queue | B2.R1 row completion |
| `governance_deviation_signal` | Governance | assignments, decrees, SLA breach evidence | deviation signal | yes | governance-only | autonomous rectification | audit trail | B2.R1 row completion |
| `faculty_overload_signal` | HR / Academic | workload, contracts, teaching load evidence | overload signal | yes | governance-only | HR disciplinary action | workload evidence | B2.R1 row completion |
| `compliance_breach_signal` | Compliance | audit findings, retention, privacy evidence | breach signal | yes | governance-only | autonomous sanction | evidence pack | B2.R1 row completion |
| `security_incident_signal` | Security | SOC, IAM, SIEM evidence | incident signal | yes | governance-only | auto-lock without policy | security audit evidence | B2.R1 row completion |
| `integration_failure_signal` | Integration | connector health, queues, retries | failure signal | yes | governance-only | external submission retries without approval | integration logs | B2.R1 row completion |
| `facility_risk_signal` | Campus | incidents, occupancy metadata, work orders | risk signal | yes | governance-only | autonomous closure | facility evidence | B2.R1 row completion |
| `grant_execution_risk_signal` | Research | grants, deliverables, ethics evidence | risk signal | yes | governance-only | funding decision automation | grant evidence | B2.R1 row completion |
| `notification_failure_signal` | Communications | notification center, gateway readiness | failure signal | yes | governance-only | auto-send or silent retries | provider logs | B2.R1 row completion |
| `KPI_quality_signal` | Data / KPI | KPI registry, lineage, evidence | quality signal | yes | governance-only | fake KPI publication | dashboard evidence | B2.R1 row completion |
| `brain_decision_audit_trail` | AI Governance | recommendations, human review outcomes | audit evidence | yes | human-review queue ready | silent autonomous execution | immutable audit chain | B2.R1 row completion |
| `human_review_queue` | AI Governance | all signal families | review queue | yes | human review only | automated approval | queue evidence | B2.R1 row completion |
| `safe_task_drafting_agent` | AI Governance | policies, tasks, templates | draft artifact | yes | safe-draft only | execution or submission | prompt + audit evidence | B2.R1 row completion |
| `safe_policy_draft_agent` | AI Governance | policy registry, controls | draft artifact | yes | safe-draft only | policy enactment | draft evidence | B2.R1 row completion |
| `safe_report_draft_agent` | AI Governance | dashboards, evidence layers | draft report | yes | safe-draft only | official filing | evidence references | B2.R1 row completion |
| `safe_minutes_summary_agent` | Governance | meetings, agenda notes | draft summary | yes | safe-draft only | binding decision publication | review evidence | B2.R1 row completion |

Brain rule:

- Brain does not imply autonomous action by default.
- Signal, draft, and audit layers are allowed planning surfaces.
- Critical decisions remain forbidden or human-review-only.

## 12. Provider / Integration Master Map

| Integration | Provider Profile | Integration Status | Live Posture | Credentials Present | External Submission Present | Risk | Related Verticals | Future Action |
|---|---|---|---|---|---|---|---|---|
| Platonus / SIS | student information system | planned | `LIVE_INTEGRATION_DEFERRED` | false | false | high | student lifecycle, academic ops | non-live profile first |
| `one_c_integration` | finance / HR ERP | planned | `LIVE_INTEGRATION_DEFERRED` | false | false | high | HR, finance | non-live profile first |
| `egov_integration` | government services | planned | `LIVE_INTEGRATION_DEFERRED` | false | false | high | governance, ministry, compliance | non-live profile first |
| `eds_kz_provider` | digital signature / EDS | planned | `LIVE_INTEGRATION_DEFERRED` | false | false | high | document, ministry | profile first |
| ministry reporting | regulatory submission | planned | `LIVE_INTEGRATION_DEFERRED` | false | false | high | ministry, compliance | non-live profile first |
| IDP / SSO | identity provider | partial existing anchor | `NON_LIVE_PROFILE_ONLY` | false | false | medium | security | clarify provider profiles |
| LMS | learning management system | planned | `LIVE_INTEGRATION_DEFERRED` | false | false | medium | academic ops | non-live profile first |
| email gateway | outbound messaging | planned | `NON_LIVE_PROFILE_ONLY` | false | false | medium | communications | provider-safe readiness only |
| SMS gateway | outbound messaging | planned | `NON_LIVE_PROFILE_ONLY` | false | false | medium | communications | provider-safe readiness only |
| payment gateway | payment provider | partial conceptual anchor | `LIVE_INTEGRATION_DEFERRED` | false | false | high | finance | defer live rails |
| bank gateway | banking rails | planned | `LIVE_INTEGRATION_DEFERRED` | false | false | high | finance | read/verify-first profile |
| HR payroll | payroll platform | planned | `LIVE_INTEGRATION_DEFERRED` | false | false | high | HR | non-live profile first |
| biometric/device | access/attendance device | planned | `LIVE_INTEGRATION_DEFERRED` | false | false | high | campus, student lifecycle | privacy-first profile |
| library repository | knowledge / repository | planned | `READ_ONLY_INTEGRATION` | false | false | medium | library, research | read-only first |
| BI warehouse | analytics warehouse | planned | `READ_ONLY_INTEGRATION` | false | false | medium | data / dashboards | read-only first |
| SIEM | security telemetry | planned | `READ_ONLY_INTEGRATION` | false | false | high | security | read-only first |
| IoT / access control | campus operations devices | planned | `LIVE_INTEGRATION_DEFERRED` | false | false | high | campus, security | profile first |

## 13. Dashboard / Reporting Master Map

| Dashboard | fake_metrics Requirement | Data Source | Incomplete Data Behavior | Source Modules | Current Status | Future Action |
|---|---|---|---|---|---|---|
| `rector_strategy_dashboard` | must be false | evidence aggregates | show limitation banner | governance, finance, academic, ministry | planned / UCE candidate | B2.R1 row completion |
| `executive_control_tower` | must be false | existing governance evidence | show incomplete-data contract | executive governance canonicals | existing baseline surface | reuse canonical |
| `student_lifecycle_dashboard` | must be false | runtime student lifecycle evidence | show incomplete-data contract | admissions, records, interventions | adjacent existing | reuse canonical |
| `academic_operations_dashboard` | must be false | metadata-derived aggregates | show incomplete-data contract | timetable, attendance, exams, catalog | specified only | canonical-aware runtime later |
| `research_science_dashboard` | must be false | research evidence | show incomplete-data contract | grants, publications, ethics | planned | B2.R1 row completion |
| `accreditation_dashboard` | must be false | accreditation evidence | show incomplete-data contract | accreditation, quality, curriculum | planned | B2.R1 row completion |
| `finance_executive_dashboard` | must be false | finance evidence | show incomplete-data contract | billing, procurement, close | UCE candidate | B2.R1 row completion |
| `HR_operations_dashboard` | must be false | HR evidence | show incomplete-data contract | staff records, workload, appeals | planned | B2.R1 row completion |
| `security_risk_dashboard` | must be false | security evidence | show incomplete-data contract | IAM, SOC, SIEM | UCE candidate | B2.R1 row completion |
| `integration_health_dashboard` | must be false | connector readiness and failures | show incomplete-data contract | integration registry, failure signals | planned | B2.R1 row completion |
| `ministry_reporting_dashboard` | must be false | filing evidence packs | show incomplete-data contract | ministry orchestrator, compliance | UCE candidate | B2.R1 row completion |
| `campus_operations_dashboard` | must be false | campus evidence | show incomplete-data contract | facilities, housing, transport | planned | B2.R1 row completion |
| `library_archive_dashboard` | must be false | archive and repository evidence | show incomplete-data contract | library, archive, repository | planned | B2.R1 row completion |
| `AI_governance_dashboard` | must be false | model, prompt, signal evidence | show incomplete-data contract | brain governance surfaces | UCE candidate / partial adjacent | B2.R1 row completion |
| `data_trust_dashboard` | must be false | lineage and quality evidence | show incomplete-data contract | analytics, KPI registry, evidence layer | planned | B2.R1 row completion |
| `KPI_quality_dashboard` | must be false | KPI evidence | show incomplete-data contract | kpi registry, quality signal | planned | B2.R1 row completion |
| `provider_readiness_dashboard` | must be false | provider readiness evidence | show incomplete-data contract | integration registry, provider map | planned | B2.R1 row completion |
| `compliance_dashboard` | must be false | compliance evidence | show incomplete-data contract | legal, audit, ministry | planned | B2.R1 row completion |
| `document_SLA_dashboard` | must be false | document workflow evidence | show incomplete-data contract | document workflow, correspondence | planned | B2.R1 row completion |
| `academic_quality_scorecard` | must be false | quality and curriculum evidence | show incomplete-data contract | curriculum, outcomes, quality | planned | B2.R1 row completion |

## 14. Cross-Suite Bridge Map

| Bridge | Source Vertical | Target Vertical | Data Direction | Mutation Allowed | Read-Only First | Audit Required | Provider Allowed | Next Action |
|---|---|---|---|---|---|---|---|---|
| `academic_operations_to_student_lifecycle_bridge` | Academic Operations | Student Lifecycle | bi-directional reference | no | yes | yes | no | B2.R1 row completion |
| `academic_operations_to_document_workflow_bridge` | Academic Operations | Executive Governance / Document | metadata to document | no | yes | yes | no | B2.R1 row completion |
| `academic_operations_to_executive_governance_bridge` | Academic Operations | Executive Governance | summary upward | no | yes | yes | no | B2.R1 row completion |
| `academic_operations_to_quality_accreditation_bridge` | Academic Operations | Quality / Accreditation | evidence outward | no | yes | yes | no | B2.R1 row completion |
| `student_lifecycle_to_executive_control_tower_bridge` | Student Lifecycle | Executive Governance | summary upward | no | yes | yes | no | B2.R1 row completion |
| `research_to_accreditation_bridge` | Research | Quality | evidence outward | no | yes | yes | no | B2.R1 row completion |
| `HR_to_academic_operations_teaching_load_bridge` | HR | Academic Operations | workload and assignment | no | yes | yes | no | B2.R1 row completion |
| `finance_to_procurement_asset_bridge` | Finance | Procurement / Assets | bi-directional reference | no | yes | yes | no | B2.R1 row completion |
| `provider_layer_to_all_verticals_bridge` | Integration | All verticals | profile outward | no except provider lane | yes | yes | yes in provider lane only | B2.R1 row completion |
| `brain_layer_to_all_signal_enabled_verticals_bridge` | Brain Governance | All signal-enabled verticals | signals and drafts outward | no | yes | yes | no | B2.R1 row completion |

## 15. Gap Scoring Model

Priority:

- `P0 = core University OS completeness`
- `P1 = high-value operational depth`
- `P2 = later maturity`
- `P3 = optional or advanced`

Implementation lane:

- `NOW`
- `NEXT_VERTICAL`
- `LATER_VERTICAL`
- `BRIDGE_ONLY`
- `PROVIDER_DEFERRED`
- `BRAIN_DEFERRED`
- `FORBIDDEN`

Risk:

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

Completeness score fields:

- `coverage_status`
- `runtime_depth`
- `frontend_depth`
- `e2e_depth`
- `integration_depth`
- `brain_depth`
- `evidence_depth`

## 16. Seeded Detailed Rows

| capability_id | capability_name | canonical_module_name | source_plane | domain | product_vertical | capability_type | implementation_status | maturity_level | duplicate_risk | brain_readiness | provider_integration_need | dashboard_need | backend_needed | frontend_needed | e2e_needed | next_action |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `BAS-001` | admissions | admissions | BASELINE_150 | Student Lifecycle | Student Lifecycle Suite | EXISTING_CANONICAL_MODULE | IMPLEMENTED_RUNTIME | SEPARATE_OVERLAY | NONE | NO_BRAIN | FUTURE_READINESS_ONLY | MODULE_SUMMARY | ALREADY_EXISTS | ALREADY_EXISTS | ALREADY_EXISTS | preserve canonical |
| `BAS-002` | student_profile | student_profile | BASELINE_150 | Student Lifecycle | Student Lifecycle Suite | EXISTING_CANONICAL_MODULE | IMPLEMENTED_RUNTIME | SEPARATE_OVERLAY | NONE | NO_BRAIN | FUTURE_READINESS_ONLY | MODULE_SUMMARY | ALREADY_EXISTS | ALREADY_EXISTS | ALREADY_EXISTS | preserve canonical |
| `BAS-003` | executive_control_tower | executive_control_tower | BASELINE_150 | Governance / Rectorate / Strategy | Executive Governance Suite | EXISTING_CANONICAL_MODULE | IMPLEMENTED_RUNTIME | SEPARATE_OVERLAY | NONE | GOVERNANCE_ONLY | NONE | EXECUTIVE_VISIBILITY | ALREADY_EXISTS | ALREADY_EXISTS | ALREADY_EXISTS | preserve canonical |
| `UCE-009` | document_workflow | document_workflow | UNIVERSITY_COMPLETENESS_EXPANSION | Document / Decree / Correspondence | Executive Governance Suite | EXISTING_CANONICAL_MODULE | IMPLEMENTED_BACKEND_ONLY | L2 | RESOLVED_BY_ALIAS | NO_BRAIN | NON_LIVE_PROFILE_ONLY | OPERATIONAL_DASHBOARD | ALREADY_EXISTS | DEFERRED | DEFERRED | preserve canonical |
| `UCE-011` | order_decree_registry | order_decree_registry | UNIVERSITY_COMPLETENESS_EXPANSION | Document / Decree / Correspondence | Executive Governance Suite | EXISTING_CANONICAL_MODULE | IMPLEMENTED_BACKEND_ONLY | L2 | NONE | NO_BRAIN | NON_LIVE_PROFILE_ONLY | COMPLIANCE_DASHBOARD | ALREADY_EXISTS | DEFERRED | DEFERRED | preserve canonical |
| `UCE-038` | student_appeals_workflow | student_appeals_workflow | UNIVERSITY_COMPLETENESS_EXPANSION | Student Lifecycle | Student Lifecycle Suite | EXISTING_CANONICAL_MODULE | SPECIFIED_ONLY | L2 | RESOLVED_BY_ALIAS | GOVERNANCE_ONLY | NONE | MODULE_SUMMARY | ALREADY_EXISTS | DEFERRED | DEFERRED | preserve canonical |
| `UCE-039` | academic_calendar_governance_workflow | academic_calendar_governance_workflow | UNIVERSITY_COMPLETENESS_EXPANSION | Academic Operations | Academic Operations Suite | EXISTING_ADJACENT_MODULE | PLANNED | L2 | RESOLVED_BY_ALIAS | GOVERNANCE_ONLY | NONE | MODULE_SUMMARY | BRIDGE_ONLY | BRIDGE_ONLY | DEFERRED | reuse in academic runtime |
| `UCE-073` | elective_course_selection | elective_course_selection | UNIVERSITY_COMPLETENESS_EXPANSION | Academic Operations | Academic Operations Suite | EXISTING_CANONICAL_MODULE | PLANNED | L3 | NONE | NO_BRAIN | NONE | MODULE_SUMMARY | ALREADY_EXISTS | DEFERRED | DEFERRED | preserve canonical |
| `UCE-076` | course_catalog_management | course_catalog_management | UNIVERSITY_COMPLETENESS_EXPANSION | Academic Operations | Academic Operations Suite | EXISTING_CANONICAL_MODULE | PLANNED | L3 | NONE | NO_BRAIN | NONE | MODULE_SUMMARY | ALREADY_EXISTS | DEFERRED | DEFERRED | preserve canonical |
| `VRT-001` | academic_group_management | academic_group_management | PRODUCT_VERTICAL | Academic Operations | Academic Operations Suite | NEW_MODULE | SPECIFIED_ONLY | L0 | LOW | NO_BRAIN | NONE | MODULE_SUMMARY | YES | YES | YES | B2.R1 row completion |
| `VRT-002` | cohort_management | cohort_management | PRODUCT_VERTICAL | Academic Operations | Academic Operations Suite | NEW_MODULE | SPECIFIED_ONLY | L0 | MEDIUM | NO_BRAIN | NONE | MODULE_SUMMARY | YES | YES | YES | B2.R1 row completion |
| `VRT-003` | gradebook_metadata | gradebook_metadata | PRODUCT_VERTICAL | Academic Operations | Academic Operations Suite | NEW_MODULE | SPECIFIED_ONLY | L0 | LOW | GOVERNANCE_ONLY | NONE | OPERATIONAL_DASHBOARD | YES | YES | YES | canonical-aware runtime later |
| `VRT-004` | retake_management | retake_management | PRODUCT_VERTICAL | Academic Operations | Academic Operations Suite | NEW_MODULE | SPECIFIED_ONLY | L0 | MEDIUM | GOVERNANCE_ONLY | NONE | MODULE_SUMMARY | YES | YES | YES | B2.R1 row completion |
| `VRT-005` | summer_semester_management | summer_semester_management | PRODUCT_VERTICAL | Academic Operations | Academic Operations Suite | NEW_MODULE | SPECIFIED_ONLY | L0 | LOW | NO_BRAIN | NONE | MODULE_SUMMARY | YES | YES | YES | B2.R1 row completion |
| `VRT-006` | advisor_tutor_management | advisor_tutor_management | PRODUCT_VERTICAL | Student Support / Health / Career / Alumni | Academic Operations Suite | NEW_MODULE | SPECIFIED_ONLY | L0 | MEDIUM | GOVERNANCE_ONLY | NONE | MODULE_SUMMARY | YES | YES | YES | B2.R1 row completion |
| `BRN-001` | brain_signal_registry | brain_signal_registry | BRAIN_LAYER | AI / Brain / Agents / Automation | Brain Governance / Agent Suite | BRAIN_SIGNAL | PLANNED | L1 | LOW | SIGNAL_READY | FORBIDDEN | BRAIN_GOVERNANCE_DASHBOARD | YES | YES | DEFERRED | B2.R1 row completion |
| `INT-001` | integration_registry_ops | integration_registry_ops | INTEGRATION_LAYER | Integration / External Systems | Integration / Provider Suite | INTEGRATION | PLANNED | L1 | LOW | NO_BRAIN | NON_LIVE_PROFILE_ONLY | OPERATIONAL_DASHBOARD | YES | YES | DEFERRED | B2.R1 row completion |
| `RPT-001` | rector_strategy_dashboard | rector_strategy_dashboard | REPORTING_DASHBOARD | Governance / Rectorate / Strategy | Executive Governance Suite | REPORT_DASHBOARD | PLANNED | L1 | LOW | GOVERNANCE_ONLY | NONE | EXECUTIVE_VISIBILITY | YES | YES | DEFERRED | B2.R1 row completion |
| `BRG-001` | academic_operations_to_student_lifecycle_bridge | academic_operations_to_student_lifecycle_bridge | BRIDGE_CAPABILITY | Academic Operations | Academic Operations Suite | BRIDGE_TO_EXISTING_VERTICAL | PLANNED | NOT_APPLICABLE | RESOLVED_BY_BRIDGE | NO_BRAIN | NONE | OPERATIONAL_DASHBOARD | BRIDGE_ONLY | BRIDGE_ONLY | DEFERRED | bridge-first design |
| `FORBID-001` | autonomous_grading_FORBIDDEN | autonomous_grading_FORBIDDEN | FORBIDDEN_ACTION_REGISTRY | Academic Operations | Academic Operations Suite | FORBIDDEN_AUTONOMOUS_ACTION | FORBIDDEN | NOT_APPLICABLE | NONE | FORBIDDEN | FORBIDDEN | NONE | NO | NO | NO | keep forbidden |

## 17. Seeded Capability Universe Registry

The following section seeds the Full University OS universe and guarantees the listed capabilities are tracked. Exhaustive per-row completion against all 25 taxonomy fields is deferred to `A-036.2-B2.R1`.

### A. Governance / Rectorate / Executive Suite

- `VRT-010 rector_assignment_os`, `BAS-010 executive_control_tower`, `RPT-001 rector_strategy_dashboard`, `VRT-011 strategy_execution_office`, `VRT-012 rector_resolution_tracking`, `VRT-013 rector_resolution_tracking_workflow`, `BAS-011 internal_assignment_management`, `BAS-012 assignment_execution_tracking`, `BAS-013 assignment_evidence_management`, `BAS-014 assignment_sla_monitoring`, `RPT-002 executive_escalation_visibility`, `UCE-090 committee_decision_registry`, `BRN-010 governance_deviation_signal`, `VRT-014 policy_decision_register`, `VRT-015 rectorate_meeting_management`, `VRT-016 protocol_decision_tracking`, `BAS-015 executive_audit_trail`, `RPT-003 executive_kpi_visibility`, `RPT-004 leadership_operational_dashboard`

### B. Document / Decree / Correspondence / Archive Suite

- `UCE-009 document_workflow`, `VRT-020 document_workflow_os`, `UCE-010 internal_memo_routing`, `UCE-011 order_decree_registry`, `VRT-021 decree_registry_entries`, `VRT-022 rector_order_tracking`, `VRT-023 correspondence_management`, `VRT-024 incoming_correspondence`, `VRT-025 outgoing_correspondence`, `VRT-026 correspondence_routing`, `VRT-027 correspondence_sla_tracking`, `VRT-028 document_review_workflow`, `VRT-029 document_versioning`, `X-REF document_status_history`, `VRT-030 document_archive_records`, `UCE-012 archive_retention_management`, `VRT-031 archive_disposal_approval`, `X-REF document_audit_events`, `INT-010 digital_signature_readiness`, `INT-011 eds_signature_integration`

### C. Student Lifecycle Suite

- `BAS-001 admissions`, `VRT-040 applicant_management`, `VRT-041 admission_review`, `VRT-042 admission_decision_committee`, `VRT-043 admission_exception_workflow`, `BAS-002 student_profile`, `VRT-044 student_status_management`, `BAS-003 enrollment`, `BAS-004 academic_records`, `VRT-045 transcript_preview`, `VRT-046 transcript`, `VRT-047 degree_progress`, `UCE-092 degree_audit`, `VRT-048 graduation_readiness`, `UCE-075 transfer_credit_management`, `VRT-049 student_requests`, `UCE-038 student_appeals_workflow`, `VRT-050 student_appeal_management`, `BAS-005 interventions`, `RPT-010 student_success_risk_visibility`, `UCE-034 student_success_dashboard`, `X-REF student_lifecycle_audit`, `X-REF student_lifecycle_evidence`, `UCE-082 student_financial_hardship`, `UCE-037 scholarship_committee_workflow`, `VRT-051 student_discipline`, `VRT-052 student_disciplinary_case_management`, `BAS-006 student_portal`, `BAS-007 student_services`, `BAS-008 student_ai_tutor`

### D. Academic Operations Suite

- `VRT-060 curriculum_management`, `UCE-014 curriculum_mapping`, `UCE-015 syllabus_management`, `UCE-016 competency_framework`, `UCE-071 program_learning_outcomes`, `UCE-072 course_learning_outcomes`, `VRT-061 course_catalog`, `UCE-076 course_catalog_management`, `VRT-062 academic_calendar`, `UCE-039 academic_calendar_governance_workflow`, `VRT-001 academic_group_management`, `VRT-002 cohort_management`, `VRT-063 course_registration`, `UCE-073 elective_course_selection`, `VRT-064 prerequisite_validation`, `UCE-074 prerequisite_management`, `VRT-065 timetable_management`, `BAS-066 human_approved_timetable_workflow`, `BAS-067 timetable_change_proposal`, `BAS-068 timetable_change_simulation`, `BAS-069 timetable_recommendation_bridge`, `BAS-070 timetable_approval_queue`, `BAS-071 timetable_change_kpi_dashboard`, `VRT-072 classroom_room_allocation`, `BAS-072 room_booking`, `VRT-073 attendance_tracking`, `VRT-074 attendance_operations`, `VRT-075 teaching_load_management`, `UCE-067 teaching_load_contracts`, `BAS-073 workload_management`, `VRT-076 faculty_assignment_visibility`, `VRT-077 exam_planning`, `BAS-074 exam_governance`, `BAS-075 exam_proctoring`, `VRT-003 gradebook_metadata`, `VRT-078 grade_appeal_management`, `VRT-079 exam_appeal_management`, `VRT-080 academic_debt_tracking`, `VRT-004 retake_management`, `VRT-005 summer_semester_management`, `VRT-081 student_practice_management`, `VRT-082 thesis_supervision_management`, `UCE-077 thesis_dissertation_management`, `VRT-083 academic_committee_decisions`, `VRT-084 academic_policy_exception_tracking`, `VRT-085 academic_order_linkage`, `VRT-006 advisor_tutor_management`, `VRT-086 student_academic_support_tracking`, `VRT-087 academic_operations_dashboard`, `X-REF academic_operations_audit`

### E. Research / Science Suite

- `VRT-100 research_projects`, `VRT-101 research_activity_tracking`, `VRT-102 student_research_work`, `VRT-103 scientific_supervision_management`, `BAS-100 research_grants`, `VRT-104 grant_application_tracking`, `UCE-040 grant_deliverable_tracking_workflow`, `EXT-001 grant_peer_review`, `EXT-002 research_data_governance`, `VRT-105 research_data_management`, `VRT-106 publication_registry`, `BAS-101 publications`, `BAS-102 conference_management`, `VRT-107 conference_participation_tracking`, `BAS-103 lab_operations`, `BAS-104 research_ethics`, `VRT-108 research_ethics_approval`, `VRT-109 research_ethics_amendment_workflow`, `RPT-020 science_dashboard`, `RPT-021 research_performance_dashboard`, `X-REF research_evidence_repository`, `VRT-110 research_team_management`, `VRT-111 research_output_verification`, `VRT-112 research_compliance_audit`

### F. Quality / Accreditation / Compliance Suite

- `BAS-110 accreditation`, `BAS-111 accreditation_compliance`, `RPT-030 accreditation_dashboard`, `VRT-120 accreditation_evidence_repository`, `VRT-121 accreditation_evidence_workflow`, `VRT-122 accreditation_gap_tracking`, `VRT-123 program_accreditation`, `VRT-124 institutional_accreditation`, `VRT-125 academic_quality_management`, `BRN-020 academic_quality_signal_registry`, `VRT-126 quality_indicators`, `RPT-031 quality_scorecard`, `VRT-127 nonconformance_tracking`, `VRT-128 nonconformance_closure_workflow`, `VRT-129 internal_quality_audit`, `VRT-130 course_quality_review`, `VRT-131 program_review`, `VRT-132 learning_outcomes_assessment`, `VRT-133 quality_committee_decisions`, `VRT-134 regulatory_register`, `RPT-032 compliance_calendar_dashboard`, `VRT-135 compliance_calendar`, `BRN-021 compliance_breach_signal`, `VRT-136 policy_controls`, `VRT-137 policy_exception_tracking`

### G. HR / Staff / Faculty Governance Suite

- `UCE-001 staff_recruitment`, `UCE-002 staff_onboarding`, `UCE-003 employee_records`, `VRT-140 faculty_profile`, `UCE-008 position_budgeting`, `UCE-004 leave_management`, `UCE-005 performance_appraisal`, `UCE-006 training_certification`, `UCE-007 disciplinary_case_management`, `VRT-141 staff_disciplinary_case_management`, `BAS-073 workload_management`, `EXT-020 faculty_workload_optimizer`, `BRN-022 faculty_overload_signal`, `UCE-067 teaching_load_contracts`, `VRT-142 staff_attendance`, `VRT-143 staff_requests`, `VRT-144 staff_appeals`, `VRT-145 HR_policy_exceptions`, `BAS-120 hr_payroll`, `INT-020 hr_payroll_integration`, `UCE-025 one_c_integration`, `VRT-146 staff_exit_offboarding`, `VRT-147 staff_access_lifecycle`, `RPT-040 staff_compliance_dashboard`

### H. Finance / Procurement / Assets Suite

- `BAS-130 billing`, `BAS-131 budget_planning`, `UCE-033 finance_executive_dashboard`, `VRT-150 financial_close_orchestration`, `VRT-151 cost_center_management`, `BAS-132 online_payments`, `INT-021 payment_gateway_integration`, `UCE-026 bank_gateway_integration`, `EXT-030 billing_reconciliation_ops`, `EXT-031 revenue_leak_detection`, `BAS-133 procurement`, `BAS-134 procurement_approval_workflow`, `VRT-152 procurement_plan_approval_workflow`, `EXT-032 procurement_vendor_risk`, `BAS-135 vendor_management`, `BAS-136 contracts_legal_repository`, `BAS-137 asset_inventory`, `VRT-153 asset_lifecycle_management`, `BAS-138 inventory_management`, `BRN-023 finance_anomaly_signal_registry`, `X-REF finance_audit_trail`, `VRT-154 finance_policy_exception_tracking`, `VRT-155 tax_reporting_support`

### I. Legal / Contracts / Compliance / Audit Suite

- `BAS-136 contracts_legal_repository`, `VRT-160 contracts_hr`, `VRT-161 legal_case_tracking`, `VRT-162 contract_exception_escalation`, `VRT-134 regulatory_register`, `VRT-163 policy_register`, `BAS-160 audit`, `VRT-164 internal_audit_management`, `X-REF audit_evidence_repository`, `VRT-165 audit_findings_tracking`, `VRT-166 audit_closure_workflow`, `BRN-021 compliance_breach_signal`, `BAS-161 pdpl`, `EXT-040 privacy_request_orchestrator`, `EXT-041 data_retention_orchestrator`, `UCE-046 consent_management_policy`, `RPT-050 legal_compliance_dashboard`

### J. Campus / Facilities / Housing / Transport Suite

- `BAS-170 facilities_work_orders`, `VRT-171 facilities_maintenance`, `BAS-072 room_booking`, `VRT-072 classroom_room_allocation`, `VRT-172 room_capacity_metadata`, `UCE-017 dormitory_management`, `BAS-171 housing`, `VRT-173 housing_assignment_workflow`, `RPT-060 dormitory_occupancy_dashboard`, `BAS-172 transport`, `UCE-018 transport_shuttle_management`, `EXT-050 transport_fleet_ops`, `BAS-173 parking`, `BAS-174 parking_permit_ops`, `BAS-175 parking_enforcement`, `VRT-174 campus_incident_response`, `RPT-061 campus_safety_dashboard`, `BRN-024 facility_risk_signal`, `EXT-051 classroom_iot_telemetry`, `EXT-052 energy_optimization_ops`, `INT-030 access_control_turnstile_integration`

### K. Library / Knowledge / Archive Suite

- `BAS-180 library`, `BAS-181 library_circulation`, `BAS-182 digital_documents`, `BAS-183 records_hub`, `VRT-180 digital_repository`, `BAS-184 knowledge_retrieval`, `EXT-060 knowledge_retrieval_fabric`, `RPT-070 library_quality_dashboard`, `UCE-012 archive_retention_management`, `VRT-181 archive_disposal_approval`, `BRN-025 content_freshness_signal`, `BRG-020 research_repository_bridge`, `VRT-182 institutional_repository`, `BRG-021 document_archive_bridge`

### L. International / Mobility / Partnerships Suite

- `UCE-019 international_office`, `UCE-020 visa_support`, `VRT-190 mobility_management`, `VRT-191 student_exchange_management`, `VRT-192 visiting_student_management`, `VRT-193 international_student_support`, `UCE-022 partnership_registry`, `UCE-023 mou_lifecycle`, `VRT-194 mou_renewal_tracking`, `X-REF partnership_evidence_repository`, `RPT-080 international_mobility_dashboard`, `BRN-026 mobility_risk_signal`, `INT-040 visa_status_integration`, `VRT-195 international_agreement_workflow`

### M. Student Support / Health / Career / Alumni Suite

- `BAS-190 counseling`, `BAS-191 counseling_case_management`, `BAS-192 health_services`, `VRT-200 student_support_coordination`, `VRT-201 intervention_follow_up_workflow`, `BAS-193 career_services`, `BAS-194 alumni`, `EXT-070 alumni_career_outcomes`, `EXT-071 student_success_playbooks`, `UCE-034 student_success_dashboard`, `VRT-193 international_student_support`, `BRN-027 student_wellbeing_signal`, `INT-041 health_referral_integration`, `BRN-028 support_escalation_signal`

### N. Communications / Notifications / Community Suite

- `BAS-200 communications`, `BAS-201 notification_center`, `BAS-202 parent_portal`, `BAS-203 parent_engagement`, `VRT-023 correspondence_management`, `VRT-210 crisis_communication_workflow`, `UCE-027 email_gateway_integration`, `UCE-028 sms_gateway_integration`, `BRN-029 notification_failure_signal`, `RPT-090 communications_reliability_dashboard`, `VRT-211 community_feedback_management`, `VRT-212 announcement_management`, `VRT-213 event_notification_workflow`

### O. Security / IAM / SOC / Access Suite

- `BAS-210 auth`, `BAS-211 rbac`, `VRT-220 abac`, `BAS-212 access_control`, `BAS-213 security`, `BAS-214 security_operations`, `BAS-215 sso_saml`, `INT-050 identity_provider_integration`, `BAS-216 federation_management`, `BAS-217 local_user_management`, `VRT-221 privileged_access_management`, `VRT-222 soc_case_management`, `VRT-223 security_incident_triage_workflow`, `UCE-035 security_risk_dashboard`, `BRN-030 security_incident_signal`, `INT-051 siem_integration`, `EXT-080 threat_intel_fusion`, `VRT-224 mfa`, `VRT-225 session_management`, `BAS-218 tenant_spoofing_protection`, `X-REF audit_log_security`

### P. IT Operations / DevOps / Platform / SRE Suite

- `BAS-230 platform`, `BAS-231 platform_health`, `BAS-232 observability`, `BAS-233 jobs`, `BAS-234 scheduler`, `BAS-235 feature_flags`, `BAS-236 developer_portal`, `VRT-240 endpoint_inventory`, `VRT-241 patch_management`, `VRT-242 backup_restore_management`, `BAS-237 release_gate`, `VRT-243 deployment_readiness`, `VRT-244 rollback_readiness`, `RPT-100 platform_reliability_dashboard`, `BRN-031 platform_degradation_signal`, `INT-060 monitoring_federation_integration`, `VRT-245 docker_runtime_governance`, `VRT-246 nginx_edge_runtime`, `VRT-247 redis_runtime`, `VRT-248 postgres_runtime`, `VRT-249 pgbouncer_runtime`

### Q. Data / Analytics / KPI / BI Suite

- `BAS-250 analytics`, `BAS-251 platform_shared`, `VRT-260 kpi_registry`, `VRT-261 kpi_certification_workflow`, `VRT-262 data_catalog_governance`, `RPT-110 executive_data_trust_dashboard`, `BRN-032 KPI_quality_signal`, `VRT-263 semantic_context`, `VRT-264 education_graph`, `BAS-252 model_evaluation`, `VRT-265 data_lineage`, `VRT-266 data_quality_rules`, `X-REF dashboard_evidence_layer`, `VRT-267 reporting_pack_builder`, `INT-061 BI_warehouse_integration`, `VRT-268 analytics_permission_governance`

### R. Integration / Provider / External Systems Suite

- `INT-001 integration_registry_ops`, `RPT-120 integration_health_dashboard`, `BRN-033 integration_failure_signal`, `UCE-024 platonus_integration`, `INT-070 student_information_system_integration`, `INT-071 finance_erp_integration`, `UCE-025 one_c_integration`, `UCE-030 egov_integration`, `INT-072 government_services_integration`, `INT-073 regulatory_reporting_integration`, `INT-074 digital_signature_integration`, `INT-075 eds_kz_provider`, `INT-076 ministry_reporting_integration`, `INT-050 identity_provider_integration`, `INT-077 idp_sso_kz`, `INT-078 lms_integration`, `UCE-027 email_gateway_integration`, `UCE-028 sms_gateway_integration`, `INT-021 payment_gateway_integration`, `UCE-026 bank_gateway_integration`, `INT-020 hr_payroll_integration`, `UCE-029 biometric_device_integration`, `INT-079 library_repository_integration`, `INT-051 siem_integration`, `INT-080 iot_device_integration`

### S. Ministry / Government / Regulatory Reporting Suite

- `VRT-280 ministry_pack_orchestrator`, `UCE-032 ministry_reporting_dashboard`, `INT-073 regulatory_reporting_integration`, `VRT-281 ministry_submission_workflow`, `VRT-282 ministry_correction_workflow`, `X-REF government_filing_evidence`, `VRT-283 egov_policy_feed`, `INT-072 government_services_integration`, `BRN-034 filing_compliance_risk_signal`, `VRT-284 ministry_pack_status_tracking`, `X-REF official_reporting_audit`, `VRT-285 regulatory_deadline_calendar`

### T. AI / Brain / Agents / Automation Suite

- `BAS-260 brain_core`, `BRN-001 brain_signal_registry`, `UCE-049 student_risk_signal_registry`, `UCE-050 finance_anomaly_signal_registry`, `UCE-051 academic_quality_signal_registry`, `BRN-010 governance_deviation_signal`, `BRN-022 faculty_overload_signal`, `BRN-021 compliance_breach_signal`, `BRN-030 security_incident_signal`, `BRN-033 integration_failure_signal`, `BRN-024 facility_risk_signal`, `BRN-035 grant_execution_risk_signal`, `BRN-029 notification_failure_signal`, `BRN-032 KPI_quality_signal`, `BAS-261 decision_audit_trail`, `UCE-054 brain_decision_audit_trail`, `BAS-262 recommendation_audit`, `BRN-002 human_review_queue`, `BRN-003 brain_human_review_workflow`, `BRN-004 evidence_summary_agent`, `BRN-005 safe_task_drafting_agent`, `BRN-006 safe_policy_draft_agent`, `BRN-007 safe_report_draft_agent`, `BRN-008 safe_minutes_summary_agent`, `UCE-036 ai_governance_dashboard`, `RPT-130 decision_audit_dashboard`, `RPT-131 signal_health_dashboard`, `BAS-263 model_registry`, `EXT-090 ai_model_registry`, `BAS-264 prompt_management`, `EXT-091 prompt_lifecycle_governance`, `EXT-092 llm_eval_harness`, `EXT-093 model_cost_optimizer`, `BAS-265 ai_cost_governance`, `EXT-094 copilot_safety_ops`, `BAS-266 ai_guardrails`, `BAS-267 ai_gateway`, `BAS-268 ai_copilot_ops`, `BRN-009 autonomous_workflow_candidate_registry`, `FORBID-REG forbidden_autonomous_action_registry`

### U. Forbidden / Human-Review-Only Autonomous Actions

- `FORBID-001 autonomous_admissions_decision_FORBIDDEN`, `FORBID-002 autonomous_grading_FORBIDDEN`, `FORBID-003 autonomous_student_sanction_FORBIDDEN`, `FORBID-004 autonomous_academic_dismissal_FORBIDDEN`, `FORBID-005 autonomous_procurement_decision_FORBIDDEN`, `FORBID-006 autonomous_hr_disciplinary_decision_FORBIDDEN`, `FORBID-007 autonomous_financial_approval_FORBIDDEN`, `FORBID-008 autonomous_provider_submission_FORBIDDEN`, `FORBID-009 hidden_student_score_FORBIDDEN`, `FORBID-010 hidden_faculty_score_FORBIDDEN`, `FORBID-011 discriminatory_score_FORBIDDEN`, `FORBID-012 fake_kpi_FORBIDDEN`, `FORBID-013 fake_grade_FORBIDDEN`, `FORBID-014 fake_attendance_FORBIDDEN`, `FORBID-015 fake_accreditation_status_FORBIDDEN`

### V. Cross-Suite Bridge Capabilities

- `BRG-001 academic_operations_to_student_lifecycle_bridge`, `BRG-002 academic_operations_to_document_workflow_bridge`, `BRG-003 academic_operations_to_executive_governance_bridge`, `BRG-004 academic_operations_to_quality_accreditation_bridge`, `BRG-005 student_lifecycle_to_executive_control_tower_bridge`, `BRG-006 research_to_accreditation_bridge`, `BRG-007 HR_to_academic_operations_teaching_load_bridge`, `BRG-008 finance_to_procurement_asset_bridge`, `BRG-009 provider_layer_to_all_verticals_bridge`, `BRG-010 brain_layer_to_all_signal_enabled_verticals_bridge`, `BRG-011 document_workflow_to_order_decree_bridge`, `BRG-012 academic_order_to_document_decree_bridge`, `BRG-013 student_appeals_to_academic_committee_bridge`, `BRG-014 gradebook_to_academic_records_bridge`, `BRG-015 attendance_to_student_support_bridge`, `BRG-016 thesis_to_research_science_bridge`, `BRG-017 practice_to_partnership_registry_bridge`, `BRG-018 ministry_reporting_to_regulatory_compliance_bridge`

### W. Executive Dashboards / Command Centers

- `BAS-010 executive_control_tower`, `RPT-001 rector_strategy_dashboard`, `RPT-010 student_lifecycle_dashboard`, `RPT-011 academic_operations_dashboard`, `RPT-020 research_science_dashboard`, `RPT-030 accreditation_dashboard`, `UCE-033 finance_executive_dashboard`, `RPT-040 HR_operations_dashboard`, `UCE-035 security_risk_dashboard`, `RPT-120 integration_health_dashboard`, `UCE-032 ministry_reporting_dashboard`, `RPT-060 campus_operations_dashboard`, `RPT-070 library_archive_dashboard`, `UCE-036 AI_governance_dashboard`, `RPT-110 data_trust_dashboard`, `RPT-111 KPI_quality_dashboard`, `RPT-112 provider_readiness_dashboard`, `RPT-113 compliance_dashboard`, `RPT-114 document_SLA_dashboard`, `RPT-115 academic_quality_scorecard`

### X. Evidence / Audit / Trust Layer

- `X-REF audit_events`, `X-REF status_history`, `X-REF evidence_metadata`, `X-REF evidence_repository`, `X-REF dashboard_evidence_lineage`, `X-REF human_review_evidence`, `X-REF decision_evidence_pack`, `X-REF provider_readiness_evidence`, `X-REF compliance_evidence`, `X-REF accreditation_evidence`, `X-REF academic_operations_evidence`, `X-REF student_lifecycle_evidence`, `X-REF executive_governance_evidence`, `X-REF research_evidence`, `X-REF finance_audit_evidence`, `X-REF security_audit_evidence`, `X-REF data_quality_evidence`, `X-REF no_fake_metrics_contract`, `X-REF limitations_registry`, `X-REF incomplete_data_registry`

## 18. Must-Not-Forget Lists

### A. Must Not Forget - Core Missing University OS Capabilities

- strategy execution office
- ministry pack orchestrator
- integration registry ops
- KPI registry and certification workflow
- accreditation evidence repository
- HR staff core stack
- international office and partnership lifecycle
- research deliverable and data governance depth

### B. Already Covered - Do Not Duplicate

- executive control tower
- admissions and student lifecycle canonicals
- document workflow and order/decree registry
- attendance
- room booking
- workload management
- course catalog management
- elective course selection
- committee decision registry

### C. Bridge Required - Do Not Create Standalone Duplicate

- course registration to registrar
- timetable to existing scheduling family
- classroom allocation to room booking
- attendance to existing attendance canonical
- academic order linkage to document/decree canonicals
- student support tracking to counseling and student-success canonicals

### D. Future Verticals

- Research / Science Suite
- Quality / Accreditation Suite
- HR / Staff Governance Suite
- Campus / Facilities / Housing Suite
- International / Mobility / Partnerships Suite
- Integration / Provider Suite
- Brain Governance / Agent Suite
- Ministry / Regulatory Reporting Suite

### E. Brain Layer Candidates

- signal registries
- decision audit trail
- human review queue
- safe drafting agents
- governance dashboards

### F. Provider / Integration Candidates

- SIS / Platonus
- 1C / finance ERP
- eGov / government services
- EDS / digital signature
- ministry reporting connectors
- IDP / SSO
- LMS
- message gateways
- payment and banking rails
- SIEM and IoT layers

### G. Dashboards Required

- rector strategy dashboard
- academic operations dashboard
- research science dashboard
- accreditation dashboard
- finance executive dashboard
- security dashboard
- integration health dashboard
- ministry dashboard
- AI governance dashboard
- data trust / KPI quality dashboards

### H. Sensitive Deferred Modules

- grading and publication surfaces
- sanctions and dismissals
- procurement and financial approvals
- HR disciplinary decisions
- provider submission workflows

### I. Forbidden Autonomous Actions

- autonomous admissions decision
- autonomous grading
- autonomous sanctions
- autonomous procurement decision
- autonomous HR disciplinary decision
- autonomous provider submission
- hidden or discriminatory scoring
- fake KPI / fake academic evidence generation

### J. High-Value Demo Capabilities

- executive control tower
- student lifecycle dashboard
- academic operations dashboard
- document workflow plus decree registry
- finance executive dashboard
- research performance dashboard
- AI governance dashboard

### K. Enterprise / GCC / Compliance Future Readiness Capabilities

- audit evidence lineage
- provider readiness evidence
- ministry reporting evidence packs
- policy controls and retention workflows
- decision audit trails and human review queues

## 19. Duplicate Prevention Rules

1. Never create a new package when an existing canonical already covers the capability under a different trusted name.
2. Treat vertical umbrellas as planning lenses, not automatic package factories.
3. Default to bridge-first for registrar, document, attendance, room, dashboard, and evidence reuse.
4. Dashboard rows must not claim `fake_metrics=true` or invent source data.
5. Brain rows must default to governance, review, and drafting, not autonomous execution.
6. Provider rows must default to non-live readiness with no credentials and no external submission evidence unless separately implemented.

## 20. Anti-Fake / No-Overclaim Boundaries

- no runtime implementation claimed here
- no backend or frontend implementation claimed here unless separately evidenced
- no real data
- no credentials
- no provider integration execution
- no autonomous decision execution
- no hidden score
- no fake KPI
- no fake grades, attendance, research, finance, or accreditation metrics
- no production-ready claim
- no sales-ready claim
- no GCC readiness claim
- no L5/L6 claim

## 21. Current Matrix Decision

- Matrix framework created: yes
- Full-system ambition preserved: yes
- Duplicate prevention added: yes
- Exhaustive per-row completion done: no
- Reason exhaustive row completion is deferred: authoritative sources fully lock `175 + 54` plus seeded vertical universes, but do not yet canonically enumerate every row in a `450-520+` universe without further reconciliation work
- Recommended next action: `A-036.2-B2.R1`
