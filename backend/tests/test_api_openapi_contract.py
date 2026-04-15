from __future__ import annotations

from collections import defaultdict

from app.main import app


def _openapi() -> dict[str, object]:
    return app.openapi()


def _operation(path: str, method: str) -> dict[str, object]:
    schema = _openapi()
    paths = schema.get("paths", {})
    assert path in paths, f"OpenAPI path {path!r} is missing"
    entry = paths[path]
    assert isinstance(entry, dict), f"OpenAPI path {path!r} is not a path item object"
    operation = entry.get(method.lower())
    assert isinstance(operation, dict), f"OpenAPI operation {method.upper()} {path} is missing"
    return operation


def _response_schema_ref(operation: dict[str, object], status_code: str) -> str:
    responses = operation.get("responses", {})
    assert isinstance(responses, dict), "OpenAPI responses block must be a dict"
    assert status_code in responses, f"Response {status_code} is not documented"
    response = responses[status_code]
    assert isinstance(response, dict), f"Response {status_code} must be an object"
    content = response.get("content", {})
    assert isinstance(content, dict) and "application/json" in content, (
        f"Response {status_code} must document application/json content"
    )
    media = content["application/json"]
    assert isinstance(media, dict), "OpenAPI media type must be an object"
    schema = media.get("schema", {})
    assert isinstance(schema, dict), "Response schema must be an object"
    ref = schema.get("$ref")
    assert isinstance(ref, str) and ref, f"Response {status_code} must use a component schema reference"
    return ref


def _response_schema(operation: dict[str, object], status_code: str) -> dict[str, object]:
    responses = operation.get("responses", {})
    assert isinstance(responses, dict), "OpenAPI responses block must be a dict"
    assert status_code in responses, f"Response {status_code} is not documented"
    response = responses[status_code]
    assert isinstance(response, dict), f"Response {status_code} must be an object"
    content = response.get("content", {})
    assert isinstance(content, dict) and "application/json" in content, (
        f"Response {status_code} must document application/json content"
    )
    media = content["application/json"]
    assert isinstance(media, dict), "OpenAPI media type must be an object"
    schema = media.get("schema", {})
    assert isinstance(schema, dict), "Response schema must be an object"
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref:
        return _resolve_schema(ref)
    return schema


def _resolve_schema(ref: str) -> dict[str, object]:
    prefix = "#/components/schemas/"
    assert ref.startswith(prefix), f"Unsupported schema ref: {ref}"
    schema_name = ref[len(prefix) :]
    schema = _openapi().get("components", {}).get("schemas", {}).get(schema_name)
    assert isinstance(schema, dict), f"Schema {schema_name!r} must be present in OpenAPI components"
    return schema


def test_auth_modes_openapi_contract_present_and_public() -> None:
    operation = _operation("/api/auth/modes", "get")
    assert operation.get("tags") == ["auth"]
    assert operation.get("security") in (None, []), "Public auth modes endpoint must not require auth in OpenAPI"
    responses = operation.get("responses", {})
    assert "200" in responses


def test_developer_latest_kpi_openapi_contract_stable() -> None:
    operation = _operation("/api/dev/analytics/kpis/latest", "get")
    assert operation.get("tags") == ["developer-api"]
    assert _response_schema_ref(operation, "200") == "#/components/schemas/TenantKpiSnapshotRead"
    responses = operation.get("responses", {})
    assert "401" in responses
    assert "403" in responses
    assert "429" in responses


def test_playbooks_list_openapi_contract_stable() -> None:
    operation = _operation("/api/admin/interventions/playbooks", "get")
    assert operation.get("tags") == ["interventions-playbooks"]
    assert _response_schema_ref(operation, "200") == "#/components/schemas/PlaybookListResponseSchema"
    params = operation.get("parameters", [])
    assert isinstance(params, list)
    param_names = {param.get("name") for param in params if isinstance(param, dict)}
    assert {"enabled_only", "offset", "limit"}.issubset(param_names)


def test_risk_student_latest_openapi_contract_stable() -> None:
    operation = _operation("/api/v1/risk/students/{student_profile_id}/latest", "get")
    assert operation.get("tags") == ["risk-v1"]
    assert _response_schema_ref(operation, "200") == "#/components/schemas/RiskStudentLatestSchema"
    assert _response_schema_ref(operation, "403") == "#/components/schemas/ErrorDetailResponse"
    assert _response_schema_ref(operation, "404") == "#/components/schemas/ErrorDetailResponse"
    params = operation.get("parameters", [])
    assert isinstance(params, list)
    path_param = next(
        (param for param in params if isinstance(param, dict) and param.get("name") == "student_profile_id"),
        None,
    )
    assert path_param is not None, "student_profile_id path parameter must be documented"
    assert path_param.get("in") == "path"
    assert path_param.get("required") is True


def test_tenants_list_openapi_contract_stable() -> None:
    operation = _operation("/api/admin/tenants", "get")
    assert operation.get("tags") == ["tenants"]
    assert _response_schema_ref(operation, "200") == "#/components/schemas/TenantListResponse"


def test_jobs_list_openapi_contract_stable() -> None:
    operation = _operation("/api/admin/jobs", "get")
    assert operation.get("tags") == ["jobs"]
    assert _response_schema_ref(operation, "200") == "#/components/schemas/JobListResponse"


def test_backup_settings_openapi_contract_present() -> None:
    operation = _operation("/api/admin/backups/settings", "get")
    assert operation.get("tags") == ["backups"]
    responses = operation.get("responses", {})
    assert isinstance(responses, dict) and "200" in responses


def test_backup_settings_update_exposes_idempotent_replay_flag() -> None:
    operation = _operation("/api/admin/backups/settings", "put")
    schema = _response_schema(operation, "200")
    props = schema.get("properties", {})
    assert isinstance(props, dict) and "idempotent_replay" in props
    assert props["idempotent_replay"].get("type") == "boolean"


def test_analytics_kpis_openapi_contract_stable() -> None:
    operation = _operation("/api/analytics/kpis", "get")
    assert operation.get("tags") == ["analytics-kpi"]
    assert _response_schema_ref(operation, "200") == "#/components/schemas/TenantAnalyticsKpiListReadSchema"


def test_identity_providers_openapi_contract_present() -> None:
    operation = _operation("/api/admin/identity/providers", "get")
    assert operation.get("tags") == ["identity-admin"]
    responses = operation.get("responses", {})
    assert isinstance(responses, dict) and "200" in responses


def test_identity_provider_upsert_exposes_idempotent_replay_flag() -> None:
    operation = _operation("/api/admin/identity/providers/{provider}", "put")
    schema = _response_schema(operation, "200")
    props = schema.get("properties", {})
    assert isinstance(props, dict) and "idempotent_replay" in props
    assert props["idempotent_replay"].get("type") == "boolean"
    provider_props = props.get("provider", {})
    assert isinstance(provider_props, dict)
    assert provider_props.get("type") == "object"


def test_integrations_mutation_responses_expose_idempotent_replay_flag() -> None:
    ldap_operation = _operation("/api/admin/integrations/ldap", "put")
    ldap_schema = _response_schema(ldap_operation, "200")
    ldap_props = ldap_schema.get("properties", {})
    assert isinstance(ldap_props, dict) and "idempotent_replay" in ldap_props
    assert ldap_props["idempotent_replay"].get("type") == "boolean"

    ai_operation = _operation("/api/admin/integrations/ai/{provider}", "put")
    ai_schema = _response_schema(ai_operation, "200")
    ai_props = ai_schema.get("properties", {})
    assert isinstance(ai_props, dict) and "idempotent_replay" in ai_props
    assert ai_props["idempotent_replay"].get("type") == "boolean"


def test_platform_billing_subscription_assign_exposes_idempotent_replay_flag() -> None:
    operation = _operation("/api/v1/admin/tenants/{tenant_id}/billing/subscription", "put")
    schema = _response_schema(operation, "200")
    properties = schema.get("properties", {})
    assert isinstance(properties, dict) and "idempotent_replay" in properties
    assert properties["idempotent_replay"].get("type") == "boolean"

    subscription = properties.get("subscription", {})
    assert isinstance(subscription, dict)
    assert subscription.get("$ref") == "#/components/schemas/SubscriptionRead"


def test_platform_billing_plan_create_exposes_idempotent_replay_flag() -> None:
    operation = _operation("/api/v1/admin/billing/plans", "post")
    schema = _response_schema(operation, "201")
    properties = schema.get("properties", {})
    assert isinstance(properties, dict) and "idempotent_replay" in properties
    assert properties["idempotent_replay"].get("type") == "boolean"

    plan = properties.get("plan", {})
    assert isinstance(plan, dict)
    assert plan.get("$ref") == "#/components/schemas/PlanRead"


def test_platform_tenant_create_exposes_idempotent_replay_flag() -> None:
    operation = _operation("/api/v1/admin/tenants", "post")
    schema = _response_schema(operation, "201")
    properties = schema.get("properties", {})
    assert isinstance(properties, dict) and "idempotent_replay" in properties
    assert properties["idempotent_replay"].get("type") == "boolean"
    assert properties.get("tenant_id", {}).get("type") == "integer"


def test_platform_notifications_dispatch_exposes_idempotent_replay_flag() -> None:
    operation = _operation("/api/v1/admin/notifications", "post")
    schema = _response_schema(operation, "201")
    properties = schema.get("properties", {})
    assert isinstance(properties, dict) and "idempotent_replay" in properties
    assert properties["idempotent_replay"].get("type") == "boolean"

    notification = properties.get("notification", {})
    assert isinstance(notification, dict)
    assert notification.get("$ref") == "#/components/schemas/NotificationRead"


def test_platform_webhook_subscription_create_exposes_idempotent_replay_flag() -> None:
    operation = _operation("/api/v1/admin/webhooks/subscriptions", "post")
    schema = _response_schema(operation, "201")
    properties = schema.get("properties", {})
    assert isinstance(properties, dict) and "idempotent_replay" in properties
    assert properties["idempotent_replay"].get("type") == "boolean"

    subscription = properties.get("subscription", {})
    assert isinstance(subscription, dict)
    assert subscription.get("$ref") == "#/components/schemas/WebhookSubscriptionReadSchema"


def test_platform_webhook_subscription_deactivate_exposes_idempotent_replay_flag() -> None:
    operation = _operation("/api/v1/admin/webhooks/subscriptions/{subscription_id}/deactivate", "post")
    schema = _response_schema(operation, "200")
    properties = schema.get("properties", {})
    assert isinstance(properties, dict) and "idempotent_replay" in properties
    assert properties["idempotent_replay"].get("type") == "boolean"

    subscription = properties.get("subscription", {})
    assert isinstance(subscription, dict)
    assert subscription.get("$ref") == "#/components/schemas/WebhookSubscriptionReadSchema"


def test_platform_feature_flag_mutations_expose_idempotent_replay_flag() -> None:
    platform_operation = _operation("/api/v1/admin/features/{module}/{key}", "put")
    platform_schema = _response_schema(platform_operation, "200")
    platform_props = platform_schema.get("properties", {})
    assert isinstance(platform_props, dict) and "idempotent_replay" in platform_props
    assert platform_props["idempotent_replay"].get("type") == "boolean"
    platform_flag = platform_props.get("flag", {})
    assert isinstance(platform_flag, dict)
    assert platform_flag.get("$ref") == "#/components/schemas/FeatureFlagRead"

    tenant_operation = _operation("/api/v1/admin/tenants/{tenant_id}/features/{module}/{key}", "put")
    tenant_schema = _response_schema(tenant_operation, "200")
    tenant_props = tenant_schema.get("properties", {})
    assert isinstance(tenant_props, dict) and "idempotent_replay" in tenant_props
    assert tenant_props["idempotent_replay"].get("type") == "boolean"
    tenant_flag = tenant_props.get("flag", {})
    assert isinstance(tenant_flag, dict)
    assert tenant_flag.get("$ref") == "#/components/schemas/FeatureFlagRead"


def test_platform_tenant_profile_mutations_expose_idempotent_replay_flag() -> None:
    for path, method in [
        ("/api/v1/admin/tenants/{tenant_id}/settings", "patch"),
        ("/api/v1/admin/tenants/{tenant_id}/quotas", "put"),
        ("/api/v1/admin/tenants/{tenant_id}/limits", "put"),
        ("/api/v1/admin/tenants/{tenant_id}/suspension", "post"),
    ]:
        operation = _operation(path, method)
        schema = _response_schema(operation, "200")
        props = schema.get("properties", {})
        assert isinstance(props, dict) and "idempotent_replay" in props, (
            f"idempotent_replay missing from {method.upper()} {path} response schema"
        )
        assert props["idempotent_replay"].get("type") == "boolean", (
            f"idempotent_replay must be boolean for {method.upper()} {path}"
        )
        tenant_ref = props.get("tenant", {})
        assert isinstance(tenant_ref, dict), f"'tenant' key missing from {path}"
        assert tenant_ref.get("$ref") == "#/components/schemas/TenantPlatformRead", (
            f"'tenant' must ref TenantPlatformRead for {path}"
        )


def test_platform_ai_risk_thresholds_exposes_idempotent_replay_flag() -> None:
    operation = _operation("/api/v1/admin/platform/ai/risk-thresholds", "put")
    schema = _response_schema(operation, "200")
    props = schema.get("properties", {})
    assert isinstance(props, dict) and "idempotent_replay" in props
    assert props["idempotent_replay"].get("type") == "boolean"
    thresholds_ref = props.get("thresholds", {})
    assert isinstance(thresholds_ref, dict)
    assert thresholds_ref.get("$ref") == "#/components/schemas/AcademicRiskThresholdsRead"


def test_platform_developer_mutations_expose_idempotent_replay_flag() -> None:
    installation_operation = _operation("/api/v1/admin/platform/developer/apps/{app_id}/installations", "post")
    installation_schema = _response_schema(installation_operation, "201")
    installation_props = installation_schema.get("properties", {})
    assert isinstance(installation_props, dict) and "idempotent_replay" in installation_props
    assert installation_props["idempotent_replay"].get("type") == "boolean"
    installation_ref = installation_props.get("installation", {})
    assert isinstance(installation_ref, dict)
    assert installation_ref.get("$ref") == "#/components/schemas/DeveloperAppInstallationReadSchema"

    subscription_operation = _operation("/api/v1/admin/platform/developer/apps/{app_id}/subscriptions", "post")
    subscription_schema = _response_schema(subscription_operation, "201")
    subscription_props = subscription_schema.get("properties", {})
    assert isinstance(subscription_props, dict) and "idempotent_replay" in subscription_props
    assert subscription_props["idempotent_replay"].get("type") == "boolean"
    subscription_ref = subscription_props.get("subscription", {})
    assert isinstance(subscription_ref, dict)
    assert subscription_ref.get("$ref") == "#/components/schemas/DeveloperAppEventSubscriptionReadSchema"


def test_platform_federation_tenant_link_exposes_idempotent_replay_flag() -> None:
    operation = _operation("/api/v1/admin/platform/federation/institutions/{institution_id}/tenants", "post")
    schema = _response_schema(operation, "201")
    props = schema.get("properties", {})
    assert isinstance(props, dict) and "idempotent_replay" in props
    assert props["idempotent_replay"].get("type") == "boolean"
    member_ref = props.get("member", {})
    assert isinstance(member_ref, dict)
    assert member_ref.get("$ref") == "#/components/schemas/FederationMemberReadSchema"


def test_platform_education_graph_mutations_expose_idempotent_replay_flag() -> None:
    skill_operation = _operation("/api/v1/admin/skills", "post")
    skill_schema = _response_schema(skill_operation, "201")
    skill_props = skill_schema.get("properties", {})
    assert isinstance(skill_props, dict) and "idempotent_replay" in skill_props
    assert skill_props["idempotent_replay"].get("type") == "boolean"
    skill_ref = skill_props.get("skill", {})
    assert isinstance(skill_ref, dict)
    assert skill_ref.get("$ref") == "#/components/schemas/SkillReadSchema"

    course_skill_operation = _operation("/api/v1/admin/course-skills", "post")
    course_skill_schema = _response_schema(course_skill_operation, "201")
    course_skill_props = course_skill_schema.get("properties", {})
    assert isinstance(course_skill_props, dict) and "idempotent_replay" in course_skill_props
    assert course_skill_props["idempotent_replay"].get("type") == "boolean"
    course_skill_ref = course_skill_props.get("course_skill", {})
    assert isinstance(course_skill_ref, dict)
    assert course_skill_ref.get("$ref") == "#/components/schemas/CourseSkillReadSchema"


def test_platform_federation_institution_create_exposes_idempotent_replay_flag() -> None:
    operation = _operation("/api/v1/admin/platform/federation/institutions", "post")
    schema = _response_schema(operation, "201")
    props = schema.get("properties", {})
    assert isinstance(props, dict) and "idempotent_replay" in props
    assert props["idempotent_replay"].get("type") == "boolean"
    institution_ref = props.get("institution", {})
    assert isinstance(institution_ref, dict)
    assert institution_ref.get("$ref") == "#/components/schemas/InstitutionReadSchema"


def test_openapi_operation_ids_are_unique() -> None:
    schema = _openapi()
    paths = schema.get("paths", {})
    assert isinstance(paths, dict)

    seen: dict[str, list[str]] = defaultdict(list)
    http_methods = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in http_methods or not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            assert isinstance(operation_id, str) and operation_id.strip(), (
                f"OpenAPI {method.upper()} {path} must define a non-empty operationId"
            )
            seen[operation_id].append(f"{method.upper()} {path}")

    duplicates = {operation_id: refs for operation_id, refs in seen.items() if len(refs) > 1}
    assert not duplicates, f"Duplicate OpenAPI operationId values found: {duplicates}"


def test_platform_automation_rule_create_exposes_idempotent_replay_flag() -> None:
    operation = _operation("/api/v1/admin/platform/automation/rules", "post")
    schema = _response_schema(operation, "201")
    properties = schema.get("properties", {})
    assert isinstance(properties, dict) and "idempotent_replay" in properties
    assert properties["idempotent_replay"].get("type") == "boolean"
    assert "id" in properties and "event_type" in properties


def test_platform_developer_app_create_exposes_idempotent_replay_flag() -> None:
    operation = _operation("/api/v1/admin/platform/developer/apps", "post")
    schema = _response_schema(operation, "201")
    properties = schema.get("properties", {})
    assert isinstance(properties, dict) and "idempotent_replay" in properties
    assert properties["idempotent_replay"].get("type") == "boolean"
    assert "id" in properties and "app_key" in properties


def test_platform_automation_template_instantiate_exposes_idempotent_replay_flag() -> None:
    operation = _operation("/api/v1/admin/platform/automation/templates/{template_key}/instantiate", "post")
    schema = _response_schema(operation, "201")
    properties = schema.get("properties", {})
    assert isinstance(properties, dict) and "idempotent_replay" in properties
    assert properties["idempotent_replay"].get("type") == "boolean"
    assert "id" in properties and "event_type" in properties


def test_rbac_assign_exposes_idempotent_replay_flag() -> None:
    """ERP-QA-26: POST /api/admin/rbac/assign must expose idempotent_replay boolean."""
    operation = _operation("/api/admin/rbac/assign", "post")
    schema = _response_schema(operation, "200")
    properties = schema.get("properties", {})
    assert isinstance(properties, dict) and "idempotent_replay" in properties
    assert properties["idempotent_replay"].get("type") == "boolean"
    assert "user_id" in properties and "roles" in properties


def test_rbac_roles_upsert_exposes_idempotent_replay_flag() -> None:
    """ERP-QA-27: POST /api/admin/rbac/roles must expose idempotent_replay boolean."""
    operation = _operation("/api/admin/rbac/roles", "post")
    schema = _response_schema(operation, "200")
    properties = schema.get("properties", {})
    assert isinstance(properties, dict) and "idempotent_replay" in properties
    assert properties["idempotent_replay"].get("type") == "boolean"
    assert "role" in properties


def test_service_account_create_exposes_idempotent_replay_flag() -> None:
    """ERP-QA-28: POST /api/admin/service-accounts must expose idempotent_replay boolean."""
    operation = _operation("/api/admin/service-accounts", "post")
    schema = _response_schema(operation, "200")
    properties = schema.get("properties", {})
    assert isinstance(properties, dict) and "idempotent_replay" in properties
    assert properties["idempotent_replay"].get("type") == "boolean"
    assert "account" in properties


def test_job_enqueue_exposes_idempotent_replay_flag() -> None:
    """ERP-QA-29: POST /api/admin/jobs must expose idempotent_replay boolean at top level."""
    operation = _operation("/api/admin/jobs", "post")
    schema = _response_schema(operation, "200")
    properties = schema.get("properties", {})
    assert isinstance(properties, dict) and "idempotent_replay" in properties, (
        f"idempotent_replay not found in POST /api/admin/jobs response properties: {list(properties.keys())}"
    )
    assert properties["idempotent_replay"].get("type") == "boolean"
    assert "job" in properties
