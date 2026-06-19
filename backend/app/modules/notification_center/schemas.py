from pydantic import BaseModel, Field


class NotificationCenterVisibilitySchema(BaseModel):
    tenant_id: int | None = Field(default=None)
    module: str
    visibility_level: str = Field(default="L4")
    operational_status: str
    classification: str
    allowed_actions: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    safety_flags: dict[str, bool | str] = Field(default_factory=dict)
    evidence_notes: list[str] = Field(default_factory=list)
    no_autonomous_execution: bool = True
    readonly: bool = True
    tenant_scoped: bool = True
    # D-07 consolidation (compatibility-first): this thin module is superseded by the
    # canonical communications notification center. Additive, non-breaking signal.
    deprecated: bool = True
    superseded_by: str = "/api/admin/communications/notifications/summary"
