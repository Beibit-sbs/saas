from __future__ import annotations

from typing import Any


class RulesEngine:
    """Deterministic rules for first Brain Core scenarios."""

    def evaluate(self, classification: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        situation_type = classification.get("situation_type")
        severity = classification.get("severity")
        reasoning_path = classification.get("reasoning_path")

        if reasoning_path in {"thesis_delay_medium", "thesis_delay_low"}:
            if reasoning_path == "thesis_delay_medium":
                return {
                    "decision_type": "preventive",
                    "priority": "high",
                    "recommended_actions": [
                        "create_supervision_task",
                        "notify_faculty",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "preventive",
                "priority": "medium",
                "recommended_actions": ["notify_faculty"],
                "requires_approval": False,
            }

        if reasoning_path in {"faculty_overload_high", "faculty_overload_medium"}:
            if reasoning_path == "faculty_overload_high":
                return {
                    "decision_type": "optimization",
                    "priority": "high",
                    "recommended_actions": [
                        "create_workload_review_task",
                        "notify_faculty",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "optimization",
                "priority": "medium",
                "recommended_actions": ["create_workload_review_task"],
                "requires_approval": False,
            }

        if reasoning_path in {"payment_overdue_high", "payment_overdue_medium"}:
            if reasoning_path == "payment_overdue_high":
                return {
                    "decision_type": "risk",
                    "priority": "critical",
                    "recommended_actions": [
                        "create_collections_case",
                        "notify_finance",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "risk",
                "priority": "high",
                "recommended_actions": ["create_collections_case"],
                "requires_approval": False,
            }

        if reasoning_path in {
            "financial_aid_warning_high",
            "financial_aid_warning_medium",
            "housing_status_high",
            "housing_status_medium",
        }:
            if reasoning_path in {"financial_aid_warning_high", "housing_status_high"}:
                return {
                    "decision_type": "risk",
                    "priority": "critical",
                    "recommended_actions": [
                        "create_student_support_case",
                        "notify_student_success_team",
                        "notify_advisor",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "preventive",
                "priority": "medium",
                "recommended_actions": [
                    "create_student_support_case",
                    "notify_student_success_team",
                ],
                "requires_approval": False,
            }

        if reasoning_path in {
            "procurement_budget_variance_high",
            "procurement_budget_variance_medium",
            "procurement_vendor_sla_high",
            "procurement_vendor_sla_medium",
            "procurement_contract_risk_high",
            "procurement_contract_risk_medium",
        }:
            if reasoning_path in {
                "procurement_budget_variance_high",
                "procurement_vendor_sla_high",
                "procurement_contract_risk_high",
            }:
                return {
                    "decision_type": "procurement",
                    "priority": "high",
                    "recommended_actions": [
                        "initiate_procurement_request",
                        "notify_procurement_team",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "procurement",
                "priority": "medium",
                "recommended_actions": ["initiate_procurement_request"],
                "requires_approval": False,
            }

        if reasoning_path in {"supply_low_critical", "supply_low_medium"}:
            if reasoning_path == "supply_low_critical":
                return {
                    "decision_type": "operational",
                    "priority": "high",
                    "recommended_actions": [
                        "create_replenishment_task",
                        "initiate_procurement_request",
                        "notify_operations",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "operational",
                "priority": "medium",
                "recommended_actions": ["create_replenishment_task"],
                "requires_approval": False,
            }

        if reasoning_path in {"accreditation_risk_high", "accreditation_risk_medium"}:
            if reasoning_path == "accreditation_risk_high":
                return {
                    "decision_type": "compliance",
                    "priority": "critical",
                    "recommended_actions": [
                        "create_accreditation_remediation_workflow",
                        "notify_compliance",
                    ],
                    "requires_approval": True,
                }
            return {
                "decision_type": "compliance",
                "priority": "high",
                "recommended_actions": [
                    "create_accreditation_remediation_workflow",
                ],
                "requires_approval": False,
            }

        if reasoning_path in {
            "platform_workflow_failed_critical",
            "platform_workflow_failed_medium",
            "platform_integration_degraded_critical",
            "platform_integration_degraded_medium",
        }:
            if reasoning_path in {"platform_workflow_failed_critical", "platform_integration_degraded_critical"}:
                return {
                    "decision_type": "operational",
                    "priority": "critical",
                    "recommended_actions": [
                        "create_platform_reliability_incident",
                        "notify_platform",
                    ],
                    "requires_approval": True,
                }
            return {
                "decision_type": "operational",
                "priority": "high",
                "recommended_actions": [
                    "create_platform_reliability_incident",
                ],
                "requires_approval": False,
            }

        if reasoning_path in {
            "research_grant_deadline_high",
            "research_grant_deadline_medium",
            "research_publication_stagnant_high",
            "research_publication_stagnant_medium",
            "research_grant_pipeline_risk_high",
            "research_grant_pipeline_risk_medium",
            "research_lab_utilization_low_high",
            "research_lab_utilization_low_medium",
        }:
            if reasoning_path in {
                "research_grant_deadline_high",
                "research_publication_stagnant_high",
                "research_grant_pipeline_risk_high",
                "research_lab_utilization_low_high",
            }:
                return {
                    "decision_type": "preventive",
                    "priority": "high",
                    "recommended_actions": [
                        "create_research_remediation_workflow",
                        "notify_research_office",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "preventive",
                "priority": "medium",
                "recommended_actions": [
                    "create_research_remediation_workflow",
                ],
                "requires_approval": False,
            }

        if reasoning_path in {
            "operations_facility_issue_high",
            "operations_facility_issue_medium",
            "operations_cleaning_missed_high",
            "operations_cleaning_missed_medium",
            "operations_maintenance_predicted_due_high",
            "operations_maintenance_predicted_due_medium",
            "operations_utilities_spike_high",
            "operations_utilities_spike_medium",
        }:
            if reasoning_path in {
                "operations_facility_issue_high",
                "operations_cleaning_missed_high",
                "operations_maintenance_predicted_due_high",
                "operations_utilities_spike_high",
            }:
                return {
                    "decision_type": "operational",
                    "priority": "high",
                    "recommended_actions": [
                        "create_facility_incident_workflow",
                        "notify_facilities_team",
                    ],
                    "requires_approval": False,
                }
            if reasoning_path in {
                "operations_maintenance_predicted_due_medium",
                "operations_utilities_spike_medium",
            }:
                return {
                    "decision_type": "operational",
                    "priority": "medium",
                    "recommended_actions": [
                        "create_facility_incident_workflow",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "operational",
                "priority": "medium",
                "recommended_actions": [
                    "create_cleaning_recovery_task",
                ],
                "requires_approval": False,
            }

        if reasoning_path in {
            "student_life_wellbeing_high",
            "student_life_wellbeing_medium",
            "student_life_disciplinary_high",
            "student_life_disciplinary_medium",
        }:
            if reasoning_path in {
                "student_life_wellbeing_high",
                "student_life_disciplinary_high",
            }:
                return {
                    "decision_type": "risk",
                    "priority": "high",
                    "recommended_actions": [
                        "create_student_support_case",
                        "notify_student_success_team",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "risk",
                "priority": "medium",
                "recommended_actions": [
                    "create_disciplinary_review_case",
                ],
                "requires_approval": False,
            }

        if reasoning_path in {"risk_high", "risk_medium", "risk_low"}:
            if reasoning_path == "risk_high":
                return {
                    "decision_type": "risk",
                    "priority": "critical",
                    "recommended_actions": [
                        "create_intervention_case",
                        "notify_advisor",
                        "notify_faculty",
                    ],
                    "requires_approval": False,
                }
            if reasoning_path == "risk_medium":
                return {
                    "decision_type": "risk",
                    "priority": "high",
                    "recommended_actions": [
                        "create_intervention_case",
                        "notify_advisor",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "preventive",
                "priority": "medium",
                "recommended_actions": ["notify_advisor"],
                "requires_approval": False,
            }

        if reasoning_path in {"graduation_risk_high", "graduation_risk_medium", "graduation_risk_low"}:
            if reasoning_path == "graduation_risk_high":
                return {
                    "decision_type": "risk",
                    "priority": "critical",
                    "recommended_actions": [
                        "create_graduation_audit_case",
                        "notify_academic_advisor",
                        "escalate_to_dean",
                    ],
                    "requires_approval": False,
                }
            if reasoning_path == "graduation_risk_medium":
                return {
                    "decision_type": "preventive",
                    "priority": "high",
                    "recommended_actions": [
                        "create_graduation_audit_case",
                        "notify_academic_advisor",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "preventive",
                "priority": "low",
                "recommended_actions": ["notify_academic_advisor"],
                "requires_approval": False,
            }

        if reasoning_path in {"enrollment_dropout_high", "enrollment_dropout_medium"}:
            if reasoning_path == "enrollment_dropout_high":
                return {
                    "decision_type": "risk",
                    "priority": "critical",
                    "recommended_actions": [
                        "create_dropout_intervention",
                        "notify_enrollment_advisor",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "risk",
                "priority": "high",
                "recommended_actions": [
                    "create_dropout_intervention",
                    "notify_enrollment_advisor",
                ],
                "requires_approval": False,
            }

        if reasoning_path in {"academic_integrity_high", "academic_integrity_medium"}:
            if reasoning_path == "academic_integrity_high":
                return {
                    "decision_type": "compliance",
                    "priority": "critical",
                    "recommended_actions": [
                        "create_integrity_review_case",
                        "notify_registrar",
                    ],
                    "requires_approval": True,
                }
            return {
                "decision_type": "compliance",
                "priority": "high",
                "recommended_actions": [
                    "create_integrity_review_case",
                    "notify_registrar",
                ],
                "requires_approval": False,
            }

        if reasoning_path in {
            "academic_records_inconsistency_high",
            "academic_records_inconsistency_medium",
        }:
            if reasoning_path == "academic_records_inconsistency_high":
                return {
                    "decision_type": "compliance",
                    "priority": "high",
                    "recommended_actions": [
                        "create_records_review_task",
                        "notify_registrar",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "compliance",
                "priority": "medium",
                "recommended_actions": ["create_records_review_task"],
                "requires_approval": False,
            }

        if reasoning_path in {"programs_status_high", "programs_status_medium"}:
            if reasoning_path == "programs_status_high":
                return {
                    "decision_type": "risk",
                    "priority": "high",
                    "recommended_actions": [
                        "create_program_review_task",
                        "notify_academic_dean",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "risk",
                "priority": "medium",
                "recommended_actions": ["create_program_review_task"],
                "requires_approval": False,
            }

        if reasoning_path in {"courses_status_high", "courses_status_medium"}:
            if reasoning_path == "courses_status_high":
                return {
                    "decision_type": "risk",
                    "priority": "high",
                    "recommended_actions": [
                        "create_course_review_task",
                        "notify_academic_dean",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "risk",
                "priority": "medium",
                "recommended_actions": ["create_course_review_task"],
                "requires_approval": False,
            }

        if reasoning_path in {
            "transcripts_inconsistency_high",
            "transcripts_inconsistency_medium",
        }:
            if reasoning_path == "transcripts_inconsistency_high":
                return {
                    "decision_type": "compliance",
                    "priority": "high",
                    "recommended_actions": [
                        "create_transcript_review_task",
                        "notify_registrar",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "compliance",
                "priority": "medium",
                "recommended_actions": ["create_transcript_review_task"],
                "requires_approval": False,
            }

        if reasoning_path in {
            "student_services_escalation_high",
            "student_services_escalation_medium",
        }:
            if reasoning_path == "student_services_escalation_high":
                return {
                    "decision_type": "risk",
                    "priority": "high",
                    "recommended_actions": [
                        "create_student_support_case",
                        "notify_student_success_team",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "risk",
                "priority": "medium",
                "recommended_actions": ["create_student_support_case"],
                "requires_approval": False,
            }

        if situation_type == "academic_risk":
            if severity == "high":
                return {
                    "decision_type": "risk",
                    "priority": "critical",
                    "recommended_actions": [
                        "create_intervention_case",
                        "notify_advisor",
                        "notify_faculty",
                    ],
                    "requires_approval": False,
                }
            if severity == "medium":
                return {
                    "decision_type": "risk",
                    "priority": "high",
                    "recommended_actions": [
                        "create_intervention_case",
                        "notify_advisor",
                    ],
                    "requires_approval": False,
                }
            return {
                "decision_type": "preventive",
                "priority": "medium",
                "recommended_actions": ["notify_advisor"],
                "requires_approval": False,
            }

        return {
            "decision_type": "operational",
            "priority": "low",
            "recommended_actions": [],
            "requires_approval": True,
        }
