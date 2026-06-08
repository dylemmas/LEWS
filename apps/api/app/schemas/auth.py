"""Auth-related schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=200)
    tenant_slug: str = Field(..., min_length=2, max_length=40, pattern=r"^[a-z0-9-]+$")
    tenant_name: str = Field(..., min_length=2, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserDTO
    tenant: TenantDTO


class UserDTO(BaseModel):
    id: UUID
    tenant_id: UUID
    email: str
    full_name: str | None
    role: Literal["admin", "operator", "viewer"]
    phone_e164: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TenantDTO(BaseModel):
    id: UUID
    slug: str
    plan: Literal["free", "pro", "enterprise"]
    created_at: datetime

    model_config = {"from_attributes": True}
