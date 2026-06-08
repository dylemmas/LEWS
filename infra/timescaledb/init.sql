-- Landslide EWS — TimescaleDB initialization
-- Idempotent: safe to re-run on a fresh postgres data dir.

-- =========================================================================
-- Extensions
-- =========================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext";
CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- =========================================================================
-- Enums
-- =========================================================================
DO $$ BEGIN
    CREATE TYPE tenant_plan AS ENUM ('free', 'pro', 'enterprise');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('admin', 'operator', 'viewer');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE node_status AS ENUM ('online', 'offline', 'degraded', 'maintenance');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE alert_state AS ENUM ('open', 'acknowledged', 'resolved', 'dismissed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- =========================================================================
-- Tenants (root of the multi-tenant isolation tree)
-- =========================================================================
CREATE TABLE IF NOT EXISTS tenants (
    id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug        citext UNIQUE NOT NULL,
    name        text NOT NULL,
    plan        tenant_plan NOT NULL DEFAULT 'free',
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- =========================================================================
-- Users
-- =========================================================================
CREATE TABLE IF NOT EXISTS users (
    id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email           citext NOT NULL,
    password_hash   text NOT NULL,
    full_name       text,
    role            user_role NOT NULL DEFAULT 'viewer',
    phone_e164      text,
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, email)
);
CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  text UNIQUE NOT NULL,
    expires_at  timestamptz NOT NULL,
    revoked_at  timestamptz,
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_refresh_user ON refresh_tokens(user_id) WHERE revoked_at IS NULL;

-- =========================================================================
-- Sites and Nodes
-- =========================================================================
CREATE TABLE IF NOT EXISTS sites (
    id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id   uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name        text NOT NULL,
    region      text,
    lat         double precision NOT NULL,
    lon         double precision NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sites_tenant ON sites(tenant_id);

CREATE TABLE IF NOT EXISTS nodes (
    id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    site_id         uuid NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    dev_eui         citext UNIQUE NOT NULL,
    name            text NOT NULL,
    status          node_status NOT NULL DEFAULT 'offline',
    firmware        text,
    hardware        text,
    lat             double precision NOT NULL,
    lon             double precision NOT NULL,
    battery_mv      integer,
    last_seen_at    timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_nodes_tenant ON nodes(tenant_id);
CREATE INDEX IF NOT EXISTS idx_nodes_site ON nodes(site_id);
CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(tenant_id, status);

-- =========================================================================
-- Threshold rules (per-tenant with optional per-site override)
-- =========================================================================
CREATE TABLE IF NOT EXISTS threshold_rules (
    id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id           uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    site_id             uuid REFERENCES sites(id) ON DELETE CASCADE,
    rain_tips_warn      integer NOT NULL DEFAULT 30,
    rain_tips_crit      integer NOT NULL DEFAULT 50,
    accel_warn_mg       integer NOT NULL DEFAULT 120,
    accel_crit_mg       integer NOT NULL DEFAULT 200,
    tilt_warn_ddeg      integer NOT NULL DEFAULT 150,
    tilt_crit_ddeg      integer NOT NULL DEFAULT 300,
    crack_warn_mm10     integer NOT NULL DEFAULT 80,
    crack_crit_mm10     integer NOT NULL DEFAULT 150,
    ml_warn             double precision NOT NULL DEFAULT 0.30,
    ml_crit             double precision NOT NULL DEFAULT 0.70,
    dedup_window_sec    integer NOT NULL DEFAULT 300,
    updated_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, site_id)
);

-- =========================================================================
-- Sensor readings (hypertable — the hot path)
-- =========================================================================
CREATE TABLE IF NOT EXISTS sensor_readings (
    time                timestamptz NOT NULL,
    tenant_id           uuid NOT NULL,
    node_id             uuid NOT NULL,
    severity            smallint NOT NULL DEFAULT 0,
    sensor_mask         smallint NOT NULL DEFAULT 0,
    rain_tips_15m       integer NOT NULL DEFAULT 0,
    accel_rms_mg        integer NOT NULL DEFAULT 0,
    tilt_delta_ddeg     integer NOT NULL DEFAULT 0,
    crack_delta_mm10    integer NOT NULL DEFAULT 0,
    battery_mv          integer NOT NULL DEFAULT 0,
    lat                 integer NOT NULL DEFAULT 0,
    lon                 integer NOT NULL DEFAULT 0,
    ml_prob             double precision,
    f_cnt               integer,
    rssi                integer,
    snr                 double precision,
    raw_payload_b64     text NOT NULL
);

-- Convert to hypertable (idempotent)
SELECT create_hypertable(
    'sensor_readings', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_readings_node_time
    ON sensor_readings (node_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_readings_tenant_time
    ON sensor_readings (tenant_id, time DESC);

-- Retention: keep raw 365 days, then drop chunks
SELECT add_retention_policy(
    'sensor_readings',
    INTERVAL '365 days',
    if_not_exists => TRUE
);

-- =========================================================================
-- Continuous aggregate: 1h buckets (feeds dashboard charts fast)
-- =========================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_readings_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket(INTERVAL '1 hour', time) AS bucket,
    node_id,
    tenant_id,
    AVG(rain_tips_15m)::numeric(10,2)     AS avg_rain,
    MAX(rain_tips_15m)                    AS max_rain,
    AVG(accel_rms_mg)::numeric(10,2)      AS avg_accel,
    MAX(accel_rms_mg)                     AS max_accel,
    AVG(tilt_delta_ddeg)::numeric(10,2)   AS avg_tilt,
    MAX(tilt_delta_ddeg)                  AS max_tilt,
    AVG(crack_delta_mm10)::numeric(10,2)  AS avg_crack,
    MAX(crack_delta_mm10)                 AS max_crack,
    AVG(battery_mv)::numeric(10,2)        AS avg_battery,
    MIN(battery_mv)                       AS min_battery,
    MAX(severity)                         AS max_severity,
    COUNT(*)                              AS sample_count
FROM sensor_readings
GROUP BY bucket, node_id, tenant_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy(
    'sensor_readings_hourly',
    start_offset => INTERVAL '7 days',
    end_offset   => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- =========================================================================
-- Alerts
-- =========================================================================
CREATE TABLE IF NOT EXISTS alerts (
    id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id           uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    site_id             uuid REFERENCES sites(id) ON DELETE SET NULL,
    node_id             uuid NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    severity            smallint NOT NULL,
    state               alert_state NOT NULL DEFAULT 'open',
    dedup_key           text NOT NULL,
    title               text NOT NULL,
    description         text,
    trigger_payload     jsonb NOT NULL DEFAULT '{}'::jsonb,
    first_seen_at       timestamptz NOT NULL DEFAULT now(),
    last_seen_at        timestamptz NOT NULL DEFAULT now(),
    acknowledged_at     timestamptz,
    acknowledged_by     uuid REFERENCES users(id),
    resolved_at         timestamptz,
    resolved_by         uuid REFERENCES users(id),
    dismissed_at        timestamptz,
    dismissed_by        uuid REFERENCES users(id),
    dismiss_reason      text,
    notification_log    jsonb NOT NULL DEFAULT '[]'::jsonb
);

-- Partial unique index — "one open alert per dedup_key" enforced at the DB level
CREATE UNIQUE INDEX IF NOT EXISTS uq_alerts_open_dedup
    ON alerts (node_id, dedup_key)
    WHERE state IN ('open', 'acknowledged');

CREATE INDEX IF NOT EXISTS idx_alerts_tenant_state
    ON alerts (tenant_id, state, first_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_node_time
    ON alerts (node_id, first_seen_at DESC);

-- =========================================================================
-- Audit log
-- =========================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id          bigserial PRIMARY KEY,
    tenant_id   uuid REFERENCES tenants(id) ON DELETE CASCADE,
    actor_id    uuid REFERENCES users(id) ON DELETE SET NULL,
    action      text NOT NULL,
    resource    text,
    resource_id text,
    metadata    jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_tenant_time
    ON audit_log (tenant_id, created_at DESC);
