from __future__ import annotations

from typing import Any


class RiskClassifier:
    """Classifies core risk situations from normalized signal/context."""

    def classify(self, signal: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        event_type = str(signal.get("event_type") or "")
        academic = context.get("academic") or {}

        if event_type == "faculty.workload_overload.detected":
            workload_ratio = signal.get("payload", {}).get("workload_ratio")
            if isinstance(workload_ratio, (int, float)) and workload_ratio >= 1.4:
                return {
                    "situation_type": "faculty_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "faculty_overload_high",
                }
            return {
                "situation_type": "faculty_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "faculty_overload_medium",
            }

        if event_type == "finance.payment_overdue.detected":
            delinquency_days = signal.get("payload", {}).get("delinquency_days")
            if isinstance(delinquency_days, int) and delinquency_days >= 45:
                return {
                    "situation_type": "financial_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "payment_overdue_high",
                }
            return {
                "situation_type": "financial_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "payment_overdue_medium",
            }

        if event_type == "financial_aid.warning.detected":
            payload = signal.get("payload", {})
            to_status = str(payload.get("to_status") or "").strip().lower()
            if to_status == "rejected":
                return {
                    "situation_type": "student_success_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "financial_aid_warning_high",
                }
            return {
                "situation_type": "student_success_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "financial_aid_warning_medium",
            }

        if event_type == "housing.status.risk_detected":
            payload = signal.get("payload", {})
            to_status = str(payload.get("to_status") or "").strip().lower()
            if to_status == "rejected":
                return {
                    "situation_type": "student_success_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "housing_status_high",
                }
            return {
                "situation_type": "student_success_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "housing_status_medium",
            }

        if event_type == "finance.budget_variance.threshold_reached":
            payload = signal.get("payload", {})
            variance_ratio = payload.get("variance_ratio")
            variance_amount = payload.get("variance_amount")
            if (
                isinstance(variance_ratio, (int, float))
                and float(variance_ratio) >= 0.15
            ) or (
                isinstance(variance_amount, (int, float))
                and float(variance_amount) >= 25000
            ):
                return {
                    "situation_type": "procurement_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "procurement_budget_variance_high",
                }
            return {
                "situation_type": "procurement_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "procurement_budget_variance_medium",
            }

        if event_type == "procurement.vendor_sla.degraded":
            payload = signal.get("payload", {})
            sla_breach_rate = payload.get("sla_breach_rate")
            on_time_delivery_rate = payload.get("on_time_delivery_rate")
            if (
                isinstance(sla_breach_rate, (int, float))
                and float(sla_breach_rate) >= 0.20
            ) or (
                isinstance(on_time_delivery_rate, (int, float))
                and float(on_time_delivery_rate) <= 0.75
            ):
                return {
                    "situation_type": "procurement_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "procurement_vendor_sla_high",
                }
            return {
                "situation_type": "procurement_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "procurement_vendor_sla_medium",
            }

        if event_type == "procurement.contract_risk.high":
            payload = signal.get("payload", {})
            risk_score = payload.get("risk_score")
            sla_target_met = payload.get("sla_target_met")
            if (
                isinstance(risk_score, (int, float))
                and float(risk_score) >= 0.85
            ) or sla_target_met is False:
                return {
                    "situation_type": "procurement_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "procurement_contract_risk_high",
                }
            return {
                "situation_type": "procurement_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "procurement_contract_risk_medium",
            }

        if event_type == "operations.consumable_stock.low":
            stock_level = signal.get("payload", {}).get("stock_level")
            threshold = signal.get("payload", {}).get("threshold")
            projected_daily_usage = signal.get("payload", {}).get("projected_daily_usage")
            lead_time_days = signal.get("payload", {}).get("lead_time_days")
            auto_reorder = bool(signal.get("payload", {}).get("auto_reorder"))
            projected_days_remaining: float | None = None
            if isinstance(stock_level, (int, float)) and isinstance(projected_daily_usage, (int, float)) and float(projected_daily_usage) > 0:
                projected_days_remaining = float(stock_level) / float(projected_daily_usage)
            if isinstance(stock_level, (int, float)) and isinstance(threshold, (int, float)):
                if stock_level <= threshold * 0.5:
                    return {
                        "situation_type": "operational_risk",
                        "severity": "high",
                        "urgency": "high",
                        "reasoning_path": "supply_low_critical",
                    }
            if (
                auto_reorder
                and projected_days_remaining is not None
                and isinstance(lead_time_days, int)
                and projected_days_remaining <= max(7, lead_time_days)
            ):
                return {
                    "situation_type": "operational_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "supply_low_critical",
                }
            return {
                "situation_type": "operational_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "supply_low_medium",
            }

        if event_type == "accreditation.status_changed":
            payload = signal.get("payload", {})
            risk_level = str(payload.get("risk_level") or "").strip().lower()
            new_status = str(payload.get("new_status") or payload.get("status") or "").strip().lower()
            if risk_level in {"critical", "high"} or new_status in {"at_risk", "probation", "revoked"}:
                return {
                    "situation_type": "compliance_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "accreditation_risk_high",
                }
            return {
                "situation_type": "compliance_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "accreditation_risk_medium",
            }

        if event_type == "platform.workflow.failed":
            payload = signal.get("payload", {})
            failure_count = payload.get("failure_count")
            severity = str(payload.get("severity") or "").strip().lower()
            if severity in {"critical", "high"} or (isinstance(failure_count, int) and failure_count >= 3):
                return {
                    "situation_type": "platform_reliability_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "platform_workflow_failed_critical",
                }
            return {
                "situation_type": "platform_reliability_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "platform_workflow_failed_medium",
            }

        if event_type == "platform.integration.degraded":
            payload = signal.get("payload", {})
            error_rate = payload.get("error_rate")
            severity = str(payload.get("severity") or "").strip().lower()
            if severity in {"critical", "high"} or (isinstance(error_rate, (int, float)) and float(error_rate) >= 0.10):
                return {
                    "situation_type": "platform_reliability_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "platform_integration_degraded_critical",
                }
            return {
                "situation_type": "platform_reliability_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "platform_integration_degraded_medium",
            }

        if event_type == "research.grant_deadline.approaching":
            payload = signal.get("payload", {})
            days_to_deadline = payload.get("days_to_deadline")
            if isinstance(days_to_deadline, int) and days_to_deadline <= 14:
                return {
                    "situation_type": "research_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "research_grant_deadline_high",
                }
            return {
                "situation_type": "research_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "research_grant_deadline_medium",
            }

        if event_type == "research.publication_stagnant":
            payload = signal.get("payload", {})
            days_without_progress = payload.get("days_without_progress")
            if isinstance(days_without_progress, int) and days_without_progress >= 60:
                return {
                    "situation_type": "research_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "research_publication_stagnant_high",
                }
            return {
                "situation_type": "research_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "research_publication_stagnant_medium",
            }

        if event_type == "research.grant_pipeline.at_risk":
            payload = signal.get("payload", {})
            pipeline_risk_score = payload.get("pipeline_risk_score")
            delayed_milestones = payload.get("delayed_milestones")
            if (
                isinstance(pipeline_risk_score, (int, float))
                and float(pipeline_risk_score) >= 0.75
            ) or (
                isinstance(delayed_milestones, int)
                and delayed_milestones >= 2
            ):
                return {
                    "situation_type": "research_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "research_grant_pipeline_risk_high",
                }
            return {
                "situation_type": "research_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "research_grant_pipeline_risk_medium",
            }

        if event_type == "research.lab_utilization.low":
            payload = signal.get("payload", {})
            utilization_rate = payload.get("utilization_rate")
            idle_days = payload.get("idle_days")
            if (
                isinstance(utilization_rate, (int, float))
                and float(utilization_rate) <= 0.40
                and isinstance(idle_days, int)
                and idle_days >= 30
            ):
                return {
                    "situation_type": "research_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "research_lab_utilization_low_high",
                }
            return {
                "situation_type": "research_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "research_lab_utilization_low_medium",
            }

        if event_type == "operations.facility_issue.reported":
            payload = signal.get("payload", {})
            severity = str(payload.get("severity") or "").strip().lower()
            if severity in {"critical", "high"}:
                return {
                    "situation_type": "operational_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "operations_facility_issue_high",
                }
            return {
                "situation_type": "operational_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "operations_facility_issue_medium",
            }

        if event_type == "campus.security_incident.detected":
            payload = signal.get("payload", {})
            severity = str(payload.get("severity") or "").strip().lower()
            if severity in {"critical", "high"}:
                return {
                    "situation_type": "operational_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "operations_facility_issue_high",
                }
            return {
                "situation_type": "operational_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "operations_facility_issue_medium",
            }

        if event_type == "campus.transport.disruption_detected":
            payload = signal.get("payload", {})
            route_status = str(payload.get("route_status") or "").strip().lower()
            if route_status == "cancelled":
                return {
                    "situation_type": "operational_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "operations_facility_issue_high",
                }
            return {
                "situation_type": "operational_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "operations_facility_issue_medium",
            }

        if event_type == "campus.dining.capacity_exceeded":
            return {
                "situation_type": "operational_risk",
                "severity": "high",
                "urgency": "high",
                "reasoning_path": "operations_facility_issue_high",
            }

        if event_type == "operations.cleaning_service.missed":
            payload = signal.get("payload", {})
            missed_count = payload.get("missed_count")
            if isinstance(missed_count, int) and missed_count >= 2:
                return {
                    "situation_type": "operational_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "operations_cleaning_missed_high",
                }
            return {
                "situation_type": "operational_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "operations_cleaning_missed_medium",
            }

        if event_type == "operations.maintenance.predicted_due":
            payload = signal.get("payload", {})
            days_since_maintenance = payload.get("days_since_maintenance")
            expected_service_interval_days = payload.get("expected_service_interval_days")
            health_score = payload.get("health_score")
            days_overdue: int | None = None
            if isinstance(days_since_maintenance, int) and isinstance(expected_service_interval_days, int):
                days_overdue = days_since_maintenance - expected_service_interval_days
            if (
                isinstance(days_overdue, int)
                and days_overdue >= 14
            ) or (
                isinstance(health_score, (int, float))
                and float(health_score) <= 25
            ):
                return {
                    "situation_type": "operational_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "operations_maintenance_predicted_due_high",
                }
            return {
                "situation_type": "operational_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "operations_maintenance_predicted_due_medium",
            }

        if event_type == "operations.utilities.spike_detected":
            payload = signal.get("payload", {})
            spike_ratio = payload.get("spike_ratio")
            affected_buildings = payload.get("affected_buildings")
            if (
                isinstance(spike_ratio, (int, float))
                and float(spike_ratio) >= 1.5
            ) or (
                isinstance(affected_buildings, int)
                and affected_buildings >= 2
            ):
                return {
                    "situation_type": "operational_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "operations_utilities_spike_high",
                }
            return {
                "situation_type": "operational_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "operations_utilities_spike_medium",
            }

        if event_type == "student_life.wellbeing.at_risk":
            payload = signal.get("payload", {})
            wellbeing_score = payload.get("wellbeing_score")
            if isinstance(wellbeing_score, int) and wellbeing_score <= 30:
                return {
                    "situation_type": "student_success_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "student_life_wellbeing_high",
                }
            return {
                "situation_type": "student_success_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "student_life_wellbeing_medium",
            }

        if event_type == "student_life.disciplinary.incident_reported":
            payload = signal.get("payload", {})
            incident_count = payload.get("incident_count_30d")
            incident_severity = str(payload.get("incident_severity") or "").strip().lower()
            if incident_severity in {"high", "critical"} or (isinstance(incident_count, int) and incident_count >= 2):
                return {
                    "situation_type": "student_success_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "student_life_disciplinary_high",
                }
            return {
                "situation_type": "student_success_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "student_life_disciplinary_medium",
            }

        if event_type == "thesis.status_changed":
            days_since_last_milestone = signal.get("payload", {}).get("days_since_last_milestone")
            if isinstance(days_since_last_milestone, int) and days_since_last_milestone > 60:
                return {
                    "situation_type": "academic_risk",
                    "severity": "medium",
                    "urgency": "medium",
                    "reasoning_path": "thesis_delay_medium",
                }
            return {
                "situation_type": "academic_risk",
                "severity": "low",
                "urgency": "low",
                "reasoning_path": "thesis_delay_low",
            }

        if event_type.startswith("academic."):
            payload = signal.get("payload", {})
            attendance_rate = academic.get("attendance_rate")
            if not isinstance(attendance_rate, (int, float)):
                attendance_rate = payload.get("attendance_rate")
            if isinstance(attendance_rate, (int, float)) and attendance_rate < 0.40:
                return {
                    "situation_type": "academic_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "risk_high",
                }
            if isinstance(attendance_rate, (int, float)) and attendance_rate < 0.60:
                return {
                    "situation_type": "academic_risk",
                    "severity": "medium",
                    "urgency": "medium",
                    "reasoning_path": "risk_medium",
                }

            return {
                "situation_type": "academic_risk",
                "severity": "low",
                "urgency": "low",
                "reasoning_path": "risk_low",
            }

        if event_type == "degree_progress.graduation_risk.detected":
            payload = signal.get("payload", {})
            remaining_required_items = payload.get("remaining_required_items")
            credits_earned = payload.get("credits_earned")
            minimum_credits = payload.get("minimum_credits")
            # High risk if significant remaining requirements (more than 2 courses)
            if isinstance(remaining_required_items, int) and remaining_required_items > 2:
                return {
                    "situation_type": "academic_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "graduation_risk_high",
                }
            # Medium risk if close to minimum credits but not quite there
            if (
                isinstance(credits_earned, int)
                and isinstance(minimum_credits, int)
                and credits_earned < minimum_credits
            ):
                if minimum_credits - credits_earned <= 6:  # Roughly 2 courses remaining
                    return {
                        "situation_type": "academic_risk",
                        "severity": "medium",
                        "urgency": "medium",
                        "reasoning_path": "graduation_risk_medium",
                    }
                return {
                    "situation_type": "academic_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "graduation_risk_high",
                }
            # Default to low risk if just missing some optional items
            return {
                "situation_type": "academic_risk",
                "severity": "low",
                "urgency": "low",
                "reasoning_path": "graduation_risk_low",
            }

        if event_type == "enrollments.dropout_risk.detected":
            payload = signal.get("payload", {})
            to_status = str(payload.get("to_status") or "").strip().lower()
            if to_status in {"withdrawn", "suspended"}:
                return {
                    "situation_type": "academic_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "enrollment_dropout_high",
                }
            return {
                "situation_type": "academic_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "enrollment_dropout_medium",
            }

        if event_type == "academic_integrity.case.escalated":
            payload = signal.get("payload", {})
            case_type = str(payload.get("case_type") or "").strip().lower()
            if case_type in {"plagiarism", "cheating", "fabrication"}:
                return {
                    "situation_type": "academic_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "academic_integrity_high",
                }
            return {
                "situation_type": "academic_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "academic_integrity_medium",
            }

        if event_type == "academic_records.inconsistency.detected":
            payload = signal.get("payload", {})
            issue_count = payload.get("issue_count")
            if isinstance(issue_count, int) and issue_count >= 5:
                return {
                    "situation_type": "compliance_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "academic_records_inconsistency_high",
                }
            return {
                "situation_type": "compliance_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "academic_records_inconsistency_medium",
            }

        if event_type == "programs.status.risk_detected":
            payload = signal.get("payload", {})
            to_status = str(payload.get("to_status") or "").strip().lower()
            if to_status in {"archived", "inactive"}:
                if to_status == "archived":
                    return {
                        "situation_type": "academic_risk",
                        "severity": "high",
                        "urgency": "high",
                        "reasoning_path": "programs_status_high",
                    }
            return {
                "situation_type": "academic_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "programs_status_medium",
            }

        if event_type == "courses.status.risk_detected":
            payload = signal.get("payload", {})
            to_status = str(payload.get("to_status") or "").strip().lower()
            if to_status == "archived":
                return {
                    "situation_type": "academic_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "courses_status_high",
                }
            return {
                "situation_type": "academic_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "courses_status_medium",
            }

        if event_type == "transcripts.inconsistency.detected":
            payload = signal.get("payload", {})
            issue_count = payload.get("issue_count")
            if isinstance(issue_count, int) and issue_count >= 3:
                return {
                    "situation_type": "compliance_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "transcripts_inconsistency_high",
                }
            return {
                "situation_type": "compliance_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "transcripts_inconsistency_medium",
            }

        if event_type == "student_services.ticket.escalated":
            payload = signal.get("payload", {})
            priority = str(payload.get("priority") or "").strip().lower()
            if priority == "high":
                return {
                    "situation_type": "student_success_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "student_services_escalation_high",
                }
            return {
                "situation_type": "student_success_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "student_services_escalation_medium",
            }

        if event_type == "admissions.decision.made":
            payload = signal.get("payload", {})
            decision_outcome = str(
                payload.get("decision_outcome") or payload.get("outcome") or ""
            ).strip().lower()
            risk_score = payload.get("risk_score")
            if decision_outcome in {"rejected", "conditional"} or (
                isinstance(risk_score, (int, float)) and float(risk_score) >= 0.70
            ):
                return {
                    "situation_type": "academic_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "admissions_decision_high",
                }
            return {
                "situation_type": "academic_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "admissions_decision_medium",
            }

        if event_type == "scheduling.section.scheduled":
            payload = signal.get("payload", {})
            current_sections = payload.get("current_sections")
            max_sections_threshold = payload.get("max_sections_threshold")
            overload_flag = bool(payload.get("overload_flag"))
            if overload_flag or (
                isinstance(current_sections, int)
                and isinstance(max_sections_threshold, int)
                and current_sections > max_sections_threshold
            ):
                return {
                    "situation_type": "faculty_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "scheduling_overload_high",
                }
            return {
                "situation_type": "faculty_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "scheduling_section_scheduled_medium",
            }

        # A-013.3: Scheduling conflict signal
        if event_type == "scheduling.section.conflict_detected":
            payload = signal.get("payload", {})
            conflict_type = str(payload.get("conflict_type") or "").strip().lower()
            if conflict_type in {"room_conflict", "instructor_conflict"}:
                return {
                    "situation_type": "operational_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "section_conflict_high",
                }
            return {
                "situation_type": "operational_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "section_conflict_medium",
            }

        # A-013.3: Enrollment capacity risk signal
        if event_type == "enrollment.capacity_risk.detected":
            payload = signal.get("payload", {})
            fill_rate = payload.get("fill_rate")
            enrolled_count = payload.get("enrolled_count")
            max_capacity = payload.get("max_capacity")
            if fill_rate is None and enrolled_count is not None and max_capacity:
                try:
                    fill_rate = float(enrolled_count) / float(max_capacity)
                except (ZeroDivisionError, TypeError, ValueError):
                    fill_rate = None
            if fill_rate is not None and float(fill_rate) >= 0.90:
                return {
                    "situation_type": "academic_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "enrollment_capacity_risk_high",
                }
            return {
                "situation_type": "academic_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "enrollment_capacity_risk_medium",
            }

        return {
            "situation_type": "operational_risk",
            "severity": "low",
            "urgency": "low",
            "reasoning_path": "default",
        }
