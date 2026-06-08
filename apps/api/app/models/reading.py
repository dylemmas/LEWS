"""Sensor reading model — corresponds to the TimescaleDB hypertable."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, SmallInteger
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SensorReading(Base):
    """A single decoded reading from a sensor node.

    The table is converted to a TimescaleDB hypertable in init.sql.
    The composite primary key (time, node_id) is what Timescale needs.
    """

    __tablename__ = "sensor_readings"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    node_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), primary_key=True
    )
    site_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    severity: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    sensor_mask: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    rain_tips_15m: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accel_rms_mg: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tilt_delta_ddeg: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    crack_delta_mm10: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    battery_mv: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ml_prob: Mapped[float | None] = mapped_column(Float)
    f_cnt: Mapped[int | None] = mapped_column(BigInteger)
    rssi: Mapped[int | None] = mapped_column(Integer)
    snr: Mapped[float | None] = mapped_column(Float)
    raw_payload_b64: Mapped[str | None] = mapped_column()
    extra: Mapped[dict | None] = mapped_column("metadata", JSONB)
