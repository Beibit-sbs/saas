from pydantic import BaseModel, Field


class FeatureFlagPayload(BaseModel):
    key: str = Field(min_length=3, max_length=128)
    enabled: bool
    description: str | None = Field(default=None, max_length=256)
    scope: str = Field(default="global", min_length=3, max_length=64)


class FeatureFlagPatchPayload(BaseModel):
    enabled: bool | None = None
    description: str | None = Field(default=None, max_length=256)
