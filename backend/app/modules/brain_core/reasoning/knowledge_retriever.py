from __future__ import annotations

from typing import Any


class KnowledgeRetriever:
    """Returns compact guidance snippets for Brain Core reasoning flows."""

    _CATALOG: dict[str, list[dict[str, Any]]] = {
        "academic.attendance_risk.detected": [
            {
                "document_id": "playbook.student_attendance_outreach",
                "title": "Student Attendance Outreach Playbook",
                "excerpt": "Escalate advisor outreach when attendance drops below 60% and pair it with course-level follow-up.",
                "source_type": "playbook",
                "tags": ["attendance", "advisor", "retention"],
            }
        ],
        "thesis.status_changed": [
            {
                "document_id": "guide.thesis_milestone_recovery",
                "title": "Thesis Milestone Recovery Guide",
                "excerpt": "When milestones stall for more than 60 days, create a supervision checkpoint and confirm advisor capacity.",
                "source_type": "guidance",
                "tags": ["thesis", "supervision"],
            }
        ],
        "research.grant_pipeline.at_risk": [
            {
                "document_id": "playbook.grant_pipeline_triage",
                "title": "Grant Pipeline Triage Playbook",
                "excerpt": "Prioritize sponsor deadlines, delayed milestones, and ownership gaps before submitting remediation steps.",
                "source_type": "playbook",
                "tags": ["research", "grants", "risk"],
            }
        ],
        "operations.consumable_stock.low": [
            {
                "document_id": "policy.inventory_reorder_thresholds",
                "title": "Inventory Reorder Threshold Policy",
                "excerpt": "When projected stockout falls within lead time, open replenishment workflow and notify operations if auto reorder cannot complete.",
                "source_type": "policy",
                "tags": ["inventory", "reorder", "operations"],
            }
        ],
    }

    def retrieve(
        self,
        *,
        signal: dict[str, Any],
        classification: dict[str, Any],
    ) -> dict[str, Any]:
        event_type = str(signal.get("event_type") or "")
        items = [dict(item) for item in self._CATALOG.get(event_type, [])]
        return {
            "query": {
                "event_type": event_type,
                "situation_type": classification.get("situation_type"),
            },
            "items": items,
            "sources": [item["document_id"] for item in items],
            "retrieved": len(items),
        }