from __future__ import annotations


SEMANTIC_VERSION = "v1"


ENTITIES: dict[str, dict[str, object]] = {
    "student": {
        "description": "Student lifecycle performance and risk state",
        "grain": "student-within-tenant-period",
        "allowed_dimensions": ["time", "term", "program", "department", "cohort", "instructor"],
        "allowed_metrics": ["student.success_rate", "student.dropout_risk"],
    },
    "course": {
        "description": "Course-level academic outcomes",
        "grain": "course-within-tenant-period",
        "allowed_dimensions": ["time", "term", "program", "department", "instructor"],
        "allowed_metrics": ["course.pass_rate"],
    },
    "faculty": {
        "description": "Instructor and faculty workload view",
        "grain": "faculty-within-tenant-period",
        "allowed_dimensions": ["time", "term", "department", "program", "instructor"],
        "allowed_metrics": ["faculty.workload_index"],
    },
    "ops_health": {
        "description": "Tenant operational health and latency",
        "grain": "tenant-time-bucket",
        "allowed_dimensions": ["time", "term", "plan", "tenant"],
        "allowed_metrics": ["ops.latency_p95"],
    },
    "scorecard": {
        "description": "Decision scorecard over core KPI metrics",
        "grain": "tenant-scorecard-snapshot",
        "allowed_dimensions": ["time", "term", "program", "department"],
        "allowed_metrics": [
            "student.success_rate",
            "student.dropout_risk",
            "course.pass_rate",
            "faculty.workload_index",
            "ops.latency_p95",
        ],
    },
}


METRICS: dict[str, dict[str, object]] = {
    "student.success_rate": {
        "description": "Ratio of submitted grades to enrollments as success proxy",
        "source": "kpi.dashboard_snapshot",
        "aggregation": "ratio",
        "time_grains": ["day", "week", "month", "term"],
        "tenant_scope": "tenant",
        "entity": "student",
    },
    "student.dropout_risk": {
        "description": "Risk proxy based on failed jobs and notifications pressure",
        "source": "kpi.metric_snapshot",
        "aggregation": "derived_index",
        "time_grains": ["day", "week", "month", "term"],
        "tenant_scope": "tenant",
        "entity": "student",
    },
    "course.pass_rate": {
        "description": "Ratio of submitted grades to enrollments at course scope",
        "source": "kpi.dashboard_snapshot",
        "aggregation": "ratio",
        "time_grains": ["day", "week", "month", "term"],
        "tenant_scope": "tenant",
        "entity": "course",
    },
    "faculty.workload_index": {
        "description": "Workload proxy based on grades volume per student population",
        "source": "kpi.metric_snapshot",
        "aggregation": "derived_index",
        "time_grains": ["day", "week", "month", "term"],
        "tenant_scope": "tenant",
        "entity": "faculty",
    },
    "ops.latency_p95": {
        "description": "Observed p95 latency from platform metrics",
        "source": "ops.metrics_snapshot",
        "aggregation": "percentile",
        "time_grains": ["hour", "day"],
        "tenant_scope": "tenant",
        "entity": "ops_health",
    },
}


DIMENSIONS: dict[str, dict[str, object]] = {
    "time": {
        "description": "Time bucket and range filter",
        "allowed_entities": list(ENTITIES.keys()),
        "allowed_metrics": list(METRICS.keys()),
    },
    "program": {
        "description": "Academic program semantic filter",
        "allowed_entities": ["student", "course", "faculty", "scorecard"],
        "allowed_metrics": ["student.success_rate", "student.dropout_risk", "course.pass_rate", "faculty.workload_index"],
    },
    "department": {
        "description": "Department semantic filter",
        "allowed_entities": ["student", "course", "faculty", "scorecard"],
        "allowed_metrics": ["student.success_rate", "student.dropout_risk", "course.pass_rate", "faculty.workload_index"],
    },
    "term": {
        "description": "Academic term semantic filter",
        "allowed_entities": ["student", "course", "faculty", "ops_health", "scorecard"],
        "allowed_metrics": list(METRICS.keys()),
    },
    "course": {
        "description": "Course semantic filter",
        "allowed_entities": ["course", "scorecard"],
        "allowed_metrics": ["course.pass_rate"],
    },
    "instructor": {
        "description": "Instructor semantic filter",
        "allowed_entities": ["student", "course", "faculty", "scorecard"],
        "allowed_metrics": ["course.pass_rate", "faculty.workload_index", "student.success_rate"],
    },
    "cohort": {
        "description": "Cohort semantic filter",
        "allowed_entities": ["student", "scorecard"],
        "allowed_metrics": ["student.success_rate", "student.dropout_risk"],
    },
    "plan": {
        "description": "Tenant plan semantic filter",
        "allowed_entities": ["ops_health"],
        "allowed_metrics": ["ops.latency_p95"],
    },
    "tenant": {
        "description": "Tenant semantic filter for platform-authorized scope",
        "allowed_entities": ["ops_health"],
        "allowed_metrics": ["ops.latency_p95"],
    },
}


SUPPORTED_TIME_RANGES = {
    "last_24_hours",
    "last_7_days",
    "last_30_days",
    "last_12_months",
    "term_to_date",
}
