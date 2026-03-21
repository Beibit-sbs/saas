from app.modules.platform_shared.files import make_tenant_file_key, validate_file_key
from app.modules.platform_shared.notifications import InMemoryNotificationService, NotificationMessage
from app.modules.platform_shared.search import InMemorySearchService, SearchDocument, SearchQuery
from app.modules.platform_shared.webhooks import sign_webhook_payload, verify_webhook_signature
from app.modules.platform_shared.workflow import WorkflowDefinition, can_transition


def test_file_key_validation_rejects_path_traversal() -> None:
    try:
        validate_file_key("tenant/1/uploads/../secret.txt")
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "path traversal" in str(exc)


def test_make_tenant_file_key_generates_safe_scoped_path() -> None:
    key = make_tenant_file_key(tenant_id=7, namespace="student-docs", filename="passport.pdf")
    assert key == "tenant/7/student-docs/passport.pdf"


def test_notification_contract_requires_tenant_scope() -> None:
    service = InMemoryNotificationService()
    message = NotificationMessage(
        tenant_id=3,
        channel="in_app",
        recipient="user-1",
        subject="Workflow",
        body="Approved",
    )
    result = service.send(message)
    assert result["status"] == "queued"


def test_search_contract_is_tenant_scoped() -> None:
    service = InMemorySearchService()
    service.index(
        SearchDocument(
            tenant_id=1,
            module="students",
            entity="student",
            entity_id="st-1",
            title="Alice",
            content="Enrollment record",
        )
    )
    service.index(
        SearchDocument(
            tenant_id=2,
            module="students",
            entity="student",
            entity_id="st-2",
            title="Bob",
            content="Enrollment record",
        )
    )

    rows = service.search(SearchQuery(tenant_id=1, text="alice"))
    assert len(rows) == 1
    assert rows[0].entity_id == "st-1"


def test_workflow_transition_contract() -> None:
    definition = WorkflowDefinition(
        tenant_id=1,
        key="admission",
        initial_state="submitted",
        transitions={"submitted": ["review"], "review": ["approved", "rejected"]},
    )
    assert can_transition(definition, current_state="submitted", next_state="review") is True
    assert can_transition(definition, current_state="submitted", next_state="approved") is False


def test_webhook_sign_and_verify() -> None:
    payload = {"event": "student.created", "tenant_id": 1}
    header = sign_webhook_payload(secret="s3cr3t", payload=payload, timestamp=1700000000)
    assert verify_webhook_signature(
        secret="s3cr3t",
        payload=payload,
        header_value=header,
        tolerance_seconds=999999999,
    ) is True
    assert verify_webhook_signature(
        secret="wrong",
        payload=payload,
        header_value=header,
        tolerance_seconds=999999999,
    ) is False
