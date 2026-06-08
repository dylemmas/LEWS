"""/v1/nodes/* — node CRUD."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import CurrentUser, get_current_user, require_role
from app.models import Node
from app.schemas.node import NodeCreate, NodeDTO, NodeUpdate

router = APIRouter(prefix="/v1/nodes", tags=["nodes"])


@router.get("", response_model=list[NodeDTO])
async def list_nodes(
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Node]:
    res = await db.execute(select(Node).where(Node.tenant_id == cu.tenant.id).order_by(Node.created_at))
    return list(res.scalars().all())


@router.post("", response_model=NodeDTO, status_code=201)
async def create_node(
    payload: NodeCreate,
    cu: CurrentUser = Depends(require_role("operator")),
    db: AsyncSession = Depends(get_db),
) -> Node:
    n = Node(
        tenant_id=cu.tenant.id,
        site_id=payload.site_id,
        dev_eui=payload.dev_eui,
        name=payload.name,
        lat=payload.lat,
        lon=payload.lon,
        hardware_version=payload.hardware_version,
        firmware_version=payload.firmware_version,
    )
    db.add(n)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=409, detail=f"dev_eui already exists: {e}") from None
    await db.refresh(n)
    return n


@router.get("/{node_id}", response_model=NodeDTO)
async def get_node(
    node_id: UUID,
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Node:
    n = await db.get(Node, node_id)
    if n is None or n.tenant_id != cu.tenant.id:
        raise HTTPException(status_code=404, detail="node not found")
    return n


@router.patch("/{node_id}", response_model=NodeDTO)
async def update_node(
    node_id: UUID,
    payload: NodeUpdate,
    cu: CurrentUser = Depends(require_role("operator")),
    db: AsyncSession = Depends(get_db),
) -> Node:
    n = await db.get(Node, node_id)
    if n is None or n.tenant_id != cu.tenant.id:
        raise HTTPException(status_code=404, detail="node not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(n, k, v)
    await db.commit()
    await db.refresh(n)
    return n


@router.delete("/{node_id}", status_code=204)
async def delete_node(
    node_id: UUID,
    cu: CurrentUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> None:
    n = await db.get(Node, node_id)
    if n is None or n.tenant_id != cu.tenant.id:
        raise HTTPException(status_code=404, detail="node not found")
    await db.delete(n)
    await db.commit()
