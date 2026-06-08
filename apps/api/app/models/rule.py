"""Threshold rules model — per-tenant (optionally per-site) sensor thresholds."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ThresholdRule(Base):
    __tablename__ = "threshold_rules"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    site_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=True
    )
    rain_watch: Mapped[float] = mapped_column(Float, default=10.0)
    rain_warning: Mapped[float] = mapped_column(Float, default=25.0)
    rain_critical: Mapped[float] = mapped_column(Float, default=50.0)
    accel_watch: Mapped[float] = mapped_column(Float, default=50.0)
    accel_warning: Mapped[float] = mapped_column(Float, default=100.0)
    accel_critical: Mapped[float] = mapped_column(Float, default=200.0)
    tilt_watch: Mapped[float] = mapped_column(Float, default=100.0)
    tilt_warning: Mapped[float] = mapped_column(Float, default=250.0)
    tilt_critical: Mapped[float] = mapped_column(Float, default=500.0)
    crack_watch: Mapped[float] = mapped_column(Float, default=20.0)
    crack_warning: Mapped[float] = mapped_column(Float, default=60.0)
    crack_critical: Mapped[float] = mapped_column(Float, default=120.0)
    dedup_window_sec: Mapped[int] = mapped_column(Integer, default=300)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
