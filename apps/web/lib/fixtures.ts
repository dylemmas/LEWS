// Synthetic demo data for the offline dashboard.
// Deterministic — uses a seeded LCG so values don't shift on hot reload.

import {
  AlertState,
  NodeStatus,
  SEVERITY_LABELS,
  Severity,
  type AlertDTO,
  type KPISummary,
  type NodeDTO,
  type ReadingDTO,
  type SiteDTO,
  type TenantDTO,
  type UserDTO,
} from '@lews/shared-types';

// ---- Seeded RNG (mulberry32) -----------------------------------------------
function lcg(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---- Tenant + user ---------------------------------------------------------
export const TENANT: TenantDTO = {
  id: 't_acme',
  slug: 'acme',
  plan: 'enterprise',
  created_at: '2026-01-15T00:00:00Z',
};

export const CURRENT_USER: UserDTO = {
  id: 'u_admin',
  tenant_id: TENANT.id,
  email: 'admin@acme.test',
  full_name: 'Demo Admin',
  role: 'admin' as UserDTO['role'],
  phone_e164: null,
  created_at: '2026-01-15T00:00:00Z',
};

// ---- Sites -----------------------------------------------------------------
// 5 sites around Bandung, West Java (where the system's first deployment is)
const SITE_DEFS = [
  { name: 'Cimenyan',   lat: -7.0419, lon: 107.5722 },
  { name: 'Lembang',    lat: -6.8117, lon: 107.6225 },
  { name: 'Pangalengan', lat: -7.1633, lon: 107.5911 },
  { name: 'Ciwidey',    lat: -7.1397, lon: 107.4547 },
  { name: 'Cikalong',   lat: -6.9578, lon: 107.5289 },
];

export const SITES: SiteDTO[] = SITE_DEFS.map((s, i) => ({
  id: `s_${i + 1}`,
  tenant_id: TENANT.id,
  name: s.name,
  region: 'Bandung',
  lat: s.lat,
  lon: s.lon,
  created_at: '2026-01-20T00:00:00Z',
}));

// ---- Nodes -----------------------------------------------------------------
// 3 nodes per site. Spread each node ~0.5-1 km around its site centre.
const NODES_PER_SITE = 3;
const NODE_NAMES = ['Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo', 'Foxtrot', 'Golf', 'Hotel', 'India', 'Juliet', 'Kilo', 'Lima', 'Mike', 'November', 'Oscar'];

function makeNodes(): NodeDTO[] {
  const rand = lcg(42);
  const out: NodeDTO[] = [];
  let i = 0;
  for (const site of SITES) {
    for (let n = 0; n < NODES_PER_SITE; n++) {
      const dLat = (rand() - 0.5) * 0.015;
      const dLon = (rand() - 0.5) * 0.015;
      // status mix: ~14 online, 1 stale (last one is degraded for variety)
      let status: NodeDTO['status'] = NodeStatus.Online;
      if (i === 14) status = NodeStatus.Degraded;
      const batteryMv = 3600 + Math.floor(rand() * 600); // 3.6V - 4.2V
      const hoursAgo = i === 14 ? 6 : Math.floor(rand() * 30); // minutes
      const lastSeen = new Date(Date.now() - hoursAgo * 60_000).toISOString();
      out.push({
        id: `n_${i + 1}`,
        tenant_id: TENANT.id,
        site_id: site.id,
        dev_eui: (0xAC10_0000 + i).toString(16).toUpperCase().padStart(16, '0'),
        name: NODE_NAMES[i],
        status,
        last_seen_at: lastSeen,
        battery_mv: batteryMv,
        lat: site.lat + dLat,
        lon: site.lon + dLon,
        hardware_version: 'v1.2',
        firmware_version: '0.4.1',
        created_at: '2026-01-22T00:00:00Z',
      });
      i++;
    }
  }
  return out;
}

export const NODES: NodeDTO[] = makeNodes();

// ---- Severity per node (for colouring on the map) --------------------------
// 3 red, 5 yellow, 7 green
const NODE_SEVERITY: Severity[] = [
  Severity.Critical, Severity.Critical, Severity.Critical,                       // 3
  Severity.Warning, Severity.Warning, Severity.Warning, Severity.Warning, Severity.Warning, // 5
  Severity.Normal, Severity.Normal, Severity.Normal, Severity.Normal,            // 4
  Severity.Normal, Severity.Normal, Severity.Normal,                             // 3 → 15 total
];
export const NODE_SEVERITIES = NODE_SEVERITY;

// ---- 24h of synthetic readings per node ------------------------------------
// One reading every 15 min → 96 readings per node × 15 nodes = 1440 total.
const READINGS_PER_NODE = 96;
const INTERVAL_MIN = 15;
const SENSOR_MASK = 0b1111; // rain, accel, tilt, crack all present

function makeReadings(): ReadingDTO[] {
  const rand = lcg(99);
  const out: ReadingDTO[] = [];
  const now = Date.now();
  for (const node of NODES) {
    for (let k = 0; k < READINGS_PER_NODE; k++) {
      const t = new Date(now - (READINGS_PER_NODE - k) * INTERVAL_MIN * 60_000);
      // Base values
      let rain = Math.floor(rand() * 4);            // 0-3 tips per 15m
      let accel = 5 + rand() * 10;                  // 5-15 mg RMS
      let tilt = rand() * 1.5;                      // 0-1.5 ddeg
      let crack = rand() * 0.8;                     // 0-0.8 mm*10
      let mlProb = rand() * 0.15;                   // 0-15% for normal
      let severity: Severity = Severity.Normal;

      // Inflate the node's "home" severity, and bias recent readings upward
      const target = NODE_SEVERITY[NODES.indexOf(node)];
      if (target === Severity.Warning) {
        rain += 4 + Math.floor(rand() * 4);
        accel += 10 + rand() * 10;
        tilt += 2 + rand() * 2;
        crack += 1 + rand() * 1;
        mlProb = 0.4 + rand() * 0.3;
        severity = Severity.Warning;
      } else if (target === Severity.Critical) {
        // recent readings are worse than older ones (escalation story)
        const recency = k / READINGS_PER_NODE; // 0..1
        rain += 8 + Math.floor(rand() * 6);
        accel += 25 + rand() * 30;
        tilt += 5 + rand() * 5 + recency * 8;
        crack += 3 + rand() * 3;
        mlProb = 0.7 + rand() * 0.25 + recency * 0.1;
        severity = Severity.Critical;
      }

      out.push({
        time: t.toISOString(),
        tenant_id: TENANT.id,
        node_id: node.id,
        site_id: node.site_id,
        severity,
        sensor_mask: SENSOR_MASK,
        rain_tips_15m: rain,
        accel_rms_mg: Math.round(accel * 10) / 10,
        tilt_delta_ddeg: Math.round(tilt * 100) / 100,
        crack_delta_mm10: Math.round(crack * 100) / 100,
        battery_mv: node.battery_mv ?? 0,
        ml_prob: Math.min(0.99, Math.round(mlProb * 1000) / 1000),
        lat: node.lat,
        lon: node.lon,
      });
    }
  }
  return out;
}

export const READINGS: ReadingDTO[] = makeReadings();

// ---- Alerts ----------------------------------------------------------------
function isoMinutesAgo(m: number) {
  return new Date(Date.now() - m * 60_000).toISOString();
}

const ALERT_DEFS: Array<{ nodeIndex: number; severity: Severity; minutesAgo: number; mlProb: number; title: string; message: string; }> = [
  {
    nodeIndex: 0,   // Cimenyan Alpha
    severity: Severity.Critical,
    minutesAgo: 18,
    mlProb: 0.94,
    title: 'Tilt delta exceeds critical threshold',
    message: 'Tilt +9.4 ddeg in 15 min, accel RMS 47 mg. ML model probability 94%.',
  },
  {
    nodeIndex: 1,   // Cimenyan Bravo
    severity: Severity.Warning,
    minutesAgo: 124,
    mlProb: 0.71,
    title: 'Rain burst detected (32 mm/h)',
    message: 'Sustained rainfall above warning threshold for 45 minutes.',
  },
  {
    nodeIndex: 8,   // Ciwidey Echo
    severity: Severity.Watch,
    minutesAgo: 342,
    mlProb: 0.42,
    title: 'Crack sensor drift',
    message: 'Crack delta trending upward over 6 hours, within watch range.',
  },
];

export const ALERTS: AlertDTO[] = ALERT_DEFS.map((a, i) => {
  const node = NODES[a.nodeIndex];
  return {
    id: `a_${i + 1}`,
    tenant_id: TENANT.id,
    node_id: node.id,
    site_id: node.site_id,
    severity: a.severity,
    state: AlertState.Open,
    title: a.title,
    message: a.message,
    trigger_payload: null,
    first_seen_at: isoMinutesAgo(a.minutesAgo),
    last_seen_at: isoMinutesAgo(Math.max(1, a.minutesAgo - 10)),
    acknowledged_at: null,
    acknowledged_by: null,
    resolved_at: null,
    resolved_by: null,
    dismissed_at: null,
    dismissed_by: null,
    dismiss_reason: null,
    ml_prob: a.mlProb,
    notification_log: [
      { channel: 'ws',    target: 'dashboard',   sent_at: isoMinutesAgo(a.minutesAgo), ok: true },
      { channel: 'email', target: 'ops@acme.test', sent_at: isoMinutesAgo(a.minutesAgo), ok: true },
    ],
  };
});

// ---- KPI summary -----------------------------------------------------------
export const KPI: KPISummary = (() => {
  const now = new Date();
  const online = NODES.filter(n => n.status === NodeStatus.Online).length;
  // 24h rain: max rainfall across nodes in last 24h (stormiest site), * 0.2 mm/tip
  // Using max rather than sum avoids summing 15 nodes * 96 readings of tipping events
  const nodeRainSums = new Map<string, number>();
  for (const r of READINGS) {
    nodeRainSums.set(r.node_id, (nodeRainSums.get(r.node_id) || 0) + r.rain_tips_15m);
  }
  const maxTips = Math.max(...nodeRainSums.values(), 0);
  const rainfall24h = Math.round(maxTips * 0.2);
  const batteries = NODES.map(n => n.battery_mv).filter((v): v is number => v !== null);
  const avgBattery = Math.round(batteries.reduce((s, v) => s + v, 0) / batteries.length);
  return {
    active_alerts: ALERTS.filter(a => a.state === AlertState.Open).length,
    critical_alerts: ALERTS.filter(a => a.severity === Severity.Critical).length,
    warning_alerts: ALERTS.filter(a => a.severity === Severity.Warning).length,
    online_nodes: online,
    total_nodes: NODES.length,
    avg_battery_mv: avgBattery,
    rainfall_24h_mm: rainfall24h,
    last_updated: now.toISOString(),
  };
})();

// ---- Convenience selectors -------------------------------------------------
export function siteNameFor(nodeId: string): string {
  const n = NODES.find(x => x.id === nodeId);
  if (!n) return 'Unknown';
  return SITES.find(s => s.id === n.site_id)?.name ?? 'Unknown';
}

export function severityLabel(s: Severity): string {
  return SEVERITY_LABELS[s];
}

export function readingsForNode(nodeId: string): ReadingDTO[] {
  return READINGS.filter(r => r.node_id === nodeId);
}
