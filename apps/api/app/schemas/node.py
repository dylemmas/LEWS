"""Site and node schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


# --- Sites ---

class SiteCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    region: str | None = Field(None, max_length=120)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class SiteUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    region: str | None = Field(None, max_length=120)
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)


class SiteDTO(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    region: str | None
    lat: float
    lon: float
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Nodes ---

class NodeCreate(BaseModel):
    site_id: UUID
    dev_eui: str = Field(..., min_length=8, max_length=32)
    name: str | None = Field(None, max_length=200)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    hardware_version: str | None = Field(None, max_length=40)
    firmware_version: str | None = Field(None, max_length=40)


class NodeUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    status: Literal["online", "offline", "degraded", "maintenance"] | None = None


class NodeDTO(BaseModel):
    id: UUID
    tenant_id: UUID
    site_id: UUID
    dev_eui: str
    name: str | None
    status: Literal["online", "offline", "degraded", "maintenance"]
    last_seen_at: datetime | None
    battery_mv: int | None
    lat: float
    lon: float
    hardware_version: str | None
    firmware_version: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
