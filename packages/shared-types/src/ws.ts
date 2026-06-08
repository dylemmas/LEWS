// WebSocket event shapes — emitted from FastAPI Socket.IO to the dashboard.

import type { AlertState, NodeStatus, Severity, UserRole } from './enums';

export interface ReadingEvent {
  type: 'reading';
  tenant_id: string;
  node_id: string;
  site_id: string;
  time: string;          // ISO-8601
  severity: Severity;
  sensor_mask: number;
  rain_tips_15m: number;
  accel_rms_mg: number;
  tilt_delta_ddeg: number;
  crack_delta_mm10: number;
  battery_mv: number;
  ml_prob: number | null;
  lat: number;            // decimal degrees
  lon: number;
}

export interface AlertEvent {
  type: 'alert';
  tenant_id: string;
  alert_id: string;
  node_id: string;
  site_id: string;
  severity: Severity;
  state: AlertState;
  title: string;
  message: string;
  first_seen_at: string;
  last_seen_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  ml_prob: number | null;
}

export interface NodeStatusEvent {
  type: 'node_status';
  tenant_id: string;
  node_id: string;
  status: NodeStatus;
  last_seen_at: string | null;
  battery_mv: number | null;
}

export type SocketEvent = ReadingEvent | AlertEvent | NodeStatusEvent;

export type SocketEventName = 'reading' | 'alert' | 'node_status';
