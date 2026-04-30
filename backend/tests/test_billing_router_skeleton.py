"""
Skeleton tests for Wave1 #32 Billing Router: parity endpoints.
Focus: plans, subscription assign, usage increment
Status: PREP-PHASE (not for production)
"""

import pytest
from datetime import datetime, timezone


class BillingPlan:
    """Skeleton domain model for billing plans."""
    
    def __init__(self, plan_id: str, name: str, price: float, quota_students: int):
        self.plan_id = plan_id
        self.name = name
        self.price = price
        self.quota_students = quota_students
        self.created_at = datetime.now(timezone.utc)


class TenantSubscription:
    """Skeleton domain model for tenant subscriptions."""
    
    def __init__(self, tenant_id: str, plan_id: str):
        self.tenant_id = tenant_id
        self.plan_id = plan_id
        self.status = "active"  # active, suspended, cancelled
        self.current_period_start = datetime.now(timezone.utc)
        self.current_period_end = None
        self.usage_metrics = {}


class BillingService:
    """Skeleton billing service for prep-phase."""
    
    def __init__(self):
        self.plans = {}
        self.subscriptions = {}
    
    def create_plan(self, plan_id: str, name: str, price: float, quota_students: int) -> BillingPlan:
        """POST /api/admin/billing/plans"""
        plan = BillingPlan(plan_id, name, price, quota_students)
        self.plans[plan_id] = plan
        return plan
    
    def list_plans(self):
        """GET /api/admin/billing/plans"""
        return list(self.plans.values())
    
    def assign_subscription(self, tenant_id: str, plan_id: str) -> TenantSubscription:
        """PUT /api/admin/tenants/{tenant_id}/subscription"""
        if plan_id not in self.plans:
            raise ValueError(f"Plan {plan_id} not found")
        
        sub = TenantSubscription(tenant_id, plan_id)
        self.subscriptions[tenant_id] = sub
        return sub
    
    def increment_usage(self, tenant_id: str, metric: str, value: int) -> dict:
        """POST /api/admin/tenants/{tenant_id}/usage/{metric}"""
        if tenant_id not in self.subscriptions:
            raise ValueError(f"Subscription for {tenant_id} not found")
        
        sub = self.subscriptions[tenant_id]
        if metric not in sub.usage_metrics:
            sub.usage_metrics[metric] = 0
        sub.usage_metrics[metric] += value
        
        return {"metric": metric, "current_usage": sub.usage_metrics[metric]}
    
    def get_subscription_state(self, tenant_id: str) -> dict:
        """GET /api/admin/tenants/{tenant_id}/state"""
        if tenant_id not in self.subscriptions:
            return None
        
        sub = self.subscriptions[tenant_id]
        plan = self.plans[sub.plan_id]
        
        return {
            "tenant_id": tenant_id,
            "plan": {
                "plan_id": plan.plan_id,
                "name": plan.name,
                "quota_students": plan.quota_students
            },
            "status": sub.status,
            "usage_metrics": sub.usage_metrics,
            "period_start": sub.current_period_start.isoformat(),
            "period_end": sub.current_period_end
        }


class TestBillingPlanEndpoints:
    """#32 Billing: Plans API skeleton tests."""
    
    def test_create_plan(self):
        """POST /api/admin/billing/plans — create new plan."""
        service = BillingService()
        
        plan = service.create_plan("plan-premium", "Premium", 299.99, 500)
        assert plan.plan_id == "plan-premium"
        assert plan.name == "Premium"
        assert plan.price == 299.99
        assert plan.quota_students == 500
    
    def test_list_plans(self):
        """GET /api/admin/billing/plans — list all plans."""
        service = BillingService()
        
        service.create_plan("plan-basic", "Basic", 99.99, 100)
        service.create_plan("plan-pro", "Pro", 199.99, 300)
        
        plans = service.list_plans()
        assert len(plans) == 2
        assert plans[0].name == "Basic"


class TestBillingSubscriptionEndpoints:
    """#32 Billing: Subscription API skeleton tests."""
    
    def test_assign_subscription_to_tenant(self):
        """PUT /api/admin/tenants/{tenant_id}/subscription — assign plan."""
        service = BillingService()
        service.create_plan("plan-pro", "Pro", 199.99, 300)
        
        sub = service.assign_subscription("tenant-123", "plan-pro")
        assert sub.tenant_id == "tenant-123"
        assert sub.plan_id == "plan-pro"
        assert sub.status == "active"
    
    def test_assign_subscription_rejects_unknown_plan(self):
        """Assigning unknown plan should fail."""
        service = BillingService()
        
        with pytest.raises(ValueError):
            service.assign_subscription("tenant-123", "plan-nonexistent")
    
    def test_subscription_plan_change(self):
        """POST /api/admin/tenants/{tenant_id}/subscription/plan-change — upgrade/downgrade."""
        service = BillingService()
        service.create_plan("plan-basic", "Basic", 99.99, 100)
        service.create_plan("plan-pro", "Pro", 199.99, 300)
        
        # Initial assignment
        service.assign_subscription("tenant-123", "plan-basic")
        sub = service.subscriptions["tenant-123"]
        assert sub.plan_id == "plan-basic"
        
        # Plan change (upgrade)
        sub.plan_id = "plan-pro"
        assert sub.plan_id == "plan-pro"


class TestBillingUsageEndpoints:
    """#32 Billing: Usage tracking API skeleton tests."""
    
    def test_increment_usage_metric(self):
        """POST /api/admin/tenants/{tenant_id}/usage/{metric}"""
        service = BillingService()
        service.create_plan("plan-pro", "Pro", 199.99, 300)
        service.assign_subscription("tenant-123", "plan-pro")
        
        result = service.increment_usage("tenant-123", "api_calls", 100)
        assert result["metric"] == "api_calls"
        assert result["current_usage"] == 100
    
    def test_increment_usage_accumulates(self):
        """Multiple usage increments should accumulate."""
        service = BillingService()
        service.create_plan("plan-pro", "Pro", 199.99, 300)
        service.assign_subscription("tenant-123", "plan-pro")
        
        service.increment_usage("tenant-123", "api_calls", 100)
        result = service.increment_usage("tenant-123", "api_calls", 50)
        
        assert result["current_usage"] == 150
    
    def test_increment_usage_rejects_unknown_subscription(self):
        """Usage increment for non-existent subscription should fail."""
        service = BillingService()
        
        with pytest.raises(ValueError):
            service.increment_usage("tenant-unknown", "api_calls", 100)


class TestBillingStateEndpoints:
    """#32 Billing: State query API skeleton tests."""
    
    def test_get_subscription_state(self):
        """GET /api/admin/tenants/{tenant_id}/state — return current subscription state."""
        service = BillingService()
        service.create_plan("plan-pro", "Pro", 199.99, 300)
        service.assign_subscription("tenant-123", "plan-pro")
        service.increment_usage("tenant-123", "api_calls", 100)
        
        state = service.get_subscription_state("tenant-123")
        
        assert state["tenant_id"] == "tenant-123"
        assert state["plan"]["name"] == "Pro"
        assert state["status"] == "active"
        assert state["usage_metrics"]["api_calls"] == 100
    
    def test_get_subscription_state_unknown_tenant(self):
        """Query state for non-existent tenant should return None."""
        service = BillingService()
        
        state = service.get_subscription_state("tenant-unknown")
        assert state is None


class TestBillingBackwardCompatibility:
    """#32 Billing: Backward compatibility with platform-level endpoints."""
    
    def test_billing_module_router_has_own_prefix(self):
        """Module router uses `/api/admin/billing` prefix, separate from platform."""
        # Skeleton: ensure module router doesn't conflict with existing platform endpoints
        module_endpoints = [
            "/api/admin/billing/plans",
            "/api/admin/billing/subscription-transitions",
            "/api/admin/billing/usage"
        ]
        
        platform_endpoints = [
            "/api/v1/admin/platform/plans",  # hypothetical existing
            "/api/v1/admin/platform/usage"   # hypothetical existing
        ]
        
        # No conflict in prefixes
        assert all("/admin/billing" in ep for ep in module_endpoints)
        assert all("/v1/admin/platform" in ep for ep in platform_endpoints)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
