// Shared enums between frontend and backend (mirored in SQLAlchemy/Pydantic)

export enum TenantPlan {
  Free = 'free',
  Pro = 'pro',
  Enterprise = 'enterprise',
}

export enum UserRole {
  Admin = 'admin',
  Operator = 'operator',
  Viewer = 'viewer',
}

export enum NodeStatus {
  Online = 'online',
  Offline = 'offline',
  Degraded = 'degraded',
  Maintenance = 'maintenance',
}

export enum AlertState {
  Open = 'open',
  Acknowledged = 'acknowledged',
  Resolved = 'resolved',
  Dismissed = 'dismissed',
}

export enum Severity {
  Normal = 0,
  Watch = 1,
  Warning = 2,
  Critical = 3,
}

// Frontend convenience mapping
export const SEVERITY_COLORS: Record<Severity, { bg: string; text: string; border: string }> = {
  [Severity.Normal]: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20' },
  [Severity.Watch]: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/20' },
  [Severity.Warning]: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20' },
  [Severity.Critical]: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20' },
};

export const SEVERITY_LABELS: Record<Severity, string> = {
  [Severity.Normal]: 'Normal',
  [Severity.Watch]: 'Watch',
  [Severity.Warning]: 'Warning',
  [Severity.Critical]: 'Critical',
};
