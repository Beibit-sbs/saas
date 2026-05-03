"""L.6 — Moodle LTI 1.3 adapter (stub)."""
from __future__ import annotations

import json
import time
import uuid

import httpx

MOODLE_BASE_URL = "https://moodle.university.edu"
DEFAULT_TIMEOUT = 10


class MoodleLtiError(Exception):
    pass


def launch(
    client_id: str,
    deployment_id: str,
    user_id: str,
    resource_link_id: str,
    *,
    roles: list[str] | None = None,
    launch_url: str | None = None,
) -> dict:
    """Build LTI 1.3 launch parameters. Returns launch data for the client to POST to Moodle."""
    if not client_id:
        raise ValueError("client_id is required")
    if not deployment_id:
        raise ValueError("deployment_id is required")
    if not user_id:
        raise ValueError("user_id is required")
    if not resource_link_id:
        raise ValueError("resource_link_id is required")

    nonce = str(uuid.uuid4())
    now = int(time.time())

    claims = {
        "iss": client_id,
        "sub": user_id,
        "aud": MOODLE_BASE_URL,
        "iat": now,
        "exp": now + 3600,
        "nonce": nonce,
        "https://purl.imsglobal.org/spec/lti/claim/deployment_id": deployment_id,
        "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
        "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
        "https://purl.imsglobal.org/spec/lti/claim/resource_link": {"id": resource_link_id},
        "https://purl.imsglobal.org/spec/lti/claim/roles": roles or [],
    }
    return {
        "launch_url": launch_url or f"{MOODLE_BASE_URL}/mod/lti/launch",
        "id_token": json.dumps(claims),  # stub: real impl would sign as JWT
        "nonce": nonce,
    }


def submit_grade(
    grade_passback_url: str,
    score: float,
    user_id: str,
    *,
    activity_progress: str = "Completed",
    grading_progress: str = "FullyGraded",
) -> bool:
    """Submit grade back to Moodle via AGS (Assignment and Grades Service)."""
    if not grade_passback_url:
        raise ValueError("grade_passback_url is required")
    if not (0.0 <= score <= 1.0):
        raise ValueError("score must be between 0.0 and 1.0")
    if not user_id:
        raise ValueError("user_id is required")

    payload = {
        "scoreOf": grade_passback_url,
        "userId": user_id,
        "scoreGiven": score,
        "activityProgress": activity_progress,
        "gradingProgress": grading_progress,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    try:
        resp = httpx.post(grade_passback_url, json=payload, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        return True
    except httpx.RequestError as exc:
        raise MoodleLtiError(f"Moodle submit_grade failed: {exc}") from exc


def deep_link_selection(content_items: list[dict]) -> str:
    """Build Deep Linking response JWT for selected content items. Returns JWT string (stub)."""
    if not isinstance(content_items, list):
        raise ValueError("content_items must be a list")

    payload = {
        "type": "LtiDeepLinkingResponse",
        "content_items": content_items,
        "timestamp": int(time.time()),
    }
    # Stub: real implementation would sign this as JWT with RS256
    return json.dumps(payload)
