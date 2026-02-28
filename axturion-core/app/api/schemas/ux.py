from __future__ import annotations

from datetime import datetime
from typing import Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


UXLayout = Literal["default", "compact", "dense"]
UXTheme = Literal["dark", "light", "defense"]


class UXModuleConfigSchema(BaseModel):
    # Preserve backwards-compatibility for per-module custom keys.
    model_config = ConfigDict(extra="allow")

    layout: Optional[UXLayout] = None
    theme: Optional[UXTheme] = None
    flags: Optional[Dict[str, bool]] = None


class UXModuleConfigWriteSchema(BaseModel):
    # WRITE endpoints must be governance-safe: reject unknown keys.
    model_config = ConfigDict(extra="forbid")

    layout: Optional[UXLayout] = None
    theme: Optional[UXTheme] = None
    flags: Optional[Dict[str, bool]] = None


class UXConfigResponse(BaseModel):
    module: str
    config: UXModuleConfigSchema


class UXConfigVersionItem(BaseModel):
    version: int
    audit_log_id: str
    created_at: datetime
    actor_id: str
    config: UXModuleConfigSchema
    is_active: bool
    diff: "UXConfigDiff | None" = None


class UXFieldDiff(BaseModel):
    from_: str | None = Field(None, alias="from")
    to: str | None = None


class UXFlagChanged(BaseModel):
    key: str
    from_: bool = Field(..., alias="from")
    to: bool


class UXConfigDiff(BaseModel):
    layout: Optional[UXFieldDiff] = None
    theme: Optional[UXFieldDiff] = None
    flags_added: Optional[list[str]] = None
    flags_removed: Optional[list[str]] = None
    flags_changed: Optional[list[UXFlagChanged]] = None


class UXConfigRollbackRequest(BaseModel):
    version: int = Field(..., ge=1)
