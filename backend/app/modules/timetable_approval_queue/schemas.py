from pydantic import BaseModel, Field


class TimetableApprovalQueueVisibilitySchema(BaseModel):
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
