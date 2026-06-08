#!/usr/bin/env python3
"""
Demo seed script. Creates:
- 1 tenant (acme)
- 1 admin user (admin@acme.test / admin123)
- 5 sites around Bandung
- 5 nodes (one per site)
- 7 days of synthetic sensor readings
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import asyncpg
import numpy as np


async def main():
    import os
    conn = await asyncpg.connect(
        host=os.environ.get('PGHOST', 'localhost'),
        port=int(os.environ.get('PGPORT', '5432')),
        user=os.environ.get('PGUSER', 'lews'),
        password=os.environ.get('PGPASSWORD', 'lews_dev'),
        database=os.environ.get('PGDATABASE', 'lews'),
    )

    try:
        await seed(conn)
    finally:
        await conn.close()


async def seed(conn: asyncpg.Connection) -> None:
    tenant_id = uuid4()
    user_id = uuid4()

    # Tenant
    await conn.execute(
        """
        INSERT INTO tenants (id, slug, name, plan)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (slug) DO NOTHING
        """,
        tenant_id,
        'acme',
        'Acme Landslide Monitoring',
        'pro',
    )

    # Admin user
    from passlib.context import CryptContext
    pwd_ctx = CryptContext(schemes=['argon2'], deprecated='auto')
    pwd_hash = pwd_ctx.hash('admin123')

    await conn.execute(
        """
        INSERT INTO users (id, tenant_id, email, full_name, password_hash, role, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT DO NOTHING
        """,
        user_id,
        tenant_id,
        'admin@acme.test',
        'Admin User',
        pwd_hash,
        'admin',
        True,
    )

    # Sites around Bandung
    sites = [
        ('Cimenyan', -6.85, 107.65),
        ('Lembang', -6.82, 107.62),
        ('Pangalengan', -7.18, 107.55),
        ('Ciwidey', -7.15, 107.48),
        ('Cikalong', -6.92, 107.58),
    ]

    site_ids = []
    node_ids = []
    node_dev_euis = []

    for site_name, lat, lon in sites:
        site_id = uuid4()
        node_id = uuid4()
        dev_eui = f"01020304{len(site_ids):02x}"

        await conn.execute(
            """
            INSERT INTO sites (id, tenant_id, name, region, lat, lon)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            site_id,
            tenant_id,
            site_name,
            'Bandung',
            lat,
            lon,
        )

        await conn.execute(
            """
            INSERT INTO nodes (id, tenant_id, site_id, dev_eui, name, status, lat, lon)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            node_id,
            tenant_id,
            site_id,
            dev_eui,
            f"{site_name} Node 1",
            'online',
            lat,
            lon,
        )

        site_ids.append(site_id)
        node_ids.append(node_id)
        node_dev_euis.append(dev_eui)

    # Threshold rules
    await conn.execute(
        """
        INSERT INTO threshold_rules (tenant_id, site_id,
            rain_watch, rain_warning, rain_critical,
            accel_watch, accel_warning, accel_critical,
            tilt_watch, tilt_warning, tilt_critical,
            crack_watch, crack_warning, crack_critical)
        VALUES ($1, NULL,
            10.0, 25.0, 50.0,
            50.0, 100.0, 200.0,
            100.0, 250.0, 500.0,
            20.0, 60.0, 120.0)
        """,
        tenant_id,
    )

    # Generate 7 days of readings
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)

    readings = []

    for node_idx, node_id in enumerate(node_ids):
        # Node-specific baseline noise
        rain_base = random.uniform(0, 5)
        accel_base = random.uniform(10, 30)
        tilt_base = random.uniform(0, 50)
        crack_base = random.uniform(0, 20)

        ts = start
        while ts < now:
            # 15-min intervals
            rain = int(rain_base + random.exponential(2))
            accel = int(accel_base + random.exponential(10))
            tilt = int(tilt_base + random.uniform(-5, 10))
            crack = int(crack_base + random.uniform(-2, 5))
            battery = random.randint(3200, 4200)

            # Random severity (mostly normal)
            sev = 0
            if rain > 30 or accel > 100 or tilt > 200 or crack > 80:
                sev = random.choice([1, 2, 3])

            readings.append(
                (
                    ts,
                    tenant_id,
                    node_id,
                    site_ids[node_idx],
                    sev,
                    (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 5),  # sensor mask
                    rain,
                    accel,
                    tilt,
                    crack,
                    battery,
                    None,  # ml_prob
                )
            )

            ts += timedelta(minutes=15)

    # Bulk insert
    await conn.executemany(
        """
        INSERT INTO sensor_readings
        (time, tenant_id, node_id, site_id, severity, sensor_mask,
         rain_tips_15m, accel_rms_mg, tilt_delta_ddeg, crack_delta_mm10,
         battery_mv, ml_prob)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """,
        readings,
    )

    print(f"Seeded {len(readings)} readings across {len(node_ids)} nodes")


if __name__ == '__main__':
    asyncio.run(main())
