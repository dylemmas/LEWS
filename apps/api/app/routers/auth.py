"""/v1/auth/* — signup, login, refresh, logout, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.auth import AuthResponse, LoginRequest, RefreshRequest, SignupRequest, UserDTO, TenantDTO
from app.services.auth_service import login as svc_login, logout as svc_logout, refresh as svc_refresh, signup as svc_signup

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    return await svc_signup(db, payload)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    return await svc_login(db, payload)


@router.post("/refresh", response_model=AuthResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    return await svc_refresh(db, payload.refresh_token)


@router.post("/logout", status_code=204)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> None:
    await svc_logout(db, payload.refresh_token)
    return None


@router.get("/me")
async def me(cu: CurrentUser = Depends(get_current_user)) -> dict:
    return {
        "user": UserDTO.model_validate(cu.user).model_dump(mode="json"),
        "tenant": TenantDTO.model_validate(cu.tenant).model_dump(mode="json"),
    }
