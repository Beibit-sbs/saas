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

        if event_type in {
            "finance.expense.budget_exceeded",
            "campus.budget.overrun_risk_detected",
            "campus.expense_controls.budget_exceeded_risk_detected",
        }:
            payload = signal.get("payload", {})
            risk_level = str(payload.get("risk_level") or "").strip().lower()
            overrun_amount = payload.get("overrun_amount")
            overrun_percent = payload.get("overrun_percent")
            if overrun_percent is None:
                overrun_percent = payload.get("overrun_ratio")

            if risk_level in {"critical", "high"}:
                return {
                    "situation_type": "financial_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "budget_overrun_high",
                }

            if (
                isinstance(overrun_percent, (int, float))
                and float(overrun_percent) >= 0.10
            ) or (
                isinstance(overrun_amount, (int, float))
                and float(overrun_amount) >= 10000.0
            ):
                return {
                    "situation_type": "financial_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "budget_overrun_high",
                }

            if risk_level == "low" or (
                isinstance(overrun_percent, (int, float))
                and float(overrun_percent) < 0.03
            ):
                return {
                    "situation_type": "financial_risk",
                    "severity": "low",
                    "urgency": "low",
                    "reasoning_path": "budget_overrun_low",
                }

            return {
                "situation_type": "financial_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "budget_overrun_medium",
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

        if event_type == "scholarship.award.at_risk_detected":
            payload = signal.get("payload", {})
            risk_level = str(payload.get("risk_level") or "").strip().lower()
            current_gpa = payload.get("current_gpa")
            gpa_threshold = payload.get("gpa_threshold")
            status = str(payload.get("status") or "").strip().lower()
            if risk_level in {"critical", "high"}:
                return {
                    "situation_type": "student_success_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "scholarship_award_risk_high",
                }
            if (
                isinstance(current_gpa, (int, float))
                and isinstance(gpa_threshold, (int, float))
                and float(current_gpa) < float(gpa_threshold)
            ):
                return {
                    "situation_type": "student_success_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "scholarship_award_risk_high",
                }
            if status == "at_risk" or risk_level == "medium":
                return {
                    "situation_type": "student_success_risk",
                    "severity": "medium",
                    "urgency": "medium",
                    "reasoning_path": "scholarship_award_risk_medium",
                }
            return {
                "situation_type": "student_success_risk",
                "severity": "medium",
                "urgency": "medium",
                "reasoning_path": "scholarship_award_risk_medium",
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

        if event_type in ("procurement.request_submitted", "procurement.approval_required"):
            payload = signal.get("payload", {})
            estimated_total = payload.get("estimated_total")
            priority = str(payload.get("priority") or "").lower()
            try:
                total_f = float(estimated_total) if estimated_total is not None else 0.0
            except (TypeError, ValueError):
                total_f = 0.0
            if total_f >= 50000.0 or priority in {"critical", "high"}:
                return {
                    "situation_type": "procurement_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "procurement_approval_high",
                }
            if total_f >= 10000.0 or priority == "medium":
                return {
                    "situation_type": "procurement_risk",
                    "severity": "medium",
                    "urgency": "medium",
                    "reasoning_path": "procurement_approval_medium",
                }
            return {
                "situation_type": "procurement_risk",
                "severity": "low",
                "urgency": "low",
                "reasoning_path": "procurement_approval_low",
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
            payload = signal.get("payload", {})
            subject = signal.get("subject", {})
            days_since_last_milestone = payload.get("days_since_last_milestone")
            thesis_id = payload.get("thesis_id") or signal.get("source_entity_id")
            student_id = payload.get("student_id") or subject.get("student_id")
            to_status = str(payload.get("to_status") or "").strip().lower()

            if not thesis_id or not student_id:
                return {
                    "situation_type": "academic_risk",
                    "severity": "low",
                    "urgency": "low",
                    "reasoning_path": "thesis_delay_low",
                }

            if to_status == "rejected":
                return {
                    "situation_type": "academic_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "thesis_delay_high",
                }

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
            # A-014.3: Dedicated attendance reasoning paths for recovery loop
            if isinstance(attendance_rate, (int, float)) and attendance_rate < 0.40:
                return {
                    "situation_type": "academic_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "attendance_risk_high",
                }
            if isinstance(attendance_rate, (int, float)) and attendance_rate < 0.60:
                return {
                    "situation_type": "academic_risk",
                    "severity": "medium",
                    "urgency": "medium",
                    "reasoning_path": "attendance_risk_medium",
                }

            # Grade-risk signals carry `risk_level` instead of `attendance_rate`
            risk_level_raw = str(payload.get("risk_level") or "").lower()
            if risk_level_raw == "high":
                return {
                    "situation_type": "academic_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "risk_high",
                }
            if risk_level_raw == "medium":
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

        # A-016.1 Academic Integrity Violation Detection Brain — deterministic severity
        _INTEGRITY_VIOLATION_EVENTS = {
            "academic_integrity.violation.detected",
            "academic_integrity.risk_detected",
            "plagiarism.similarity.high_detected",
            "exam.proctoring.violation_detected",
            "coursework.submission.suspicious_detected",
            "ai_plagiarism.risk_detected",
        }
        if event_type in _INTEGRITY_VIOLATION_EVENTS:
            payload = signal.get("payload", {})
            # Normalize similarity_score: accept 0-100 (percent) or 0.0-1.0 (ratio)
            raw_score = payload.get("similarity_score")
            similarity_pct: float | None = None
            if isinstance(raw_score, (int, float)):
                if raw_score <= 1.0:
                    similarity_pct = float(raw_score) * 100.0
                else:
                    similarity_pct = float(raw_score)
            risk_level = str(payload.get("risk_level") or "").strip().lower()
            confirmed = bool(payload.get("confirmed_violation", False))
            repeated = bool(payload.get("repeated_incident", False))
            proctoring_flags = payload.get("proctoring_flags") or []
            flag_count = len(proctoring_flags) if isinstance(proctoring_flags, (list, tuple, set)) else 0
            # CRITICAL: confirmed violation, similarity >= 90, severe flags, repeated
            if (
                confirmed
                or risk_level == "critical"
                or (similarity_pct is not None and similarity_pct >= 90.0)
                or repeated
                or flag_count >= 3
            ):
                return {
                    "situation_type": "academic_risk",
                    "severity": "critical",
                    "urgency": "critical",
                    "reasoning_path": "academic_integrity_violation_critical",
                }
            # HIGH: similarity >= 75, strong suspicious, multiple flags
            if (
                risk_level == "high"
                or (similarity_pct is not None and similarity_pct >= 75.0)
                or flag_count >= 2
            ):
                return {
                    "situation_type": "academic_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "academic_integrity_violation_high",
                }
            # MEDIUM: similarity >= 50, moderate suspicion, one flag
            if (
                risk_level == "medium"
                or (similarity_pct is not None and similarity_pct >= 50.0)
                or flag_count >= 1
            ):
                return {
                    "situation_type": "academic_risk",
                    "severity": "medium",
                    "urgency": "medium",
                    "reasoning_path": "academic_integrity_violation_medium",
                }
            # LOW: weak suspicion / warning only
            return {
                "situation_type": "academic_risk",
                "severity": "low",
                "urgency": "low",
                "reasoning_path": "academic_integrity_violation_low",
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
            if bool(payload.get("graduation_risk_detected")):
                issue_count = payload.get("issue_count")
                if isinstance(issue_count, int) and issue_count >= 3:
                    return {
                        "situation_type": "academic_risk",
                        "severity": "high",
                        "urgency": "high",
                        "reasoning_path": "graduation_risk_high",
                    }
                return {
                    "situation_type": "academic_risk",
                    "severity": "medium",
                    "urgency": "medium",
                    "reasoning_path": "graduation_risk_medium",
                }
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

        # A-015.4 — Finance Operations Health Brain
        if event_type in ("finance.operations.health_check", "finance.operations.risk_detected"):
            payload = signal.get("payload", {})
            risk_level = str(payload.get("risk_level") or payload.get("overall_risk_level") or "").strip().lower()
            overall_score = payload.get("overall_score")

            if risk_level in {"critical"} or (
                isinstance(overall_score, (int, float)) and float(overall_score) < 40
            ):
                return {
                    "situation_type": "financial_risk",
                    "severity": "critical",
                    "urgency": "high",
                    "reasoning_path": "finance_operations_health_critical",
                }
            if risk_level in {"high"} or (
                isinstance(overall_score, (int, float)) and float(overall_score) < 60
            ):
                return {
                    "situation_type": "financial_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "finance_operations_health_high",
                }
            if risk_level in {"medium"} or (
                isinstance(overall_score, (int, float)) and float(overall_score) < 75
            ):
                return {
                    "situation_type": "financial_risk",
                    "severity": "medium",
                    "urgency": "medium",
                    "reasoning_path": "finance_operations_health_medium",
                }
            return {
                "situation_type": "financial_risk",
                "severity": "low",
                "urgency": "low",
                "reasoning_path": "finance_operations_health_low",
            }

        if event_type in (
            "inventory.low_stock.detected",
            "inventory.reorder_needed",
            "supply.risk.detected",
            "procurement.inventory_gap.detected",
        ):
            payload = signal.get("payload", {})
            risk_level = str(payload.get("risk_level") or "").strip().lower()
            current_quantity = payload.get("current_quantity")
            reorder_threshold = payload.get("reorder_threshold")

            # Explicit risk_level in payload takes precedence
            if risk_level == "critical" or (
                isinstance(current_quantity, (int, float)) and float(current_quantity) <= 0
            ):
                return {
                    "situation_type": "supply_risk",
                    "severity": "critical",
                    "urgency": "critical",
                    "reasoning_path": "inventory_low_stock_critical",
                }
            if risk_level == "high" or (
                isinstance(current_quantity, (int, float))
                and isinstance(reorder_threshold, (int, float))
                and float(reorder_threshold) > 0
                and float(current_quantity) < float(reorder_threshold) * 0.5
            ):
                return {
                    "situation_type": "supply_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "inventory_low_stock_high",
                }
            if risk_level == "medium" or (
                isinstance(current_quantity, (int, float))
                and isinstance(reorder_threshold, (int, float))
                and float(current_quantity) < float(reorder_threshold)
            ):
                return {
                    "situation_type": "supply_risk",
                    "severity": "medium",
                    "urgency": "medium",
                    "reasoning_path": "inventory_low_stock_medium",
                }
            return {
                "situation_type": "supply_risk",
                "severity": "low",
                "urgency": "low",
                "reasoning_path": "inventory_low_stock_low",
            }

        # A-016.2 Thesis Governance + Supervisor Assignment — deterministic severity
        _THESIS_GOVERNANCE_EVENTS = frozenset({
            "thesis.submission.created",
            "thesis.submission.pending_review",
            "thesis.supervisor.assignment_needed",
            "thesis.supervisor.overloaded",
            "thesis.review.delayed",
            "thesis.governance.risk_detected",
        })
        if event_type in _THESIS_GOVERNANCE_EVENTS:
            payload = signal.get("payload", {})
            thesis_id = str(payload.get("thesis_id") or signal.get("source_entity_id") or "").strip()
            supervisor_id = str(payload.get("supervisor_id") or "").strip()
            risk_level = str(payload.get("risk_level") or "").strip().lower()
            days_without_supervisor = payload.get("days_without_supervisor")
            days_in_review = payload.get("days_in_review")
            supervisor_overloaded = bool(
                payload.get("supervisor_overloaded")
                or event_type == "thesis.supervisor.overloaded"
            )
            supervisor_load_pct = payload.get("supervisor_load_pct")
            thesis_status = str(payload.get("status") or "").strip().lower()

            if not thesis_id:
                return {
                    "situation_type": "academic_risk",
                    "severity": "low",
                    "urgency": "low",
                    "reasoning_path": "thesis_governance_low",
                }

            # Critical: explicit level, or no supervisor beyond critical threshold,
            # or severely overdue review
            if (
                risk_level == "critical"
                or (
                    not supervisor_id
                    and isinstance(days_without_supervisor, (int, float))
                    and float(days_without_supervisor) >= 30
                )
                or (isinstance(days_in_review, (int, float)) and float(days_in_review) >= 90)
            ):
                return {
                    "situation_type": "academic_risk",
                    "severity": "critical",
                    "urgency": "critical",
                    "reasoning_path": "thesis_governance_critical",
                }

            # High: explicit level, no supervisor beyond normal threshold,
            # rejected thesis, supervisor overloaded, or overdue review
            if (
                risk_level == "high"
                or (
                    not supervisor_id
                    and isinstance(days_without_supervisor, (int, float))
                    and float(days_without_supervisor) >= 14
                )
                or thesis_status == "rejected"
                or supervisor_overloaded
                or (isinstance(days_in_review, (int, float)) and float(days_in_review) >= 60)
            ):
                return {
                    "situation_type": "academic_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "thesis_governance_high",
                }

            # Medium: explicit level, supervisor missing (no days info),
            # review pending too long, or supervisor load warning
            if (
                risk_level == "medium"
                or not supervisor_id
                or (isinstance(days_in_review, (int, float)) and float(days_in_review) >= 30)
                or (isinstance(supervisor_load_pct, (int, float)) and float(supervisor_load_pct) >= 80)
            ):
                return {
                    "situation_type": "academic_risk",
                    "severity": "medium",
                    "urgency": "medium",
                    "reasoning_path": "thesis_governance_medium",
                }

            # Low (default — supervisor present, no escalation indicators)
            return {
                "situation_type": "academic_risk",
                "severity": "low",
                "urgency": "low",
                "reasoning_path": "thesis_governance_low",
            }

        # A-016.3 Exam Proctoring Violation Workflow — deterministic severity
        _EXAM_PROCTORING_EVENTS = {
            "faculty.proctoring.violation_detected",
            "exam.proctoring.suspicious_activity_detected",
            "exam.proctoring.multiple_faces_detected",
            "exam.proctoring.face_mismatch_detected",
            "exam.proctoring.forbidden_app_detected",
            "exam.proctoring.camera_absent_detected",
        }
        if event_type in _EXAM_PROCTORING_EVENTS:
            payload = signal.get("payload", {})
            violation_type = str(payload.get("violation_type") or event_type).strip().lower()
            risk_level = str(payload.get("risk_level") or "").strip().lower()
            confidence_score = payload.get("confidence_score")
            confidence: float | None = None
            if isinstance(confidence_score, (int, float)):
                confidence = float(confidence_score)
            manual_proctor_report = bool(payload.get("manual_proctor_report", False))
            flags = payload.get("flags") or []
            flag_count_raw = payload.get("flag_count")
            if isinstance(flag_count_raw, int):
                flag_count = flag_count_raw
            elif isinstance(flags, (list, tuple, set)):
                flag_count = len(flags)
            else:
                flag_count = 0

            # Severe violation types for threshold logic
            _SEVERE_TYPES = {"face_mismatch", "forbidden_app", "multiple_faces", "face_mismatch_detected", "forbidden_app_detected", "multiple_faces_detected"}
            is_severe_type = any(s in violation_type for s in ("face_mismatch", "forbidden_app", "multiple_faces"))
            is_face_mismatch = "face_mismatch" in violation_type or event_type == "exam.proctoring.face_mismatch_detected"
            is_forbidden_app = "forbidden_app" in violation_type or event_type == "exam.proctoring.forbidden_app_detected"
            is_multiple_faces = "multiple_faces" in violation_type or event_type == "exam.proctoring.multiple_faces_detected"
            is_camera_absent = "camera_absent" in violation_type or event_type == "exam.proctoring.camera_absent_detected"
            is_suspicious = "suspicious" in violation_type or event_type == "exam.proctoring.suspicious_activity_detected"

            # CRITICAL: manual proctor report, combined severe flags, repeated pattern,
            # face_mismatch AND forbidden_app together, or very high confidence with severe type
            if (
                manual_proctor_report
                or risk_level == "critical"
                or (is_face_mismatch and is_forbidden_app)
                or flag_count >= 4
                or (confidence is not None and confidence >= 0.95 and is_severe_type)
            ):
                return {
                    "situation_type": "academic_risk",
                    "severity": "critical",
                    "urgency": "critical",
                    "reasoning_path": "exam_proctoring_critical",
                }

            # HIGH: single severe flag type, flag_count >= 3, or strong confidence
            if (
                risk_level == "high"
                or is_forbidden_app
                or is_face_mismatch
                or is_multiple_faces
                or flag_count >= 3
                or (confidence is not None and confidence >= 0.80 and is_severe_type)
            ):
                return {
                    "situation_type": "academic_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "exam_proctoring_high",
                }

            # MEDIUM: camera absent, suspicious activity, 1–2 flags, moderate confidence
            if (
                risk_level == "medium"
                or is_camera_absent
                or is_suspicious
                or flag_count >= 1
                or (confidence is not None and confidence >= 0.50)
            ):
                return {
                    "situation_type": "academic_risk",
                    "severity": "medium",
                    "urgency": "medium",
                    "reasoning_path": "exam_proctoring_medium",
                }

            # LOW: weak warning / informational anomaly
            return {
                "situation_type": "academic_risk",
                "severity": "low",
                "urgency": "low",
                "reasoning_path": "exam_proctoring_low",
            }

        # A-016.4 Research Ethics / Compliance Review — deterministic severity
        _RESEARCH_ETHICS_COMPLIANCE_EVENTS = {
            "research_ethics.application.submitted",
            "research_ethics.review.overdue",
            "research_ethics.high_risk.detected",
            "research_ethics.missing_consent.detected",
            "research_ethics.document_missing.detected",
            "research_ethics.conflict_of_interest.detected",
            "research_ethics.violation.reported",
            "research.compliance.risk_detected",
            "research.data_privacy.risk_detected",
            "compliance.review.required",
        }
        if event_type in _RESEARCH_ETHICS_COMPLIANCE_EVENTS:
            payload = signal.get("payload", {})
            risk_level = str(payload.get("risk_level") or "").strip().lower()
            study_type = str(payload.get("study_type") or "").strip().lower()
            risk_category = str(payload.get("risk_category") or "").strip().lower()
            violation_confirmed = bool(payload.get("violation_confirmed") or payload.get("confirmed_violation"))
            consent_required = bool(payload.get("consent_required", False))
            consent_present = bool(payload.get("consent_present", False))
            data_privacy_risk = bool(payload.get("data_privacy_risk", False))
            conflict_of_interest = bool(payload.get("conflict_of_interest", False))
            conflict_confirmed = bool(payload.get("conflict_confirmed", False))

            documents_missing = payload.get("documents_missing")
            doc_count = 0
            if isinstance(documents_missing, (list, tuple, set)):
                doc_count = len(documents_missing)
            elif isinstance(documents_missing, str) and documents_missing.strip():
                doc_count = 1

            days_pending = payload.get("days_pending")
            overdue_days = 0
            if isinstance(days_pending, (int, float)):
                overdue_days = int(days_pending)

            is_human_subjects = study_type in {"human_subjects", "human_subject", "clinical", "clinical_trial"}
            has_missing_consent = (event_type == "research_ethics.missing_consent.detected") or (
                consent_required and not consent_present
            )
            severe_data_privacy = event_type == "research.data_privacy.risk_detected" and (
                data_privacy_risk or risk_level in {"high", "critical"}
            )
            high_risk_study = event_type == "research_ethics.high_risk.detected" or risk_level in {"high", "critical"}

            if (
                risk_level == "critical"
                or (event_type == "research_ethics.violation.reported" and violation_confirmed)
                or (is_human_subjects and has_missing_consent)
                or severe_data_privacy
                or (high_risk_study and doc_count >= 1)
                or overdue_days >= 60
                or (conflict_of_interest and conflict_confirmed)
            ):
                return {
                    "situation_type": "compliance_risk",
                    "severity": "critical",
                    "urgency": "critical",
                    "reasoning_path": "research_ethics_compliance_critical",
                }

            if (
                risk_level == "high"
                or event_type == "research_ethics.high_risk.detected"
                or has_missing_consent
                or doc_count >= 2
                or overdue_days >= 30
                or data_privacy_risk
                or event_type == "research.compliance.risk_detected"
            ):
                return {
                    "situation_type": "compliance_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "research_ethics_compliance_high",
                }

            if (
                risk_level == "medium"
                or event_type == "research_ethics.document_missing.detected"
                or doc_count == 1
                or overdue_days >= 7
                or event_type == "research_ethics.conflict_of_interest.detected"
                or conflict_of_interest
                or event_type == "compliance.review.required"
                or risk_category in {"committee_delay", "review_delay"}
            ):
                return {
                    "situation_type": "compliance_risk",
                    "severity": "medium",
                    "urgency": "medium",
                    "reasoning_path": "research_ethics_compliance_medium",
                }

            return {
                "situation_type": "compliance_risk",
                "severity": "low",
                "urgency": "low",
                "reasoning_path": "research_ethics_compliance_low",
            }

        # A-016.5 Academic Integrity Case Resolution Automation — deterministic severity
        if event_type in {
            "academic_integrity.case.opened",
            "academic_integrity.case.evidence_requested",
            "academic_integrity.case.review_required",
            "academic_integrity.case.resolved",
            "academic_integrity.case.dismissed",
            "integrity.resolution.workflow_needed",
        }:
            payload = signal.get("payload", {})
            risk_level = str(payload.get("risk_level") or "").strip().lower()
            days_open = payload.get("days_open")
            source_decision_type = str(payload.get("source_decision_type") or "").strip().lower()
            evidence_items = payload.get("evidence_items") or []
            evidence_missing = not evidence_items

            # CRITICAL: explicit critical risk OR long-overdue case
            if risk_level == "critical" or (
                isinstance(days_open, (int, float)) and float(days_open) >= 30
            ):
                return {
                    "situation_type": "academic_risk",
                    "severity": "critical",
                    "urgency": "critical",
                    "reasoning_path": "integrity_case_resolution_critical",
                }

            # HIGH: high risk level OR overdue >= 14 days OR high-risk source type
            # (source_decision_type only escalates when explicit risk_level is not provided)
            if risk_level == "high" or (
                isinstance(days_open, (int, float)) and float(days_open) >= 14
            ) or (
                not risk_level and source_decision_type in {
                    "academic_integrity_review",
                    "exam_integrity_review",
                    "research_ethics_review",
                }
            ):
                return {
                    "situation_type": "academic_risk",
                    "severity": "high",
                    "urgency": "high",
                    "reasoning_path": "integrity_case_resolution_high",
                }

            # MEDIUM: medium risk, open >= 1 day, or evidence missing
            # (evidence_missing only escalates when explicit risk_level is not provided)
            if risk_level == "medium" or (
                isinstance(days_open, (int, float)) and float(days_open) >= 1
            ) or (not risk_level and evidence_missing):
                return {
                    "situation_type": "academic_risk",
                    "severity": "medium",
                    "urgency": "medium",
                    "reasoning_path": "integrity_case_resolution_medium",
                }

            return {
                "situation_type": "academic_risk",
                "severity": "low",
                "urgency": "low",
                "reasoning_path": "integrity_case_resolution_low",
            }

        return {
            "situation_type": "operational_risk",
            "severity": "low",
            "urgency": "low",
            "reasoning_path": "default",
        }
