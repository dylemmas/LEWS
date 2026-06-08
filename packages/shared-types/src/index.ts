// Public API for the @lews/shared-types package.

export * from './enums';
export * from './payload';
export * from './ws';

import type { AlertState, NodeStatus, Severity, UserRole } from './enums';

export interface TenantDTO {
  id: string;
  slug: string;
  plan: 'free' | 'pro' | 'enterprise';
  created_at: string;
}

export interface UserDTO {
  id: string;
  tenant_id: string;
  email: string;
  full_name: string | null;
  role: UserRole;
  phone_e164: string | null;
  created_at: string;
}

export interface SiteDTO {
  id: string;
  tenant_id: string;
  name: string;
  region: string | null;
  lat: number;
  lon: number;
  created_at: string;
}

export interface NodeDTO {
  id: string;
  tenant_id: string;
  site_id: string;
  dev_eui: string;
  name: string | null;
  status: NodeStatus;
  last_seen_at: string | null;
  battery_mv: number | null;
  lat: number;
  lon: number;
  hardware_version: string | null;
  firmware_version: string | null;
  created_at: string;
}

export interface ReadingDTO {
  time: string;
  tenant_id: string;
  node_id: string;
  site_id: string;
  severity: Severity;
  sensor_mask: number;
  rain_tips_15m: number;
  accel_rms_mg: number;
  tilt_delta_ddeg: number;
  crack_delta_mm10: number;
  battery_mv: number;
  ml_prob: number | null;
  lat: number;
  lon: number;
}

export interface AlertDTO {
  id: string;
  tenant_id: string;
  node_id: string;
  site_id: string;
  severity: Severity;
  state: AlertState;
  title: string;
  message: string;
  trigger_payload: Record<string, unknown> | null;
  first_seen_at: string;
  last_seen_at: string;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
  resolved_at: string | null;
  resolved_by: string | null;
  dismissed_at: string | null;
  dismissed_by: string | null;
  dismiss_reason: string | null;
  ml_prob: number | null;
  notification_log: NotificationLogEntry[];
}

export interface NotificationLogEntry {
  channel: 'sms' | 'email' | 'ws';
  target: string;
  sent_at: string;
  ok: boolean;
  error?: string;
}

export interface AuthSession {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;     // seconds
  user: UserDTO;
  tenant: TenantDTO;
}

export interface KPISummary {
  active_alerts: number;
  critical_alerts: number;
  warning_alerts: number;
  online_nodes: number;
  total_nodes: number;
  avg_battery_mv: number | null;
  rainfall_24h_mm: number;
  last_updated: string;
}

export interface IngestAck {
  ok: true;
  reading_id: string;
  severity: Severity;
  ml_prob: number | null;
  alert_id: string | null;
}

export interface IngestInjectRequest {
  node_id?: string;
  scenario: 'rain_burst' | 'tilt_spike' | 'crack_jump' | 'critical';
  duration_sec?: number;
}
