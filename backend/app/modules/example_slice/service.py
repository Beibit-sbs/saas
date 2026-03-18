from dataclasses import dataclass


@dataclass(frozen=True)
class ExampleReferenceItem:
    key: str
    title: str
    required_permission: str
    audit_action: str


# Example-only reference data for the template.
# This slice does not demonstrate migrations, persistence, or full CRUD yet.
_EXAMPLE_ITEMS: tuple[ExampleReferenceItem, ...] = (
    ExampleReferenceItem(
        key="example_rbac_guarded_read",
        title="RBAC-guarded read endpoint",
        required_permission="admin.dashboard.read",
        audit_action="example_slice.read",
    ),
    ExampleReferenceItem(
        key="example_audited_operation",
        title="Audited template operation",
        required_permission="admin.dashboard.read",
        audit_action="example_slice.read",
    ),
)


def list_reference_items() -> list[dict[str, str]]:
    return [
        {
            "key": item.key,
            "title": item.title,
            "required_permission": item.required_permission,
            "audit_action": item.audit_action,
        }
        for item in _EXAMPLE_ITEMS
    ]
