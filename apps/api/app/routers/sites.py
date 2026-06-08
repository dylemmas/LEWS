"""/v1/sites/* — site CRUD."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import CurrentUser, get_current_user, require_role
from app.models import Site
from app.schemas.node import SiteCreate, SiteDTO, SiteUpdate

router = APIRouter(prefix="/v1/sites", tags=["sites"])


@router.get("", response_model=list[SiteDTO])
async def list_sites(
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Site]:
    res = await db.execute(select(Site).where(Site.tenant_id == cu.tenant.id).order_by(Site.name))
    return list(res.scalars().all())


@router.post("", response_model=SiteDTO, status_code=201)
async def create_site(
    payload: SiteCreate,
    cu: CurrentUser = Depends(require_role("operator")),
    db: AsyncSession = Depends(get_db),
) -> Site:
    s = Site(
        tenant_id=cu.tenant.id,
        name=payload.name,
        region=payload.region,
        lat=payload.lat,
        lon=payload.lon,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


@router.get("/{site_id}", response_model=SiteDTO)
async def get_site(
    site_id: UUID,
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Site:
    s = await db.get(Site, site_id)
    if s is None or s.tenant_id != cu.tenant.id:
        raise HTTPException(status_code=404, detail="site not found")
    return s


@router.patch("/{site_id}", response_model=SiteDTO)
async def update_site(
    site_id: UUID,
    payload: SiteUpdate,
    cu: CurrentUser = Depends(require_role("operator")),
    db: AsyncSession = Depends(get_db),
) -> Site:
    s = await db.get(Site, site_id)
    if s is None or s.tenant_id != cu.tenant.id:
        raise HTTPException(status_code=404, detail="site not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    await db.commit()
    await db.refresh(s)
    return s


@router.delete("/{site_id}", status_code=204)
async def delete_site(
    site_id: UUID,
    cu: CurrentUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> None:
    s = await db.get(Site, site_id)
    if s is None or s.tenant_id != cu.tenant.id:
        raise HTTPException(status_code=404, detail="site not found")
    await db.delete(s)
    await db.commit()
