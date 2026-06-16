"""Permission constants for Communications module (A-054 specification)."""

# Core Permission Slugs (19 total - all read-only in A-054.5-E1)
CORE_PERMISSIONS = [
    "communications.summary.read",               # 1. Overview dashboard access
    "communications.notifications.read",         # 2. Read notifications
    "communications.notifications.archive",      # 3. Archive notifications
    "communications.announcements.read",         # 4. Read announcements
    "communications.templates.read",             # 5. Read message templates
    "communications.preferences.read",           # 6. Read own preferences
    "communications.preferences.write_own",      # 7. Update own preferences
    "communications.audit.read",                 # 8. Read delivery audit
    "communications.audit.export",               # 9. Export audit data
    "communications.escalations.read",           # 10. Read escalations
    "communications.escalations.approve",        # 11. Approve escalation steps
    "communications.emergency.read",             # 12. Read emergency broadcast status
    "communications.emergency.test",             # 13. Test emergency broadcast
    "communications.recipients.read",            # 14. Query recipient groups
    "communications.campaigns.read",             # 15. Read campaigns
    "communications.providers.read",             # 16. Read provider readiness
    "communications.brain_actions.read",         # 17. Read Brain action proposals
    "communications.parent_communication.read",  # 18. Read parent-student threads
    "communications.moderation.review",          # 19. Review community messages
]

# Future-Gated Workflow Permissions (NOT active in A-054.5-E1)
FUTURE_GATED_WORKFLOW_PERMISSIONS = [
    "communications.notifications.send",         # FUTURE_GATED_WORKFLOW
    "communications.announcements.create",       # FUTURE_GATED_WORKFLOW
    "communications.announcements.update",       # FUTURE_GATED_WORKFLOW
    "communications.templates.create",           # FUTURE_GATED_WORKFLOW
    "communications.templates.update",           # FUTURE_GATED_WORKFLOW
    "communications.escalations.create",         # FUTURE_GATED_WORKFLOW
    "communications.emergency.activate",         # FUTURE_GATED_WORKFLOW
    "communications.campaigns.create",           # FUTURE_GATED_WORKFLOW
    "communications.campaigns.execute",          # FUTURE_GATED_WORKFLOW
    "communications.community.send",             # FUTURE_GATED_WORKFLOW
    "communications.moderation.approve",         # FUTURE_GATED_WORKFLOW
]


# Permission groupings for role assignment
STUDENT_PERMISSIONS = {
    "communications.notifications.read",
    "communications.announcements.read",
    "communications.preferences.read",
    "communications.preferences.write_own",
    "communications.parent_communication.read",
}

STAFF_PERMISSIONS = {
    "communications.notifications.read",
    "communications.announcements.read",
    "communications.preferences.read",
    "communications.preferences.write_own",
    "communications.parent_communication.read",
    "communications.audit.read",  # Limited to department
    "communications.moderation.review",
}

DIRECTOR_PERMISSIONS = {
    "communications.announcements.read",
    "communications.templates.read",
    "communications.preferences.read",
    "communications.audit.read",  # Department scope
    "communications.campaigns.read",
}

ADMIN_PERMISSIONS = set(CORE_PERMISSIONS)  # All core permissions

RECTOR_PERMISSIONS = {
    "communications.summary.read",
    "communications.announcements.read",
    "communications.audit.read",
    "communications.emergency.read",
    "communications.emergency.test",
    "communications.brain_actions.read",
}


def get_permissions_for_role(role: str) -> set[str]:
    """Get all permissions for a given role."""
    role_map = {
        "student": STUDENT_PERMISSIONS,
        "staff": STAFF_PERMISSIONS,
        "director": DIRECTOR_PERMISSIONS,
        "admin": ADMIN_PERMISSIONS,
        "rector": RECTOR_PERMISSIONS,
    }
    return role_map.get(role.lower(), set())
