"""Tests for Automation Templates Engine v1."""

import pytest
from app.platform.automation.templates.models import AutomationTemplateModel
from app.platform.automation.templates.repository import AutomationTemplateRepository
from app.platform.automation.templates import service as template_service
from app.platform.automation.templates.seeds import get_seed_templates
from app.platform.uow import UnitOfWork
from app.platform.repository.db import transaction


class TestAutomationTemplateRepository:
    """Test AutomationTemplateRepository operations."""

    def test_create_template(self):
        """Test creating a new template."""
        repo = AutomationTemplateRepository()

        template = repo.create_template(
            template_key="test-template",
            title="Test Template",
            description="A test template",
            category="Testing",
            event_type="test.event",
            condition_json={"field": "value"},
            actions_json=[{"type": "send_notification"}],
            is_system_template=False,
        )

        assert template.template_key == "test-template"
        assert template.title == "Test Template"
        assert template.event_type == "test.event"
        assert template.is_system_template is False

    def test_get_template(self):
        """Test retrieving a template by key."""
        repo = AutomationTemplateRepository()

        repo.create_template(
            template_key="get-test",
            title="Get Test",
            description="Test getting templates",
            category="Testing",
            event_type="test.event",
            condition_json={},
            actions_json=[],
        )

        template = repo.get_template("get-test")
        assert template is not None
        assert template.template_key == "get-test"

    def test_get_template_not_found(self):
        """Test getting non-existent template returns None."""
        repo = AutomationTemplateRepository()
        template = repo.get_template("nonexistent")
        assert template is None

    def test_list_templates(self):
        """Test listing all templates."""
        repo = AutomationTemplateRepository()

        repo.create_template(
            template_key="template-1",
            title="Template 1",
            description="First",
            category="Testing",
            event_type="event.one",
            condition_json={},
            actions_json=[],
        )

        repo.create_template(
            template_key="template-2",
            title="Template 2",
            description="Second",
            category="Testing",
            event_type="event.two",
            condition_json={},
            actions_json=[],
        )

        templates = repo.list_templates()
        assert len(templates) >= 2
        assert any(t.template_key == "template-1" for t in templates)
        assert any(t.template_key == "template-2" for t in templates)

    def test_update_template(self):
        """Test updating a template."""
        repo = AutomationTemplateRepository()

        original = repo.create_template(
            template_key="update-test",
            title="Original Title",
            description="Original description",
            category="Testing",
            event_type="test.event",
            condition_json={},
            actions_json=[],
        )

        updated = repo.update_template(
            "update-test",
            title="Updated Title",
            description="Updated description",
        )

        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.description == "Updated description"
        assert updated.version == original.version + 1

    def test_delete_template(self):
        """Test deleting a template."""
        repo = AutomationTemplateRepository()

        repo.create_template(
            template_key="delete-test",
            title="Delete Test",
            description="Testing deletion",
            category="Testing",
            event_type="test.event",
            condition_json={},
            actions_json=[],
        )

        deleted = repo.delete_template("delete-test")
        assert deleted is True

        found = repo.get_template("delete-test")
        assert found is None

    def test_delete_nonexistent_template(self):
        """Test deleting non-existent template returns False."""
        repo = AutomationTemplateRepository()
        deleted = repo.delete_template("nonexistent")
        assert deleted is False


class TestAutomationTemplateService:
    """Test AutomationTemplateService operations."""

    def test_list_templates_service(self):
        """Test listing templates via service."""
        with UnitOfWork() as uow:
            uow.automation_template_repository.create_template(
                template_key="service-test-1",
                title="Service Test 1",
                description="Test",
                category="Testing",
                event_type="test.event",
                condition_json={},
                actions_json=[],
            )

            templates = template_service.list_templates(uow=uow)
            assert len(templates) > 0

    def test_instantiate_template_creates_rule(self):
        """Test that instantiate_template creates an automation rule."""
        with UnitOfWork() as uow:
            # Create a template
            template = uow.automation_template_repository.create_template(
                template_key="instantiate-test",
                title="Instantiate Test",
                description="Test instantiation",
                category="Testing",
                event_type="test.event",
                condition_json={"field": "test_value"},
                actions_json=[
                    {"type": "send_notification", "channel": "in_app", "template": "test"}
                ],
                conn=uow.conn,
            )

            # Instantiate it
            rule = template_service.instantiate_template(
                template_key="instantiate-test",
                tenant_id=1,
                uow=uow,
            )

            assert rule is not None
            assert rule.tenant_id == 1
            assert rule.event_type == template.event_type
            assert rule.condition_json == template.condition_json
            assert rule.actions_json == template.actions_json
            assert rule.name == template.title  # Uses template title as default name
            assert rule.description == template.description

    def test_instantiate_template_with_custom_name(self):
        """Test instantiating template with custom rule name."""
        with UnitOfWork() as uow:
            uow.automation_template_repository.create_template(
                template_key="custom-name-test",
                title="Original Title",
                description="Original description",
                category="Testing",
                event_type="test.event",
                condition_json={},
                actions_json=[],
                conn=uow.conn,
            )

            rule = template_service.instantiate_template(
                template_key="custom-name-test",
                tenant_id=1,
                rule_name="Custom Rule Name",
                rule_description="Custom description",
                uow=uow,
            )

            assert rule.name == "Custom Rule Name"
            assert rule.description == "Custom description"

    def test_instantiate_template_not_found(self):
        """Test instantiating non-existent template raises error."""
        with UnitOfWork() as uow:
            with pytest.raises(ValueError, match="Template not found"):
                template_service.instantiate_template(
                    template_key="nonexistent-template",
                    tenant_id=1,
                    uow=uow,
                )

    def test_instantiate_template_tenant_isolation(self):
        """Test that instantiated rules are isolated by tenant."""
        with UnitOfWork() as uow:
            uow.automation_template_repository.create_template(
                template_key="tenant-iso-test",
                title="Tenant Isolation Test",
                description="Test",
                category="Testing",
                event_type="test.event",
                condition_json={},
                actions_json=[],
                conn=uow.conn,
            )

            # Create rules for different tenants
            rule_t1 = template_service.instantiate_template(
                template_key="tenant-iso-test",
                tenant_id=1,
                uow=uow,
            )

            rule_t2 = template_service.instantiate_template(
                template_key="tenant-iso-test",
                tenant_id=2,
                uow=uow,
            )

            assert rule_t1.tenant_id == 1
            assert rule_t2.tenant_id == 2
            # Both should have same template values
            assert rule_t1.event_type == rule_t2.event_type
            assert rule_t1.condition_json == rule_t2.condition_json

    def test_instantiate_copies_actions_correctly(self):
        """Test that actions are correctly copied from template."""
        with UnitOfWork() as uow:
            actions = [
                {"type": "send_notification", "channel": "email", "template": "test_1"},
                {"type": "create_task", "job_type": "review", "max_retries": 3},
                {"type": "emit_event", "event_type": "custom", "aggregate_type": "entity"},
            ]

            uow.automation_template_repository.create_template(
                template_key="actions-copy-test",
                title="Actions Copy Test",
                description="Test",
                category="Testing",
                event_type="test.event",
                condition_json={},
                actions_json=actions,
                conn=uow.conn,
            )

            rule = template_service.instantiate_template(
                template_key="actions-copy-test",
                tenant_id=1,
                uow=uow,
            )

            assert len(rule.actions_json) == 3
            assert rule.actions_json[0]["type"] == "send_notification"
            assert rule.actions_json[1]["type"] == "create_task"
            assert rule.actions_json[2]["type"] == "emit_event"


class TestSeedTemplates:
    """Test seed templates."""

    def test_seed_templates_structure(self):
        """Test that seed templates have correct structure."""
        templates = get_seed_templates()

        assert len(templates) == 4
        for template in templates:
            assert "template_key" in template
            assert "title" in template
            assert "description" in template
            assert "category" in template
            assert "event_type" in template
            assert "condition_json" in template
            assert "actions_json" in template
            assert "is_system_template" in template
            assert template["is_system_template"] is True

    def test_seed_templates_have_unique_keys(self):
        """Test that seed templates have unique keys."""
        templates = get_seed_templates()
        keys = [t["template_key"] for t in templates]
        assert len(keys) == len(set(keys))

    def test_seed_templates_academic_risk_detection(self):
        """Test Academic Risk Detection template structure."""
        templates = get_seed_templates()
        template = next(t for t in templates if t["template_key"] == "academic-risk-detection")

        assert template["event_type"] == "grade.submitted"
        assert template["condition_json"]["field"] == "grade_points"
        assert template["condition_json"]["operator"] == "<"
        assert template["condition_json"]["value"] == 50
        assert len(template["actions_json"]) == 2
        assert template["actions_json"][0]["type"] == "send_notification"
        assert template["actions_json"][1]["type"] == "create_task"

    def test_seed_templates_enrollment_welcome(self):
        """Test enrollment welcome template has empty condition."""
        templates = get_seed_templates()
        template = next(t for t in templates if t["template_key"] == "enrollment-welcome")

        assert template["event_type"] == "enrollment.created"
        assert template["condition_json"] == {}  # Always match
        assert len(template["actions_json"]) == 1
        assert template["actions_json"][0]["type"] == "send_notification"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
